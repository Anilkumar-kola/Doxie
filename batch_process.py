import os
import sys
import json
import logging
import argparse
import datetime
import concurrent.futures
from pathlib import Path
from tqdm import tqdm

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from our document processing system
from core.config import Config
from core.pipeline import Pipeline
from preprocessing.processor import Processor
from preprocessing.ocr_engine import OCREngine
from classification.classifier import Classifier
from extraction.extractor import Extractor
from integration.document_storage import DocumentStorage  # Add this line
from integration.vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - **%(name)s** - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_process.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("batch_processor")

class BatchProcessor:
    """
    Batch document processor that can handle multiple files in parallel
    """
    def __init__(self, config_path=None, max_workers=None):
        """
        Initialize the batch processor
        
        Args:
            config_path: Path to configuration file
            max_workers: Maximum number of worker threads (default: CPU count)
        """
        # Load configuration
        self.config = Config(config_path)
        
        # Initialize components
        self.preprocessor = Processor()
        self.ocr_engine = OCREngine()
        self.classifier = Classifier()
        self.extractor = Extractor()
        self.vector_store = VectorStore(self.config.get("vector_db_url"))
        
        # Create processing pipeline
        self.pipeline = Pipeline([
            ("preprocess", self.preprocessor.process),
            ("ocr", self.ocr_engine.extract_text),
            ("classify", self.classifier.classify),
            ("extract", self.extractor.extract_data),
            ("store", self.vector_store.store_document)
        ])
        
        # Set max workers
        self.max_workers = max_workers or os.cpu_count()
        
    def process_document(self, file_path):
        """
        Process a single document
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Processing result
        """
        file_path = Path(file_path)
        
        # Skip if file doesn't exist
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {
                "file_path": str(file_path),
                "status": "error",
                "error": "File not found"
            }
            
        # Skip if not a file
        if not file_path.is_file():
            logger.warning(f"Not a file: {file_path}")
            return {
                "file_path": str(file_path),
                "status": "error",
                "error": "Not a file"
            }
            
        # Get basic file information
        try:
            file_size = os.path.getsize(file_path)
            file_type = file_path.suffix.lower()
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return {
                "file_path": str(file_path),
                "status": "error",
                "error": f"Error getting file info: {str(e)}"
            }
            
        logger.info(f"Processing file: {file_path}")
        
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
            processed_doc["status"] = "processed"
            
            # Save processed result
            output_dir = Path(self.config.get("storage.processed_dir"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{file_path.stem}_result.json"
            
            with open(output_path, 'w') as f:
                json.dump(processed_doc, f, indent=2)
                
            logger.info(f"Saved result to {output_path}")
            
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            
            # Save error result
            document["status"] = "error"
            document["error"] = str(e)
            
            output_dir = Path(self.config.get("storage.failed_dir"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{file_path.stem}_error.json"
            
            with open(output_path, 'w') as f:
                json.dump(document, f, indent=2)
                
            logger.info(f"Saved error to {output_path}")
            
            return document
            
    def process_directory(self, dir_path, recursive=False, file_types=None):
        """
        Process all documents in a directory
        
        Args:
            dir_path: Path to the directory
            recursive: Whether to process subdirectories
            file_types: List of file types to process (e.g. ['.pdf', '.png'])
            
        Returns:
            Dictionary with processing statistics
        """
        dir_path = Path(dir_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Directory not found: {dir_path}")
            return {
                "status": "error",
                "error": f"Directory not found: {dir_path}"
            }
            
        # Get list of files to process
        files = []
        
        if recursive:
            # Use rglob to find files recursively
            pattern = "*.*" if not file_types else f"*.[{'|'.join(t.strip('.') for t in file_types)}]"
            files = list(dir_path.rglob(pattern))
        else:
            # Use glob to find files in current directory only
            pattern = "*.*" if not file_types else f"*.[{'|'.join(t.strip('.') for t in file_types)}]"
            files = list(dir_path.glob(pattern))
            
        # Filter by file type if needed
        if file_types:
            files = [f for f in files if f.suffix.lower() in file_types]
            
        if not files:
            logger.warning(f"No files found in {dir_path}")
            return {
                "status": "completed",
                "total_files": 0,
                "processed": 0,
                "failed": 0,
                "files": []
            }
            
        logger.info(f"Found {len(files)} files to process")
        
        # Process files in parallel
        results = []
        successful = 0
        failed = 0
        
        with tqdm(total=len(files), desc="Processing documents") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all files for processing
                future_to_file = {executor.submit(self.process_document, f): f for f in files}
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result.get("status") == "processed":
                            successful += 1
                        else:
                            failed += 1
                            
                    except Exception as e:
                        logger.error(f"Executor error for {file_path}: {str(e)}")
                        failed += 1
                        results.append({
                            "file_path": str(file_path),
                            "status": "error",
                            "error": str(e)
                        })
                        
                    pbar.update(1)
        
        # Summarize results
        logger.info(f"Processed {len(files)} files: {successful} successful, {failed} failed")
        
        return {
            "status": "completed",
            "total_files": len(files),
            "processed": successful,
            "failed": failed,
            "files": results
        }

def main():
    parser = argparse.ArgumentParser(description="Batch document processor")
    parser.add_argument("--dir", required=True, help="Directory containing documents to process")
    parser.add_argument("--recursive", action="store_true", help="Process subdirectories recursively")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--workers", type=int, help="Maximum number of worker threads")
    parser.add_argument("--types", help="Comma-separated list of file types to process (e.g. '.pdf,.png')")
    parser.add_argument("--output", help="Output file for processing results")
    
    args = parser.parse_args()
    
    # Initialize batch processor
    processor = BatchProcessor(config_path=args.config, max_workers=args.workers)
    
    # Parse file types
    file_types = None
    if args.types:
        file_types = [t.strip() for t in args.types.split(",")]
        # Ensure all file types start with a dot
        file_types = [t if t.startswith(".") else f".{t}" for t in file_types]
    
    # Process directory
    results = processor.process_directory(args.dir, recursive=args.recursive, file_types=file_types)
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")
    
    # Print summary
    print(f"\nProcessing completed:")
    print(f"  Total files: {results['total_files']}")
    print(f"  Successfully processed: {results['processed']}")
    print(f"  Failed: {results['failed']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())