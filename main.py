import os
import sys
import argparse
import logging
import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import from modules within src
from core.config import Config
from core.pipeline import Pipeline
from preprocessing.processor import Processor
from preprocessing.ocr_engine import OCREngine
from classification.classifier import Classifier
from extraction.extractor import Extractor
from integration.document_storage import DocumentStorage
from integration.vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - **%(name)s** - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

class DocumentProcessor:
    """
    Main document processing orchestrator that integrates all components
    """
    def __init__(self, config_path=None):
        # Load configuration
        self.config = Config(config_path)
        
        # Initialize components
        self.preprocessor = Processor()
        self.ocr_engine = OCREngine()
        self.classifier = Classifier()
        self.extractor = Extractor()
        self.document_storage = DocumentStorage()
        self.vector_store = VectorStore(self.config.get("vector_db_url"))
        
        # Create processing pipeline
        self.pipeline = Pipeline([
            ("preprocess", self.preprocessor.process),
            ("ocr", self.ocr_engine.extract_text),
            ("classify", self.classifier.classify),
            ("extract", self.extractor.extract_data),
            ("store", self.document_storage.store_document),
            ("index", self.vector_store.store_document)
        ])
        
    def process_document(self, file_path):
        """
        Process a document through the entire pipeline
        """
        file_path = Path(file_path)
        
        # Basic file information
        file_size = os.path.getsize(file_path)
        file_type = file_path.suffix.lower()
        
        logger.info(f"Processing file: {file_path}")
        logger.info(f"File size: {file_size} bytes")
        logger.info(f"File type: {file_type}")
        
        # Create document object
        document = {
            "file_path": str(file_path),
            "file_size": file_size,
            "file_type": file_type,
            "content": None,
            "metadata": {},
            "processed_at": datetime.datetime.now().isoformat()
        }
        
        try:
            # Run the document through the pipeline
            processed_doc = self.pipeline.run(document)
            
            # Log the document type from classification
            doc_type = processed_doc.get("doc_type", "unknown_document")
            logger.info(f"Classified as: {doc_type}")
            
            # If this is an invoice, extract specific invoice fields
            if doc_type == "invoice":
                invoice_data = self.extractor.extract_invoice_data(processed_doc)
                processed_doc["invoice_data"] = invoice_data
                logger.info(f"Extracted invoice data: {invoice_data}")
            
            processed_doc["status"] = "processed"
            logger.info(f"Processing result: {processed_doc}")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            document["status"] = "error"
            document["error"] = str(e)
            return document

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Advanced Document Processing System")
    parser.add_argument("--file", required=True, help="Path to the document file")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Output directory for processed results")
    args = parser.parse_args()
    
    # Initialize processor
    processor = DocumentProcessor(config_path=args.config)
    
    # Process the document
    result = processor.process_document(args.file)
    
    # Save results if output directory specified
    if args.output:
        output_path = Path(args.output) / f"{Path(args.file).stem}_result.json"
        import json
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()