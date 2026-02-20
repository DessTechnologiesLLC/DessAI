# frontend/streamlit_app.py
import streamlit as st
import requests
from datetime import date

BACKEND_URL = "http://localhost:8001"

st.set_page_config(page_title="Board Smart Search", layout="wide")
st.title("Board Smart Search – Prototype")

with st.sidebar:
    st.header("Backend status")
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if resp.status_code == 200 and resp.json().get("status") == "ok":
            st.success("Backend is running ✅")
        else:
            st.warning("Health endpoint returned unexpected response.")
    except Exception as e:
        st.error(f"Cannot reach backend: {e}")#test

tab_search, tab_admin, tab_upload = st.tabs(
    ["🔍 Search (stub)", "🏗️ Committees & Meetings", "📄 Upload Documents"]
)


with tab_search:
    st.subheader("Search")

    committee_external_id = st.text_input("Committee External ID", "AC001")

    meetings_options = ["All meetings"]
    meeting_map = {}

    if committee_external_id:
        try:
            resp = requests.get(
                f"{BACKEND_URL}/meetings/",
                params={"committee_external_id": committee_external_id},
                timeout=5,
            )
            if resp.status_code == 200:
                meetings = resp.json()
                for m in meetings:
                    label = f"{m['external_meeting_id']} – {m['name']}"
                    meetings_options.append(label)
                    meeting_map[label] = m["external_meeting_id"]
            else:
                st.warning(
                    f"Could not load meetings for committee {committee_external_id} "
                    f"(status {resp.status_code})."
                )
        except Exception as e:
            st.warning(f"Error loading meetings: {e}")

    selected_meeting_label = st.selectbox("Meeting (optional filter)", meetings_options)
    meeting_external_id = (
        None if selected_meeting_label == "All meetings" else meeting_map[selected_meeting_label]
    )

    doc_type_filter = st.selectbox(
        "Document Type (optional filter)",
        ["Any", "Agenda", "DraftMinutes", "FinalMinutes", "CircularResolution", "Extra1", "Extra2"],
    )
    doc_type_value = None if doc_type_filter == "Any" else doc_type_filter

    
    st.subheader("Keyword Search")

    query = st.text_input("Search query", key="keyword_query")

    if st.button("Search", type="primary"):
        payload = {
            "committee_external_id": committee_external_id,
            "query": query,
            "meeting_external_id": meeting_external_id,
            "doc_type": doc_type_value,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/search/", json=payload)
            if resp.status_code != 200:
                st.error(f"Error {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    st.info("No results found.")
                else:
                    st.success(f"Found {len(results)} result(s).")
                    for hit in results:
                        st.markdown(f"### {hit['document_title']}")
                        meta = f"Doc type: {hit['doc_type']}"
                        if hit.get("meeting_name"):
                            meta += f" | Meeting: {hit['meeting_name']}"
                        st.caption(meta)

                        st.markdown(hit["snippet"])

                        st.markdown(
                            f"*Matches in this section:* `{hit['occurrence_count']}`  "
                            f"| *Score:* `{hit['score']:.3f}`"
                        )
                        if hit.get("ddm_url"):
                            st.markdown(f"[Open in DDM]({hit['ddm_url']})")
                        st.markdown("---")
        except Exception as e:
            st.error(f"Search failed: {e}")

    
    st.markdown("---")
    st.subheader("Semantic Search (beta)")

    sem_query = st.text_input(
        "Semantic query (concepts, synonyms, etc.)",
        key="semantic_query",
        placeholder="e.g. related party transactions, board evaluation, ESOP approvals",
    )

    if st.button("Semantic Search", type="secondary"):
        payload = {
            "committee_external_id": committee_external_id,
            "query": sem_query,
            "meeting_external_id": meeting_external_id,
            "doc_type": doc_type_value,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/semantic-search/", json=payload)
            if resp.status_code != 200:
                st.error(f"Error {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    st.info("No semantic results found.")
                else:
                    st.success(f"Found {len(results)} semantic result(s).")
                    for hit in results:
                        st.markdown(f"### {hit['document_title']}")
                        meta = f"Doc type: {hit['doc_type']}"
                        if hit.get("meeting_name"):
                            meta += f" | Meeting: {hit['meeting_name']}"
                        st.caption(meta)

                        st.write(hit["snippet"])
                        st.markdown(f"*Semantic score:* `{hit['score']:.3f}`")
                        if hit.get("ddm_url"):
                            st.markdown(f"[Open in DDM]({hit['ddm_url']})")
                        st.markdown("---")
        except Exception as e:
            st.error(f"Semantic search failed: {e}")

   
    st.markdown("---")
    st.subheader("Hybrid Search (recommended)")

    hybrid_query = st.text_input(
        "Hybrid query (uses both keyword + semantic signals)",
        key="hybrid_query",
        placeholder="e.g. appropriation of profit as per statutory requirement",
    )

    if st.button("Hybrid Search"):
        payload = {
            "committee_external_id": committee_external_id,
            "query": hybrid_query,
            "meeting_external_id": meeting_external_id,
            "doc_type": doc_type_value,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/hybrid-search/", json=payload)
            if resp.status_code != 200:
                st.error(f"Error {resp.status_code}: {resp.text}")
            else:
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    st.info("No hybrid results found.")
                else:
                    results = sorted(results, key=lambda h: h["score"], reverse=True)

                    st.success(f"Found {len(results)} hybrid result(s). (sorted by score)")

                    for hit in results:
                        st.markdown(f"### {hit['document_title']}")

                        meta_parts = []
                        if hit.get("meeting_name"):
                            meta_parts.append(f"Meeting: {hit['meeting_name']}")
                        meta_parts.append(f"Doc type: {hit['doc_type']}")
                        st.caption(" | ".join(meta_parts))

                        snippet = hit["snippet"]
                        if len(snippet) > 400:
                            snippet = snippet[:400] + "..."
                        st.write(snippet)

                        st.markdown(f"*Hybrid score:* `{hit['score']:.3f}`")
                        if hit.get("ddm_url"):
                            st.markdown(f"[Open in DDM]({hit['ddm_url']})")

                        st.markdown("---")
        except Exception as e:
            st.error(f"Hybrid search failed: {e}")





with tab_admin:
    st.subheader("Create Committee")

    col1, col2 = st.columns(2)

    with col1:
        company_external_id = st.text_input(
            "Company External ID",
            value="Titan",
            help="E.g. Titan; used as tenant/company key",
        )
        committee_name = st.text_input(
            "Committee Name",
            value="Audit Committee",
            help="Display name, e.g. Audit Committee",
        )

    with col2:
        external_committee_id = st.text_input(
            "External Committee ID",
            value="AC001",
            help="ID used by DDM; for now, just pick something unique",
        )

    if st.button("Create Committee"):
        payload = {
            "company_external_id": company_external_id or None,
            "committee_name": committee_name,
            "external_committee_id": external_committee_id or None,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/committees/", json=payload)
            if resp.status_code == 200:
                st.success(f"Committee created: {resp.json()}")
            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")

    st.markdown("---")
    st.subheader("Existing Committees")

    try:
        resp = requests.get(f"{BACKEND_URL}/committees/")
        if resp.status_code == 200:
            committees = resp.json()
            if not committees:
                st.info("No committees yet. Create one above.")
            else:
                st.table(committees)
        else:
            st.error(f"Error fetching committees: {resp.status_code} {resp.text}")
    except Exception as e:
        st.error(f"Failed to fetch committees: {e}")

    st.markdown("---")
    st.subheader("Create Meeting")

    committee_options = []
    try:
        resp = requests.get(f"{BACKEND_URL}/committees/")
        if resp.status_code == 200:
            committee_options = resp.json()
    except Exception:
        committee_options = []

    if committee_options:
        committee_labels = [
            f"{c['external_committee_id'] or 'N/A'} – {c['name']}" for c in committee_options
        ]
        idx = st.selectbox(
            "Select Committee",
            range(len(committee_options)),
            format_func=lambda i: committee_labels[i],
        )
        selected_committee = committee_options[idx]
        selected_committee_external_id = selected_committee["external_committee_id"]
    else:
        selected_committee = None
        selected_committee_external_id = None
        st.warning("No committees available for meetings. Create a committee first.")

    col3, col4 = st.columns(2)
    with col3:
        meeting_name = st.text_input(
            "Meeting Name",
            value="Audit Committee Meeting 2025-11-03",
        )
        meeting_date = st.date_input("Meeting Date", value=date.today())
    with col4:
        external_meeting_id = st.text_input(
            "External Meeting ID",
            value="M2025-11-03",
            help="ID used by DDM; for now just choose something unique",
        )

    if st.button("Create Meeting", disabled=selected_committee_external_id is None):
        payload = {
            "external_committee_id": selected_committee_external_id,
            "meeting_name": meeting_name,
            "meeting_date": meeting_date.isoformat() if meeting_date else None,
            "external_meeting_id": external_meeting_id or None,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/meetings/", json=payload)
            if resp.status_code == 200:
                st.success(f"Meeting created: {resp.json()}")
            else:
                st.error(f"Error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Request failed: {e}")

    st.markdown("---")
    st.subheader("Meetings for a Committee")

    if committee_options:
        idx2 = st.selectbox(
            "Choose Committee to list its meetings",
            range(len(committee_options)),
            format_func=lambda i: committee_labels[i],
            key="list_meetings_committee",
        )
        list_committee = committee_options[idx2]
        list_external_committee_id = list_committee["external_committee_id"]

        try:
            resp = requests.get(
                f"{BACKEND_URL}/meetings/",
                params={"committee_external_id": list_external_committee_id},
            )
            if resp.status_code == 200:
                meetings = resp.json()
                if not meetings:
                    st.info("No meetings for this committee yet.")
                else:
                    st.table(meetings)
            else:
                st.error(f"Error fetching meetings: {resp.status_code} {resp.text}")
        except Exception as e:
            st.error(f"Failed to fetch meetings: {e}")
    else:
        st.info("Create a committee above to see meetings.")



with tab_upload:
    st.subheader("Upload Agenda / Minutes / etc.")

    committees = []
    try:
        resp = requests.get(f"{BACKEND_URL}/committees/")
        if resp.status_code == 200:
            committees = resp.json()
    except Exception:
        committees = []

    if not committees:
        st.warning("No committees found. Create a committee in the previous tab first.")
    else:
        committee_labels = [
            f"{c['external_committee_id'] or 'N/A'} – {c['name']}" for c in committees
        ]
        c_idx = st.selectbox(
            "Committee",
            range(len(committees)),
            format_func=lambda i: committee_labels[i],
            key="upload_committee",
        )
        selected_committee = committees[c_idx]
        committee_external_id = selected_committee["external_committee_id"]

        meetings = []
        try:
            resp = requests.get(
                f"{BACKEND_URL}/meetings/",
                params={"committee_external_id": committee_external_id},
            )
            if resp.status_code == 200:
                meetings = resp.json()
        except Exception:
            meetings = []

        meeting_options = ["(None – committee-level doc)"]
        meeting_map: dict[str, str | None] = {"(None – committee-level doc)": None}
        for m in meetings:
            label = f"{m['external_meeting_id'] or 'N/A'} – {m['name']}"
            meeting_options.append(label)
            meeting_map[label] = m["external_meeting_id"]

        meeting_label = st.selectbox("Meeting", meeting_options)
        selected_meeting_external_id = meeting_map[meeting_label]

        doc_type = st.selectbox(
            "Document Type",
            ["Agenda", "DraftMinutes", "FinalMinutes", "CircularResolution", "Extra1", "Extra2"],
        )

        uploaded_file = st.file_uploader(
            "Choose file",
            type=["pdf", "docx", "doc", "txt", "csv", "xlsx", "xls", "pptx", "ppt"],
        )

        external_document_id = st.text_input(
            "External Document ID (optional)",
            help="ID from DDM if available",
        )

        if st.button("Upload Document", type="primary"):
            if not uploaded_file:
                st.error("Please select a file to upload.")
            else:
                files = {
                    "file": (uploaded_file.name, uploaded_file, uploaded_file.type),
                }
                data = {
                    "external_committee_id": committee_external_id,
                    "doc_type": doc_type,
                    "external_meeting_id": selected_meeting_external_id or "",
                    "external_document_id": external_document_id or "",
                }

                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/documents/upload",
                        data=data,
                        files=files,
                    )
                    if resp.status_code == 200:
                        st.success("Document uploaded and registered.")
                        st.json(resp.json())
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Upload failed: {e}")
