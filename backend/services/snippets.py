# backend/services/snippets.py
import re
import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


def split_sentences(text: str):
    """Uses NLTK to split text into sentences."""
    return nltk.sent_tokenize(text)


def highlight_terms(text: str, query: str) -> str:
    """Bold all keywords from query."""
    q_terms = [t for t in query.lower().split() if t]

    def repl(match):
        return f"**{match.group(0)}**"

    for term in q_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(repl, text)

    return text


def best_sentence_snippet(chunk_text: str, query: str, score_value: float) -> str:
    """
    Picks the most relevant sentence (semantic + keyword blend),
    includes ±1 neighbor sentence, highlights keywords.
    """

    if not chunk_text:
        return ""

    sentences = split_sentences(chunk_text)
    if not sentences:
        return chunk_text[:300]

    query_low = query.lower()

    scored = []
    for i, s in enumerate(sentences):
        s_low = s.lower()
        keyword_score = 0

        for term in query_low.split():
            if term in s_low:
                keyword_score += 1

        total = score_value + 0.05 * keyword_score

        scored.append((total, i, s))

    scored.sort(reverse=True, key=lambda x: x[0])

    _, best_i, best_sentence = scored[0]

    snippet_parts = []

    if best_i - 1 >= 0:
        snippet_parts.append(sentences[best_i - 1])

    snippet_parts.append(best_sentence)

    if best_i + 1 < len(sentences):
        snippet_parts.append(sentences[best_i + 1])

    final_snippet = " ".join(snippet_parts)

    final_snippet = highlight_terms(final_snippet, query)

    return final_snippet
