# src/integration/vector_store.py
import logging
import json
import sqlite3
from typing import Dict, Any, List, Optional

logger = logging.getLogger("vector_store")

class VectorStore:
    """
    Vector database connector for document storage and retrieval
    """
    def __init__(self, db_url=None):
        """
        Initialize the vector store
        
        Args:
            db_url: Database connection URL
        """
        self.db_url = db_url or "sqlite:///documents.db"
        
        # Parse SQLite URL
        if self.db_url.startswith("sqlite:///"):
            self.db_path = self.db_url[10:]
            self._init_sqlite_db()
        else:
            logger.warning(f"Unsupported database URL: {db_url}")
            self.db_path = None
            
    def _init_sqlite_db(self):
        """Initialize SQLite database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create documents table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                doc_type TEXT,
                file_type TEXT,
                file_size INTEGER,
                processed_at TEXT,
                metadata TEXT,
                content TEXT,
                storage_path TEXT
            )
            ''')
            
            # Create extracted_data table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS extracted_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                data TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Initialized SQLite database at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing SQLite database: {str(e)}")
            
    def store_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a document in the vector database
        
        Args:
            document: The document to store
            
        Returns:
            The document with storage information added
        """
        if not self.db_path:
            logger.warning("No database configured, skipping document storage")
            return document
            
        try:
            # Extract fields for storage
            file_path = document.get("file_path", "")
            doc_type = document.get("doc_type", "unknown")
            file_type = document.get("file_type", "")
            file_size = document.get("file_size", 0)
            processed_at = document.get("processed_at", "")
            content = document.get("content", "")
            storage_path = document.get("storage_path", "")
            metadata = json.dumps({
                k: v for k, v in document.items() 
                if k not in ["content", "extracted_data", "file_path", "doc_type", "file_size", "processed_at", "storage_path"]
            })
            
            # Store in SQLite
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert document
            cursor.execute('''
            INSERT INTO documents (file_path, doc_type, file_type, file_size, processed_at, metadata, content, storage_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, doc_type, file_type, file_size, processed_at, metadata, content, storage_path))
            
            document_id = cursor.lastrowid
            
            # Insert extracted_data if available
            if "extracted_data" in document and document["extracted_data"]:
                extracted_data = json.dumps(document["extracted_data"])
                cursor.execute('''
                INSERT INTO extracted_data (document_id, data)
                VALUES (?, ?)
                ''', (document_id, extracted_data))
                
            conn.commit()
            conn.close()
            
            document["storage"] = {
                "id": document_id,
                "location": self.db_path,
                "status": "stored"
            }
            
            logger.info(f"Document stored with ID {document_id}")
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            document["storage"] = {
                "status": "error",
                "error": str(e)
            }
            
        return document
    
    def retrieve_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from the vector database
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            The retrieved document or None if not found
        """
        if not self.db_path:
            logger.warning("No database configured, cannot retrieve document")
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Retrieve document
            cursor.execute('''
            SELECT * FROM documents WHERE id = ?
            ''', (document_id,))
            
            # Get the row first, then check if it exists
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Document not found with ID {document_id}")
                conn.close()
                return None
                
            # Convert row to dict
            document = dict(row)
            
            # Parse metadata
            if document.get("metadata"):
                try:
                    document["metadata"] = json.loads(document["metadata"])
                except:
                    document["metadata"] = {}
                
            # Retrieve extracted_data
            cursor.execute('''
            SELECT data FROM extracted_data WHERE document_id = ?
            ''', (document_id,))
            
            # Get the data row and check if it exists
            data_row = cursor.fetchone()
            if data_row and data_row["data"]:
                try:
                    document["extracted_data"] = json.loads(data_row["data"])
                except:
                    document["extracted_data"] = {}
            else:
                document["extracted_data"] = {}
                
            conn.close()
            
            logger.info(f"Retrieved document with ID {document_id}")
            return document
            
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return None
    
    def get_all_documents(self, doc_type=None, file_type=None, search_query=None, sort_by="processed_at", sort_order="desc", limit=None) -> List[Dict[str, Any]]:
        """
        Get all documents from the database with optional filters
        
        Args:
            doc_type: Optional document type to filter by
            file_type: Optional file type to filter by
            search_query: Optional search query for content
            sort_by: Field to sort by
            sort_order: Sort order ("asc" or "desc")
            limit: Maximum number of results
            
        Returns:
            List of document dictionaries
        """
        if not self.db_path:
            logger.warning("No database configured, cannot get documents")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM documents"
            params = []
            
            # Apply filters
            conditions = []
            if doc_type:
                conditions.append("doc_type = ?")
                params.append(doc_type)
            
            if file_type:
                conditions.append("file_type = ?")
                params.append(file_type)
            
            if search_query:
                conditions.append("(content LIKE ? OR file_path LIKE ?)")
                params.extend([f"%{search_query}%", f"%{search_query}%"])
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Apply sorting
            if sort_by in ["id", "file_path", "doc_type", "file_type", "file_size", "processed_at"]:
                query += f" ORDER BY {sort_by}"
                if sort_order.lower() == "desc":
                    query += " DESC"
                else:
                    query += " ASC"
            
            # Apply limit
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            documents = []
            for row in rows:
                doc = dict(row)
                
                # Parse metadata
                if doc.get("metadata"):
                    try:
                        doc["metadata"] = json.loads(doc["metadata"])
                    except:
                        doc["metadata"] = {}
                
                # Get extracted data in a separate query to avoid "NoneType not iterable" issues
                doc_id = doc["id"]
                extracted_query = "SELECT data FROM extracted_data WHERE document_id = ?"
                cursor.execute(extracted_query, (doc_id,))
                data_row = cursor.fetchone()
                
                if data_row and data_row["data"]:
                    try:
                        doc["extracted_data"] = json.loads(data_row["data"])
                    except:
                        doc["extracted_data"] = {}
                else:
                    doc["extracted_data"] = {}
                
                documents.append(doc)
            
            conn.close()
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            return []
    
    def search_documents(self, query: str, doc_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents in the vector database
        
        Args:
            query: Search query
            doc_type: Optional document type filter
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        if not self.db_path:
            logger.warning("No database configured, cannot search documents")
            return []
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Search query
            if doc_type:
                sql = '''
                SELECT id, file_path, doc_type, file_type, file_size, processed_at, storage_path
                FROM documents 
                WHERE content LIKE ? AND doc_type = ?
                ORDER BY processed_at DESC
                LIMIT ?
                '''
                cursor.execute(sql, (f"%{query}%", doc_type, limit))
            else:
                sql = '''
                SELECT id, file_path, doc_type, file_type, file_size, processed_at, storage_path
                FROM documents 
                WHERE content LIKE ?
                ORDER BY processed_at DESC
                LIMIT ?
                '''
                cursor.execute(sql, (f"%{query}%", limit))
                
            rows = cursor.fetchall()
            
            # Convert rows to dicts
            results = [dict(row) for row in rows]
            
            conn.close()
            
            logger.info(f"Found {len(results)} documents matching query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []