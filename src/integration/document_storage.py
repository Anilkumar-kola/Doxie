# src/integration/document_storage.py
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentStorage:
    """
    Manages document storage organization by document type
    """
    def __init__(self, base_path="data/processed"):
        """
        Initialize the document storage manager
        
        Args:
            base_path: Base directory for processed documents
        """
        self.base_path = Path(base_path)
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure all required directories exist"""
        # Base directory
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Type-specific directories
        for folder in [
            "invoices", 
            "receipts", 
            "contracts", 
            "letters", 
            "forms", 
            "reports", 
            "scanned", 
            "pdf", 
            "images", 
            "spreadsheets", 
            "other"
        ]:
            (self.base_path / folder).mkdir(exist_ok=True)
    
    def store_document(self, document):
        """
        Store a document in the appropriate directory
        
        Args:
            document: The document to store
            
        Returns:
            Updated document with storage information
        """
        file_path = document.get("file_path")
        if not file_path or not os.path.exists(file_path):
            logger.error(f"Document file not found: {file_path}")
            document["storage"] = {
                "status": "error",
                "error": "File not found"
            }
            return document
        
        file_path = Path(file_path)
        doc_type = document.get("doc_type", "unknown")
        file_type = document.get("file_type", "")
        
        # Determine target directory based on document type and file type
        target_dir = self._get_target_directory(doc_type, file_type)
        
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        target_path = self.base_path / target_dir / new_filename
        
        try:
            # Copy the file to the target directory
            shutil.copy2(file_path, target_path)
            
            # Update document storage information
            document["storage"] = {
                "original_path": str(file_path),
                "stored_path": str(target_path),
                "category": target_dir,
                "timestamp": timestamp,
                "status": "stored"
            }
            
            logger.info(f"Document stored in {target_dir} folder: {new_filename}")
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            document["storage"] = {
                "status": "error",
                "error": str(e)
            }
        
        return document
    
    def _get_target_directory(self, doc_type, file_type):
        """
        Determine the target directory based on document type and file type
        
        Args:
            doc_type: Document type classification
            file_type: File extension
            
        Returns:
            Target directory name
        """
        # First, check document type
        if doc_type == "invoice":
            return "invoices"
        elif doc_type == "receipt":
            return "receipts"
        elif doc_type == "contract":
            return "contracts"
        elif doc_type == "letter":
            return "letters"
        elif doc_type == "form":
            return "forms"
        elif doc_type == "report":
            return "reports"
        
        # If no specific document type, categorize by file type
        if file_type == ".pdf":
            return "pdf"
        elif file_type in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            return "images"
        elif file_type in [".xls", ".xlsx", ".csv"]:
            return "spreadsheets"
        
        # If all else fails
        return "other"