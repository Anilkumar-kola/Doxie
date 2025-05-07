import os
import sys
import json
import sqlite3
from pathlib import Path

# Add src to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=== Document Processing System Debug Tool ===")

# Check directory structure
print("\nChecking directory structure...")
directories = [
    "data",
    "data/inbox",
    "data/processed",
    "src",
    "src/core",
    "src/preprocessing",
    "src/classification",
    "src/extraction",
    "src/integration",
    "templates",
    "static"
]

for directory in directories:
    path = Path(directory)
    exists = path.exists()
    is_dir = path.is_dir() if exists else False
    print(f"{directory}: {'✓' if exists and is_dir else '✗'} {'(exists)' if exists else '(missing)'}")
    
    if not exists:
        try:
            path.mkdir(parents=True)
            print(f"  Created directory: {directory}")
        except Exception as e:
            print(f"  Error creating directory: {e}")

# Check important files
print("\nChecking important files...")
files = [
    "src/core/__init__.py",
    "src/core/config.py",
    "src/core/pipeline.py",
    "src/preprocessing/__init__.py",
    "src/preprocessing/processor.py",
    "src/preprocessing/ocr_engine.py",
    "src/classification/__init__.py",
    "src/classification/classifier.py",
    "src/extraction/__init__.py",
    "src/extraction/extractor.py",
    "src/integration/__init__.py",
    "src/integration/document_storage.py",
    "src/integration/vector_store.py",
    "templates/index.html",
    "app.py",
    "main.py",
    "batch_process.py",
]

for file in files:
    path = Path(file)
    exists = path.exists()
    print(f"{file}: {'✓' if exists else '✗'} {'(exists)' if exists else '(missing)'}")

# Check database
print("\nChecking database...")
db_path = "documents.db"
if os.path.exists(db_path):
    print(f"{db_path}: ✓ (exists)")
    
    # Check database structure
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"  Tables: {[table[0] for table in tables]}")
        
        # Check document count
        if ('documents',) in tables:
            cursor.execute("SELECT COUNT(*) FROM documents;")
            count = cursor.fetchone()[0]
            print(f"  Document count: {count}")
            
            if count > 0:
                # Get document types
                cursor.execute("SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type;")
                types = cursor.fetchall()
                print(f"  Document types: {dict(types)}")
        
        conn.close()
    except Exception as e:
        print(f"  Error accessing database: {e}")
else:
    print(f"{db_path}: ✗ (missing)")

# Check for documents in the inbox folder
print("\nChecking inbox folder...")
inbox_dir = Path("data/inbox")
if inbox_dir.exists():
    files = list(inbox_dir.glob("*"))
    print(f"Files in inbox: {len(files)}")
    for file in files[:10]:  # Show first 10 files only
        print(f"  {file.name} ({file.stat().st_size} bytes)")
    
    if len(files) > 10:
        print(f"  ...and {len(files) - 10} more files")
else:
    print("Inbox folder does not exist")

# Check for documents in the processed folder
print("\nChecking processed folder...")
processed_dir = Path("data/processed")
if processed_dir.exists():
    # Check each subdirectory
    total_files = 0
    for subdir in processed_dir.glob("*"):
        if subdir.is_dir():
            files = list(subdir.glob("*"))
            file_count = len(files)
            total_files += file_count
            print(f"  {subdir.name}: {file_count} files")
    
    print(f"Total processed files: {total_files}")
else:
    print("Processed folder does not exist")

# Test imports
print("\nTesting imports...")
try:
    from core.config import Config
    print("✓ Successfully imported Config")
except ImportError as e:
    print(f"✗ Failed to import Config: {e}")

try:
    from core.pipeline import Pipeline
    print("✓ Successfully imported Pipeline")
except ImportError as e:
    print(f"✗ Failed to import Pipeline: {e}")

try:
    from preprocessing.processor import Processor
    print("✓ Successfully imported Processor")
except ImportError as e:
    print(f"✗ Failed to import Processor: {e}")

try:
    from preprocessing.ocr_engine import OCREngine
    print("✓ Successfully imported OCREngine")
except ImportError as e:
    print(f"✗ Failed to import OCREngine: {e}")

try:
    from classification.classifier import Classifier
    print("✓ Successfully imported Classifier")
except ImportError as e:
    print(f"✗ Failed to import Classifier: {e}")

try:
    from extraction.extractor import Extractor
    print("✓ Successfully imported Extractor")
except ImportError as e:
    print(f"✗ Failed to import Extractor: {e}")

try:
    from integration.document_storage import DocumentStorage
    print("✓ Successfully imported DocumentStorage")
except ImportError as e:
    print(f"✗ Failed to import DocumentStorage: {e}")

try:
    from integration.vector_store import VectorStore
    print("✓ Successfully imported VectorStore")
except ImportError as e:
    print(f"✗ Failed to import VectorStore: {e}")

print("\nDebug complete! Check the output above for any issues.")
print("To fix your dashboard not updating, make sure:")
print("1. You've added the JavaScript code to templates/index.html")
print("2. The DocumentStorage class is properly implemented")
print("3. All imports are consistent across main.py, app.py, and batch_process.py")