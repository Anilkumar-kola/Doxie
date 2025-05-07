import os
import sys
import json
import datetime
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from our document processing system
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
logger = logging.getLogger("app")

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure uploads
UPLOAD_FOLDER = Path('data/inbox')
PROCESSED_FOLDER = Path('data/processed')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'docx', 'xlsx', 'csv', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max size

# Initialize components
try:
    config = Config()
    processor = Processor()
    ocr_engine = OCREngine()
    classifier = Classifier()
    extractor = Extractor()
    document_storage = DocumentStorage()
    vector_store = VectorStore(config.get("vector_db_url"))
    
    # Create processing pipeline
    pipeline = Pipeline([
        ("preprocess", processor.process),
        ("ocr", ocr_engine.extract_text),
        ("classify", classifier.classify),
        ("extract", extractor.extract_data),
        ("store", document_storage.store_document),
        ("index", vector_store.store_document)
    ])
    
    logger.info("All components initialized successfully")
except Exception as e:
    logger.error(f"Error initializing components: {e}")
    raise

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = Path(app.config['UPLOAD_FOLDER']) / filename
        
        # Ensure upload directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file.save(file_path)
        
        # Process the document
        try:
            document = {
                "file_path": str(file_path),
                "file_size": os.path.getsize(file_path),
                "file_type": Path(file_path).suffix.lower(),
                "content": None,
                "metadata": {},
                "processed_at": datetime.datetime.now().isoformat()
            }
            
            processed_doc = pipeline.run(document)
            
            # Save processed result to processed folder
            result_path = Path(PROCESSED_FOLDER) / f"{filename}_result.json"
            result_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(result_path, 'w') as f:
                json.dump(processed_doc, f, indent=2)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'doc_type': processed_doc.get('doc_type', 'unknown'),
                'extracted_data': processed_doc.get('extracted_data', {})
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/documents')
def list_documents():
    try:
        documents = vector_store.get_all_documents()
        
        # Add file URLs
        for doc in documents:
            storage_path = doc.get('storage_path')
            if storage_path:
                doc['file_url'] = url_for('serve_document', path=storage_path, _external=True)
            else:
                file_path = doc.get('file_path')
                if file_path:
                    doc['file_url'] = url_for('serve_document', path=file_path, _external=True)
                else:
                    doc['file_url'] = None
                    
        return jsonify(documents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/documents/stats')
def get_document_stats():
    # Get document counts
    try:
        documents = vector_store.get_all_documents()
        
        # Count by type
        type_counts = {}
        for doc in documents:
            doc_type = doc.get('doc_type', 'unknown')
            if doc_type in type_counts:
                type_counts[doc_type] += 1
            else:
                type_counts[doc_type] = 1
                
        stats = {
            'total': len(documents),
            'by_type': type_counts
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/serve/document/<path:path>')
def serve_document(path):
    # Convert the path to absolute path from relative
    abs_path = os.path.abspath(path)
    directory = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    
    return send_from_directory(directory, filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/debug')
def debug_info():
    """Debug endpoint to check system status"""
    try:
        # Check document counts
        documents = vector_store.get_all_documents()
        
        # Check file system
        inbox_files = list(UPLOAD_FOLDER.glob('*.*'))
        processed_files = []
        for root, dirs, files in os.walk(PROCESSED_FOLDER):
            for file in files:
                processed_files.append(os.path.join(root, file))
        
        return jsonify({
            'status': 'ok',
            'document_count': len(documents),
            'inbox_files': [str(f) for f in inbox_files],
            'inbox_file_count': len(inbox_files),
            'processed_files': processed_files,
            'processed_file_count': len(processed_files),
            'components': {
                'config': bool(config),
                'processor': bool(processor),
                'ocr_engine': bool(ocr_engine),
                'classifier': bool(classifier),
                'extractor': bool(extractor),
                'document_storage': bool(document_storage),
                'vector_store': bool(vector_store),
                'pipeline': bool(pipeline)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Ensure required directories exist
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
        
    app.run(debug=True, port=5000)