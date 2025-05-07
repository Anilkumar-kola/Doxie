import os
import sqlite3
import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure uploads
UPLOAD_FOLDER = Path('data/inbox')
DB_PATH = 'documents_test.db'  # Use a new db file to avoid conflicts

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max size

def init_db():
    """Initialize a very simple database structure"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Very simple documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        file_path TEXT,
        doc_type TEXT,
        file_size INTEGER,
        processed_at TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Simple database initialized.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Extremely simple home page
    documents = get_all_documents()
    return render_template('simple_index.html', documents=documents)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
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
            
            # Save the file
            file.save(file_path)
            
            # Store in simple database
            store_document(filename, str(file_path))
            
            return redirect(url_for('index'))
            
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload a Document</title>
    </head>
    <body>
        <h1>Upload a Document</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
        <p><a href="/">Back to Home</a></p>
    </body>
    </html>
    '''

def store_document(filename, file_path):
    """Store document info in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Determine document type based on filename
    doc_type = "unknown"
    if "invoice" in filename.lower():
        doc_type = "invoice"
    elif "receipt" in filename.lower():
        doc_type = "receipt"
    elif "contract" in filename.lower():
        doc_type = "contract"
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Store in database
    cursor.execute('''
    INSERT INTO documents (filename, file_path, doc_type, file_size, processed_at)
    VALUES (?, ?, ?, ?, ?)
    ''', (filename, file_path, doc_type, file_size, datetime.datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_all_documents():
    """Get all documents from the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM documents ORDER BY processed_at DESC")
    documents = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return documents

@app.route('/document/<int:doc_id>')
def view_document(doc_id):
    """View a document by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()  # Fetch once and store result
    document = dict(row) if row else None
    
    conn.close()
    
    if not document:
        return "Document not found", 404
    
    file_path = document['file_path']
    return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))

@app.route('/simple_template')
def simple_template():
    """Generate a simple template file for testing"""
    template_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Simple Document System</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .document-list { margin-top: 20px; }
        .document-item { 
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>Simple Document System</h1>
    <a href="/upload">Upload New Document</a>
    
    <div class="document-list">
        <h2>All Documents</h2>
        {% if documents %}
            {% for doc in documents %}
                <div class="document-item">
                    <h3>{{ doc.filename }}</h3>
                    <p>Type: {{ doc.doc_type }}</p>
                    <p>Size: {{ doc.file_size }} bytes</p>
                    <p>Processed at: {{ doc.processed_at }}</p>
                    <a href="/document/{{ doc.id }}">View Document</a>
                </div>
            {% endfor %}
        {% else %}
            <p>No documents found. Please upload some documents.</p>
        {% endif %}
    </div>
</body>
</html>
'''
    
    # Write the template to the templates directory
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    with open(templates_dir / 'simple_index.html', 'w') as f:
        f.write(template_content)
    
    return "Template created successfully"

@app.route('/check_files')
def check_files():
    """Check if uploaded files exist"""
    inbox_dir = Path('data/inbox')
    files = []
    
    if inbox_dir.exists():
        for file_path in inbox_dir.glob('*'):
            if file_path.is_file():
                files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'exists': file_path.exists()
                })
    
    return jsonify({
        'files': files,
        'count': len(files)
    })

if __name__ == '__main__':
    # Create upload directory
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Create simple template
    with app.test_request_context():
        simple_template()
    
    app.run(debug=True, port=5000)