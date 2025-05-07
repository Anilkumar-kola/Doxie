# src/collection/collector.py
from asyncio import gather
import aiohttp
import aiofiles
from email.parser import BytesParser
from email import policy
import uuid
from pathlib import Path
import logging

from src.core.config import get_settings
from src.collection.connectors import EmailConnector, APIConnector, FileSystemConnector

logger = logging.getLogger(__name__)
settings = get_settings()

class ModernDocumentCollector:
    """Asynchronous document collector supporting multiple source types"""
    
    def __init__(self):
        self.target_dir = Path(settings.storage.raw_documents_path)
        self.target_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize connectors
        self.connectors = {
            "email": EmailConnector(settings.connectors.email),
            "api": APIConnector(settings.connectors.api),
            "filesystem": FileSystemConnector(settings.connectors.filesystem)
        }
        
    async def collect_all(self):
        """Collect documents from all configured sources asynchronously"""
        collection_tasks = []
        
        # Create tasks for each enabled connector
        for connector_name, connector in self.connectors.items():
            if connector.is_enabled():
                collection_tasks.append(self.collect_from_source(connector_name))
                
        # Run all collection tasks concurrently
        results = await gather(*collection_tasks, return_exceptions=True)
        
        # Process results
        collected_files = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Collection error: {result}")
            else:
                collected_files.extend(result)
                
        return collected_files
        
    async def collect_from_source(self, source_name):
        """Collect documents from a specific source"""
        connector = self.connectors.get(source_name)
        if not connector:
            raise ValueError(f"Unknown source: {source_name}")
            
        # Get documents from connector
        documents = await connector.get_documents()
        saved_files = []
        
        # Process and save each document
        for doc in documents:
            doc_id = str(uuid.uuid4())
            file_path = await self._save_document(doc, doc_id)
            
            # Save metadata
            metadata = {
                "id": doc_id,
                "source": source_name,
                "original_name": doc.get("name", "unknown"),
                "original_id": doc.get("id", "unknown"),
                "collection_time": doc.get("timestamp", ""),
                "mime_type": doc.get("mime_type", ""),
                "size": len(doc.get("content", b"")),
            }
            
            meta_path = file_path.with_suffix(".meta.json")
            async with aiofiles.open(meta_path, "w") as f:
                await f.write(json.dumps(metadata, indent=2))
                
            saved_files.append({"path": str(file_path), "metadata": metadata})
            
        return saved_files
            
    async def _save_document(self, document, doc_id):
        """Save document content to storage"""
        content = document.get("content")
        mime_type = document.get("mime_type", "application/octet-stream")
        
        # Determine file extension based on MIME type
        ext = self._mime_to_extension(mime_type)
        file_path = self.target_dir / f"{doc_id}{ext}"
        
        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
            
        return file_path
        
    def _mime_to_extension(self, mime_type):
        """Convert MIME type to file extension"""
        mime_map = {
            "application/pdf": ".pdf",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/tiff": ".tiff",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "text/plain": ".txt",
            "text/html": ".html",
            "application/json": ".json",
        }
        return mime_map.get(mime_type, ".bin")