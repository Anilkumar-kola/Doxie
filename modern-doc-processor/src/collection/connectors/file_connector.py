# src/collection/connectors/file_connector.py
import os
import asyncio
from pathlib import Path
import mimetypes
import logging
import shutil

logger = logging.getLogger(__name__)

class FileSystemConnector:
    """Connector for collecting documents from file system directories"""
    
    def __init__(self, config):
        self.paths = config.get("paths", [])
        self.file_extensions = config.get("extensions", [
            ".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".docx", 
            ".xlsx", ".txt", ".html", ".json"
        ])
        self.move_files = config.get("move_files", False)
        self.processed_folder = config.get("processed_folder", None)
        
    async def get_documents(self):
        """Get documents from configured file paths"""
        documents = []
        
        for path in self.paths:
            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"Path does not exist: {path}")
                continue
                
            if path_obj.is_file():
                doc = await self._process_file(path_obj)
                if doc:
                    documents.append(doc)
            elif path_obj.is_dir():
                for file_path in path_obj.glob("**/*"):
                    if file_path.is_file() and self._is_valid_extension(file_path):
                        doc = await self._process_file(file_path)
                        if doc:
                            documents.append(doc)
        
        return documents
        
    async def _process_file(self, file_path):
        """Process a single file"""
        try:
            # Get file information
            filename = file_path.name
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Create document entry
            document = {
                "name": filename,
                "path": str(file_path),
                "mime_type": mime_type or "application/octet-stream"
            }
            
            # Move file if configured
            if self.move_files and self.processed_folder:
                processed_dir = Path(self.processed_folder)
                processed_dir.mkdir(exist_ok=True, parents=True)
                
                dest_path = processed_dir / filename
                if dest_path.exists():
                    # Avoid overwriting by adding timestamp
                    import time
                    timestamp = int(time.time())
                    stem = file_path.stem
                    suffix = file_path.suffix
                    dest_path = processed_dir / f"{stem}_{timestamp}{suffix}"
                    
                shutil.move(str(file_path), str(dest_path))
                
            return document
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return None
            
    def _is_valid_extension(self, file_path):
        """Check if file has a valid extension"""
        if not self.file_extensions:
            return True
            
        return file_path.suffix.lower() in self.file_extensions