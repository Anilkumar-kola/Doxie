# src/integration/integrator.py
import asyncio
import json
import logging
import os
from pathlib import Path

from src.integration.vector_store import VectorDBClient
from src.integration.relation_store import RelationalDBClient
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DataIntegrator:
    """Integrates extracted document data into storage systems"""
    
    def __init__(self):
        # Initialize vector database client if enabled
        try:
            self.vector_db = VectorDBClient()
            self.vector_db_available = True
        except Exception as e:
            logger.warning(f"Vector DB not available: {str(e)}")
            self.vector_db = None
            self.vector_db_available = False
            
        # Initialize relational database client if enabled
        try:
            self.relation_db = RelationalDBClient()
            self.relation_db_available = True
        except Exception as e:
            logger.warning(f"Relational DB not available: {str(e)}")
            self.relation_db = None
            self.relation_db_available = False
            
    async def integrate_document(self, extracted_doc):
        """Integrate document data into storage"""
        doc_id = extracted_doc["id"]
        doc_class = extracted_doc["class"]
        extracted_data = extracted_doc["extracted_data"]
        extracted_dir = Path(extracted_doc["extracted_dir"])
        
        # Get text content
        text_path = None
        for candidate in ["extracted_text.txt", "ocr_text.txt", "full_text.txt"]:
            candidate_path = extracted_dir / candidate
            if candidate_path.exists():
                text_path = candidate_path
                break
                
        if text_path:
            with open(text_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            logger.warning(f"No text found for document {doc_id}")
            text = ""
            
        # Store in vector database if available
        vector_result = {"status": "skipped", "id": None}
        if self.vector_db_available:
            try:
                vector_result = await self.vector_db.store_document(
                    id=doc_id,
                    text=text,
                    doc_class=doc_class,
                    metadata={
                        "doc_class": doc_class,
                        "extracted_data": extracted_data
                    }
                )
            except Exception as e:
                logger.error(f"Error storing in vector DB: {str(e)}")
                vector_result = {"status": "error", "error": str(e), "id": None}
                
        # Store in relational database if available
        relation_result = {"status": "skipped", "id": None}
        if self.relation_db_available:
            try:
                relation_result = await self.relation_db.store_document(
                    doc_id=doc_id,
                    doc_class=doc_class,
                    data=extracted_data,
                    text=text
                )
            except Exception as e:
                logger.error(f"Error storing in relational DB: {str(e)}")
                relation_result = {"status": "error", "error": str(e), "id": None}
                
        # If neither database is available, save to local file system
        if not self.vector_db_available and not self.relation_db_available:
            db_dir = Path("data/database")
            db_dir.mkdir(exist_ok=True, parents=True)
            
            db_file = db_dir / f"{doc_id}.json"
            with open(db_file, "w") as f:
                json.dump({
                    "id": doc_id,
                    "class": doc_class,
                    "extracted_data": extracted_data,
                    "text": text,
                    "extraction_time": extracted_doc.get("extraction_time", "")
                }, f, indent=2)
                
            relation_result = {"status": "saved_local", "id": str(db_file)}
            
        return {
            "id": doc_id,
            "class": doc_class,
            "vector_db_result": vector_result,
            "relation_db_result": relation_result,
            "status": "integrated"
        }