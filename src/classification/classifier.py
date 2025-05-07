# src/classification/classifier.py
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Classifier:
    """Simple document classifier"""
    
    def __init__(self):
        """Initialize the classifier"""
        logger.info("Classifier initialized")
        
    def classify(self, document):
        """Classify a document based on filename"""
        file_path = document.get("file_path", "")
        filename = Path(file_path).name.lower()
        
        # Simple classification based on filename
        if "invoice" in filename:
            doc_type = "invoice"
        elif "receipt" in filename:
            doc_type = "receipt"
        elif "contract" in filename:
            doc_type = "contract"
        elif "report" in filename:
            doc_type = "report"
        else:
            doc_type = "unknown"
            
        document["doc_type"] = doc_type
        logger.info(f"Classified document as: {doc_type}")
        
        return document