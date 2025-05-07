# src/visualization/api.py
import logging
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Depends, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import uvicorn

from src.core.pipeline import process_document
from src.integration.relation_store import RelationalDBClient
from src.integration.vector_store import VectorDBClient
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="Document Processing API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if UI directory exists
ui_dir = Path("ui/build")
if ui_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")

# Models
class DocumentResponse(BaseModel):
    id: str
    doc_class: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DetailedDocumentResponse(DocumentResponse):
    text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None

class ProcessingMetrics(BaseModel):
    doc_class: str
    count: int
    avg_processing_time: float

# Dependency
async def get_relation_db():
    try:
        return RelationalDBClient()
    except Exception as e:
        logger.error(f"Error initializing relational DB: {str(e)}")
        raise HTTPException(status_code=500, detail="Database unavailable")

async def get_vector_db():
    try:
        return VectorDBClient()
    except Exception as e:
        logger.error(f"Error initializing vector DB: {str(e)}")
        raise HTTPException(status_code=500, detail="Vector database unavailable")

# Routes
@app.get("/")
async def root():
    return {"message": "Document Processing API", "version": "1.0.0"}

@app.get("/api/documents", response_model=List[DocumentResponse])
async def get_documents(
    doc_class: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: RelationalDBClient = Depends(get_relation_db)
):
    """Get list of processed documents"""
    documents = await db.get_documents(doc_class=doc_class, limit=limit, offset=offset)
    return documents

@app.get("/api/documents/{doc_id}", response_model=DetailedDocumentResponse)
async def get_document(
    doc_id: str,
    db: RelationalDBClient = Depends(get_relation_db)
):
    """Get detailed document information"""
    document = await db.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/api/metrics/processing", response_model=List[ProcessingMetrics])
async def get_processing_metrics(
    days: int = Query(30, ge=1, le=365),
    db: RelationalDBClient = Depends(get_relation_db)
):
    """Get document processing metrics"""
    start_date = datetime.now() - timedelta(days=days)
    metrics = await db.get_processing_metrics(start_date=start_date)
    return metrics

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Create temporary directory for uploads
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(exist_ok=True, parents=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Process document
        result = await process_document(file_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing uploaded document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_documents(
    query: str,
    doc_class: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: RelationalDBClient = Depends(get_relation_db)
):
    """Search documents by text content"""
    documents = await db.search_documents(query=query, doc_class=doc_class, limit=limit)
    return documents

@app.get("/api/similar/{doc_id}")
async def get_similar_documents(
    doc_id: str,
    limit: int = Query(5, ge=1, le=20),
    relation_db: RelationalDBClient = Depends(get_relation_db),
    vector_db: VectorDBClient = Depends(get_vector_db)
):
    """Find documents similar to a specific document"""
    # Get document text
    document = await relation_db.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Find similar documents
    similar = await vector_db.search_similar(
        text=document["text"],
        doc_class=document["doc_class"],
        limit=limit
    )
    
    return similar

def start_api():
    """Start the API server"""
    uvicorn.run("src.visualization.api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_api()