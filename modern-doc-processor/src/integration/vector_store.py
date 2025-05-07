# src/integration/vector_store.py
import asyncio
import logging
import os
import json
from pathlib import Path
import numpy as np
import faiss
import pickle

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class VectorDBClient:
    """Simple vector database client using FAISS"""
    
    def __init__(self):
        self.index_dir = Path(settings.storage.vector_db.persist_directory)
        self.index_dir.mkdir(exist_ok=True, parents=True)
        
        # Load or create indices for each document class
        self.indices = {}
        self.documents = {}
        
        # Initialize basic models
        self._initialize_models()
        
        # Load existing indices
        self._load_indices()
        
    def _initialize_models(self):
        """Initialize embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use a smaller model for embeddings if available
            model_name = "paraphrase-MiniLM-L6-v2"  # Small, fast model
            
            self.embedding_model = SentenceTransformer(model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Initialized embedding model {model_name} with dimension {self.embedding_dim}")
            
        except ImportError:
            logger.warning("SentenceTransformer not available. Using mock embeddings.")
            self.embedding_model = None
            self.embedding_dim = 384  # Default dimension for mock embeddings
            
    def _load_indices(self):
        """Load existing indices"""
        # Check for existing indices
        indices_file = self.index_dir / "indices.pkl"
        documents_file = self.index_dir / "documents.pkl"
        
        if indices_file.exists() and documents_file.exists():
            try:
                # Load indices
                with open(indices_file, "rb") as f:
                    self.indices = pickle.load(f)
                    
                # Load documents
                with open(documents_file, "rb") as f:
                    self.documents = pickle.load(f)
                    
                logger.info(f"Loaded {len(self.indices)} indices and {sum(len(docs) for docs in self.documents.values())} documents")
                
            except Exception as e:
                logger.error(f"Error loading indices: {str(e)}")
                # Initialize empty indices
                self.indices = {}
                self.documents = {}
        else:
            # Initialize empty indices
            self.indices = {}
            self.documents = {}
            
    def _save_indices(self):
        """Save indices to disk"""
        try:
            # Save indices
            indices_file = self.index_dir / "indices.pkl"
            with open(indices_file, "wb") as f:
                pickle.dump(self.indices, f)
                
            # Save documents
            documents_file = self.index_dir / "documents.pkl"
            with open(documents_file, "wb") as f:
                pickle.dump(self.documents, f)
                
        except Exception as e:
            logger.error(f"Error saving indices: {str(e)}")
            
    def _get_embeddings(self, text):
        """Get embeddings for text"""
        if self.embedding_model:
            # Use actual embeddings
            return self.embedding_model.encode([text])[0]
        else:
            # Use mock embeddings (random vector)
            return np.random.randn(self.embedding_dim).astype(np.float32)
            
    def _get_or_create_index(self, doc_class):
        """Get or create index for document class"""
        if doc_class not in self.indices:
            # Create new index
            index = faiss.IndexFlatL2(self.embedding_dim)
            self.indices[doc_class] = index
            self.documents[doc_class] = []
            
        return self.indices[doc_class]
        
    async def store_document(self, id, text, doc_class, metadata=None):
        """Store document in vector database"""
        try:
            # Get embeddings
            embeddings = self._get_embeddings(text)
            
            # Get or create index
            index = self._get_or_create_index(doc_class)
            
            # Add to index
            index.add(np.array([embeddings], dtype=np.float32))
            
            # Add to documents
            doc_index = len(self.documents[doc_class])
            self.documents[doc_class].append({
                "id": id,
                "text": text,
                "metadata": metadata or {},
                "index": doc_index
            })
            
            # Save indices
            self._save_indices()
            
            return {"status": "success", "id": id}
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            return {"status": "error", "error": str(e), "id": id}
            
    async def search_similar(self, text, doc_class=None, limit=5):
        """Search for similar documents"""
        try:
            # Get embeddings
            query_embeddings = self._get_embeddings(text)
            
            results = []
            
            if doc_class and doc_class in self.indices:
                # Search in specific index
                index = self.indices[doc_class]
                documents = self.documents[doc_class]
                
                D, I = index.search(np.array([query_embeddings], dtype=np.float32), min(limit, len(documents)))
                
                for i, (distance, idx) in enumerate(zip(D[0], I[0])):
                    if idx < len(documents):
                        doc = documents[idx]
                        results.append({
                            "id": doc["id"],
                            "text": doc["text"],
                            "metadata": doc["metadata"],
                            "distance": float(distance),
                            "doc_class": doc_class
                        })
            else:
                # Search across all indices
                for cls, index in self.indices.items():
                    documents = self.documents[cls]
                    
                    if not documents:
                        continue
                        
                    D, I = index.search(np.array([query_embeddings], dtype=np.float32), min(limit, len(documents)))
                    
                    for i, (distance, idx) in enumerate(zip(D[0], I[0])):
                        if idx < len(documents):
                            doc = documents[idx]
                            results.append({
                                "id": doc["id"],
                                "text": doc["text"],
                                "metadata": doc["metadata"],
                                "distance": float(distance),
                                "doc_class": cls
                            })
                
                # Sort by distance
                results.sort(key=lambda x: x["distance"])
                
                # Limit results
                results = results[:limit]
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []