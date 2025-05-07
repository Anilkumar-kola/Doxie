# src/preprocessing/ocr_engine.py
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class OCREngine:
    """Simple OCR engine implementation"""
    
    def __init__(self, engine="mock", config=None):
        """Initialize the OCR engine"""
        self.engine = engine
        self.config = config or {}
        logger.info(f"OCR Engine initialized: {engine}")
        
    def extract_text(self, document):
        """Extract text from document (mock implementation)"""
        file_path = document.get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            return document
            
        # For demo purposes, just set some mock content
        document["content"] = f"Mock content for {Path(file_path).name}"
        
        return document