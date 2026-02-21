# backend/services/vector_index.py
from __future__ import annotations

from typing import List, Callable, Tuple

import faiss
import numpy as np
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
import pickle

from backend.models import DocumentChunk
from logger import CustomLogger
logging = CustomLogger().get_logger(__file__)

EmbedFn = Callable[[List[str]], np.ndarray]


class VectorIndex:
    """
    Simple FAISS index over DocumentChunk embeddings.
    - Uses IndexFlatIP + L2-normalized vectors (cosine similarity).
    - Stores chunk.id as FAISS IDs (so we can map back).
    - Supports saving/loading index to/from disk.
    """

    # Default directory for storing vector index files
    DEFAULT_INDEX_DIR = Path("data/vector_indexes")
    DEFAULT_INDEX_FILE = "faiss_index.bin"
    DEFAULT_METADATA_FILE = "index_metadata.pkl"

    def __init__(self, index_dir: Path | None = None) -> None:
        self.index: faiss.IndexIDMap | None = None
        self.dim: int | None = None
        self.is_built: bool = False

        # Set the directory where index files will be saved/loaded
        self.index_dir = index_dir or self.DEFAULT_INDEX_DIR
        self.index_path = self.index_dir / self.DEFAULT_INDEX_FILE
        self.metadata_path = self.index_dir / self.DEFAULT_METADATA_FILE

        self.load()  # Attempt to load existing index from disk

        logging.info("VectorIndex initialized with index_dir: %s", self.index_dir)

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            logging.info("Creating FAISS index with dimension %d", dim)
            base = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIDMap(base)
            self.dim = dim
    
    def _ensure_directory(self) -> None:
        """Ensure the index directory exists."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Ensured index directory exists: %s", self.index_dir)

    def reset(self) -> None:
        if self.index is not None:
            logging.info("Resetting FAISS index")
            self.index.reset()
        self.index = None
        self.dim = None
        self.is_built = False
        logging.info("VectorIndex reset")

    def rebuild_from_db(self, db: Session, embed_fn: EmbedFn) -> None:
        """
        Build the index from scratch using all DocumentChunk rows.
        """
        logging.info("Rebuilding index from database")
        chunks = db.query(DocumentChunk).all()
        
        texts = [c.text or "" for c in chunks]
        if not texts:
            logging.warning("No chunks found in database")
            self.reset()
            self.is_built = True
            return

        logging.info("Embedding %d chunks", len(texts))
        vectors = embed_fn(texts)
        ids = np.array([c.id for c in chunks], dtype="int64")

        self._ensure_index(vectors.shape[1])
        self.index.reset()
        self.index.add_with_ids(vectors, ids)
        self.is_built = True
        logging.info("Index rebuilt with %d vectors", self.index.ntotal)

        self.save()  # Save index after adding new chunks
        logging.info("Saved index with %d vectors", self.index.ntotal)

    def add_chunks(self, db: Session, chunk_ids: List[int], embed_fn: EmbedFn) -> None:
        """
        Incrementally add a small set of new chunks into the index.
        """
        if not chunk_ids:
            logging.warning("No chunk IDs provided to add_chunks")
            return
        chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
        if not chunks:
            logging.warning("No chunks found for provided IDs")
            return

        logging.info("Adding %d chunks to index", len(chunks))
        texts = [c.text or "" for c in chunks]
        vectors = embed_fn(texts)
        ids = np.array([c.id for c in chunks], dtype="int64")

        self._ensure_index(vectors.shape[1])
        self.index.add_with_ids(vectors, ids)
        logging.info("Added %d vectors to index. Total: %d", len(ids), self.index.ntotal)

        self.save()  # Save index after adding new chunks
        logging.info("Saved index with %d vectors", len(ids))

    def search(self, query_vector: np.ndarray, top_k: int = 50) -> Tuple[List[int], List[float]]:
        """
        Search the index and return (chunk_ids, scores).
        """
        if self.index is None or self.index.ntotal == 0:
            logging.warning("Index is empty or not built")
            return [], []

        if query_vector.ndim == 1:
            query_vector = query_vector[None, :]

        scores, ids = self.index.search(query_vector, top_k)
        logging.info("Search returned %d results", len(ids[0]))
        return ids[0].tolist(), scores[0].tolist()
    
    def save(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> None:
        """
        Save the FAISS index and metadata to disk.
        
        Args:
            index_path: Optional custom path for the index file
            metadata_path: Optional custom path for the metadata file
        """
        if self.index is None:
            logging.warning("Cannot save: index is None")
            raise ValueError("Cannot save index: index has not been initialized")
        
        # Use provided paths or defaults
        index_file = index_path or self.index_path
        metadata_file = metadata_path or self.metadata_path
        
        # Ensure directory exists
        self._ensure_directory()
        
        try:
            # Save FAISS index
            logging.info("Saving FAISS index to %s", index_file)
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            metadata = {
                'dim': self.dim,
                'is_built': self.is_built,
                'ntotal': self.index.ntotal
            }
            logging.info("Saving metadata to %s", metadata_file)
            with open(metadata_file, 'wb') as f:
                pickle.dump(metadata, f)
            
            logging.info("Successfully saved index with %d vectors", self.index.ntotal)
            
        except Exception as e:
            logging.error("Failed to save index: %s", str(e))
            raise

    def load(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> bool:
        """
        Load the FAISS index and metadata from disk.
        
        Args:
            index_path: Optional custom path for the index file
            metadata_path: Optional custom path for the metadata file
            
        Returns:
            True if load was successful, False otherwise
        """
        # Use provided paths or defaults
        index_file = index_path or self.index_path
        metadata_file = metadata_path or self.metadata_path
        
        # Check if files exist
        if not index_file.exists():
            logging.warning("Index file not found: %s", index_file)
            return False
        
        if not metadata_file.exists():
            logging.warning("Metadata file not found: %s", metadata_file)
            return False
        
        try:
            # Load FAISS index
            logging.info("Loading FAISS index from %s", index_file)
            self.index = faiss.read_index(str(index_file))
            
            # Load metadata
            logging.info("Loading metadata from %s", metadata_file)
            with open(metadata_file, 'rb') as f:
                metadata = pickle.load(f)
            
            self.dim = metadata.get('dim')
            self.is_built = metadata.get('is_built', True)
            
            logging.info("Successfully loaded index with %d vectors (dim=%d)", 
                        self.index.ntotal, self.dim)
            return True
            
        except Exception as e:
            logging.error("Failed to load index: %s", str(e))
            self.reset()
            return False

    def exists(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> bool:
        """
        Check if saved index files exist.
        
        Args:
            index_path: Optional custom path for the index file
            metadata_path: Optional custom path for the metadata file
            
        Returns:
            True if both index and metadata files exist
        """
        index_file = index_path or self.index_path
        metadata_file = metadata_path or self.metadata_path
        
        return index_file.exists() and metadata_file.exists()

    def delete_saved_index(self, index_path: Optional[Path] = None, metadata_path: Optional[Path] = None) -> None:
        """
        Delete saved index files from disk.
        
        Args:
            index_path: Optional custom path for the index file
            metadata_path: Optional custom path for the metadata file
        """
        index_file = index_path or self.index_path
        metadata_file = metadata_path or self.metadata_path
        
        try:
            if index_file.exists():
                index_file.unlink()
                logging.info("Deleted index file: %s", index_file)
            
            if metadata_file.exists():
                metadata_file.unlink()
                logging.info("Deleted metadata file: %s", metadata_file)
                
        except Exception as e:
            logging.error("Failed to delete index files: %s", str(e))
            raise

vector_index = VectorIndex()