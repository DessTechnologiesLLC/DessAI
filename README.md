# DessAI - Board Smart Search

A powerful AI-driven document search and management system designed for board meetings, committees, and organizational document workflows. The system combines keyword search, semantic search, and hybrid search capabilities with document ingestion and processing.

## 🌟 Features

- **Multi-Modal Search**
  - Keyword search with BM25 ranking
  - Semantic search using embeddings
  - Hybrid search combining both approaches
  
- **Document Management**
  - Support for multiple document types (PDF, DOCX, PPTX, XLSX, etc.)
  - Automated document ingestion and processing
  - OCR support for scanned documents
  - Document chunking and indexing

- **Committee & Meeting Management**
  - Organize documents by committees and meetings
  - Document type categorization (Agenda, Minutes, Resolutions, etc.)
  - External ID tracking for integration

- **Vector Database Integration**
  - FAISS and Qdrant support for semantic search
  - Efficient embedding storage and retrieval
  - Scalable vector indexing

- **Background Processing**
  - Redis-based task queue (RQ)
  - Asynchronous document processing
  - Worker system for heavy computational tasks

## 🏗️ Architecture

The project follows a modern microservices architecture:

```
DessAI/
├── backend/           # FastAPI backend server
│   ├── core/         # Configuration and security
│   ├── db/           # Database models and session
│   ├── models/       # SQLAlchemy models
│   ├── routers/      # API endpoints
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── workers/      # Background workers
├── frontend/         # Streamlit UI
├── data/            # Document storage
├── scripts/         # Utility scripts
└── logs/           # Application logs
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Redis server
- Qdrant (optional, for vector search)
- OpenAI API key (for embeddings)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DessAI
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   APP_ENV=dev
   APP_NAME=Board Smart Search
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8001
   
   DATABASE_URL=sqlite:///./smartsearch.db
   DATA_ROOT=./data
   
   REDIS_URL=redis://localhost:6379/0
   
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=your_api_key_here
   
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_EMBEDDING_MODEL=text-embedding-3-large
   
   DDM_SYNC_TOKEN=your_sync_token
   ```

5. **Start Redis server**
   ```bash
   redis-server
   ```

6. **Initialize the database**
   ```bash
   python -m alembic upgrade head  # If using Alembic migrations
   ```

### Running the Application

The project includes convenience scripts for running different components:

1. **Start the backend API**
   ```bash
   bash scripts/run_backend.sh
   # Or manually:
   uvicorn backend.app:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **Start the background worker**
   ```bash
   bash scripts/run_worker.sh
   # Or manually:
   rq worker --url redis://localhost:6379/0
   ```

3. **Start the Streamlit frontend**
   ```bash
   bash scripts/run_streamlit.sh
   # Or manually:
   streamlit run frontend/streamlit_app.py
   ```

4. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/docs

## 📚 API Endpoints

### Health Check
- `GET /health` - Check backend status

### Committees
- `GET /committees/` - List all committees
- `POST /committees/` - Create a new committee
- `GET /committees/{id}` - Get committee details

### Meetings
- `GET /meetings/` - List meetings (filterable by committee)
- `POST /meetings/` - Create a new meeting
- `GET /meetings/{id}` - Get meeting details

### Documents
- `GET /documents/` - List documents
- `POST /documents/upload` - Upload a document
- `GET /documents/{id}` - Get document details

### Search
- `POST /search/` - Keyword search
- `POST /semantic_search/` - Semantic search
- `POST /hybrid_search/` - Hybrid search

### DDM Sync
- `POST /ddm_sync/` - Sync with external DDM system

## 🛠️ Technologies Used

### Backend
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database management
- **Pydantic** - Data validation
- **RQ (Redis Queue)** - Background job processing
- **Uvicorn** - ASGI server

### AI/ML
- **Transformers** - NLP models
- **Sentence Transformers** - Text embeddings
- **FAISS** - Vector similarity search
- **Qdrant** - Vector database
- **OpenAI** - Embeddings API
- **PyTorch** - Deep learning framework

### Document Processing
- **PyMuPDF** - PDF processing
- **python-docx** - Word document handling
- **python-pptx** - PowerPoint processing
- **pdfplumber** - PDF text extraction
- **pytesseract** - OCR capabilities
- **python-doctr** - Document OCR

### Frontend
- **Streamlit** - Interactive web UI

### Data Science
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing
- **SciPy** - Scientific computing

## 📁 Document Types Supported

The system supports the following document types:
- **Agenda** - Meeting agendas
- **DraftMinutes** - Draft meeting minutes
- **FinalMinutes** - Final approved minutes
- **CircularResolution** - Circular resolutions
- **Extra1** / **Extra2** - Additional document types

## 🔍 Search Capabilities

### Keyword Search
Uses BM25 algorithm for traditional keyword-based search with relevance ranking.

### Semantic Search
Leverages OpenAI embeddings to understand query context and find semantically similar content.

### Hybrid Search
Combines keyword and semantic search for optimal results, balancing exact matches with contextual understanding.

## 🐛 Logging

Application logs are stored in the `logs/` directory with timestamps. The system uses Python's logging module with detailed error tracking.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the terms specified in the LICENSE file.

## 🔧 Development

### Project Structure Details

- **backend/core/** - Core configuration, authentication, and security
- **backend/db/** - Database session management and base models
- **backend/models/** - SQLAlchemy ORM models (Committee, Meeting, Document, etc.)
- **backend/routers/** - FastAPI route handlers
- **backend/schemas/** - Pydantic validation schemas
- **backend/services/** - Business logic for search, ingestion, and embeddings
- **backend/workers/** - Background worker tasks
- **frontend/** - Streamlit-based user interface
- **data/** - Document storage and vector indexes

### Running Tests

```bash
pytest
```

## 📞 Support

For issues, questions, or contributions, please open an issue in the repository.

## 🔄 Version History

- **Current Version** - Initial development with core search and document management features

---

**Note**: This is an AI-powered document search system. Ensure you have the necessary API keys and services (Redis, Qdrant, OpenAI) configured before running the application.