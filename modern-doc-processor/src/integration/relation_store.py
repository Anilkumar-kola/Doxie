# src/integration/relation_store.py
import asyncio
import logging
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RelationalDBClient:
    """Simple relational database client using SQLite"""
    
    def __init__(self):
        self.db_dir = Path("data/sqlite")
        self.db_dir.mkdir(exist_ok=True, parents=True)
        
        self.db_path = self.db_dir / "documents.db"
        
        # Initialize database
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create documents table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                doc_class TEXT NOT NULL,
                text TEXT,
                extracted_data TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """)
            
            # Create document_metadata table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
            """)
            
            # Create processing_logs table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                processing_stage TEXT NOT NULL,
                status TEXT NOT NULL,
                processing_time REAL,
                error TEXT,
                created_at TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
            
    async def store_document(self, doc_id, doc_class, data, text):
        """Store document in relational database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if document already exists
            cursor.execute("SELECT id FROM documents WHERE id = ?", (doc_id,))
            existing = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if existing:
                # Update existing document
                cursor.execute("""
                UPDATE documents 
                SET doc_class = ?, text = ?, extracted_data = ?, updated_at = ?
                WHERE id = ?
                """, (
                    doc_class, 
                    text, 
                    json.dumps(data), 
                    now,
                    doc_id
                ))
            else:
                # Insert new document
                cursor.execute("""
                INSERT INTO documents (id, doc_class, text, extracted_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    doc_class,
                    text,
                    json.dumps(data),
                    now,
                    now
                ))
                
            # Store metadata
            self._store_metadata(cursor, doc_id, data)
            
            # Log processing
            cursor.execute("""
            INSERT INTO processing_logs (document_id, processing_stage, status, created_at)
            VALUES (?, ?, ?, ?)
            """, (
                doc_id,
                "integration",
                "success",
                now
            ))
            
            conn.commit()
            conn.close()
            
            return {"status": "success", "id": doc_id}
            
        except Exception as e:
            logger.error(f"Error storing document in relational DB: {str(e)}")
            return {"status": "error", "error": str(e), "id": doc_id}
            
    def _store_metadata(self, cursor, doc_id, data):
        """Store document metadata"""
        # Clear existing metadata
        cursor.execute("DELETE FROM document_metadata WHERE document_id = ?", (doc_id,))
        
        # Extract top-level fields as metadata
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                cursor.execute("""
                INSERT INTO document_metadata (document_id, key, value)
                VALUES (?, ?, ?)
                """, (
                    doc_id,
                    key,
                    str(value)
                ))
                
    async def get_document(self, doc_id):
        """Get document by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
                
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Create document dictionary
            document = dict(zip(column_names, row))
            
            # Parse JSON data
            if "extracted_data" in document and document["extracted_data"]:
                document["extracted_data"] = json.loads(document["extracted_data"])
                
            conn.close()
            
            return document
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
            
    async def get_documents(self, doc_class=None, limit=100, offset=0):
        """Get documents with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if doc_class:
                cursor.execute("""
                SELECT id, doc_class, created_at, updated_at
                FROM documents
                WHERE doc_class = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """, (doc_class, limit, offset))
            else:
                cursor.execute("""
                SELECT id, doc_class, created_at, updated_at
                FROM documents
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """, (limit, offset))
                
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Create document dictionaries
            documents = [dict(zip(column_names, row)) for row in rows]
            
            conn.close()
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return []
            
    async def search_documents(self, query, doc_class=None, limit=100):
        """Search documents using full-text search"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.create_function("REGEXP", 2, lambda pattern, value: bool(re.search(pattern, value)) if value else False)
            cursor = conn.cursor()
            
            if doc_class:
                cursor.execute("""
                SELECT id, doc_class, created_at, updated_at
                FROM documents
                WHERE doc_class = ? AND (text REGEXP ? OR extracted_data REGEXP ?)
                ORDER BY created_at DESC
                LIMIT ?
                """, (doc_class, query, query, limit))
            else:
                cursor.execute("""
                SELECT id, doc_class, created_at, updated_at
                FROM documents
                WHERE text REGEXP ? OR extracted_data REGEXP ?
                ORDER BY created_at DESC
                LIMIT ?
                """, (query, query, limit))
                
          
            rows = cursor.fetchall()
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Create document dictionaries
            documents = [dict(zip(column_names, row)) for row in rows]
            
            conn.close()
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
            
    async def get_processing_metrics(self, start_date=None):
        """Get document processing metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if start_date:
                cursor.execute("""
                SELECT doc_class, COUNT(*) as count, AVG(processing_time) as avg_time
                FROM documents
                JOIN processing_logs ON documents.id = processing_logs.document_id
                WHERE created_at >= ?
                GROUP BY doc_class
                """, (start_date.isoformat(),))
            else:
                cursor.execute("""
                SELECT doc_class, COUNT(*) as count, AVG(processing_time) as avg_time
                FROM documents
                JOIN processing_logs ON documents.id = processing_logs.document_id
                GROUP BY doc_class
                """)
                
            rows = cursor.fetchall()
            
            metrics = [
                {"doc_class": row[0], "count": row[1], "avg_processing_time": row[2] or 0}
                for row in rows
            ]
            
            conn.close()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting processing metrics: {str(e)}")
            return []
            
    async def get_accuracy_metrics(self, start_date=None):
        """Get extraction accuracy metrics"""
        # This is a placeholder since we don't have ground truth data
        # In a real system, this would compare extracted data to validated data
        return []                   