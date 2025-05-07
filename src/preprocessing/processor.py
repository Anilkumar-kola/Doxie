# src/preprocessing/processor.py
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Processor:
    """Simple document processor"""
    
    def __init__(self, config=None):
        """Initialize the processor with optional config"""
        self.config = config or {}
        
    def process(self, document):
        """Process a document"""
        logger.info(f"Processing document: {document.get('file_path')}")
        
        # Simple processing - just return the document as is
        return document