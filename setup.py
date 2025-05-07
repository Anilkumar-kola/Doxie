# setup.py
import os
import sys
from pathlib import Path

def create_directory(path):
    """Create a directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {path}")

def create_file(path, content=""):
    """Create a file with the given content"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created file: {path}")

def setup_project():
    """Set up the project directory structure and files"""
    # Create main directories
    create_directory("data/inbox")
    create_directory("data/processed")
    create_directory("data/failed")
    create_directory("templates")
    create_directory("static")
    
    # Create src directory and modules
    modules = [
        "core",
        "preprocessing",
        "classification",
        "extraction",
        "extraction/schemas",
        "integration",
        "visualization",
        "collection",
        "collection/connectors"
    ]
    
    for module in modules:
        create_directory(f"src/{module}")
        create_file(f"src/{module}/__init__.py", f'"""{module.capitalize()} module for document processing"""\n')
    
    # Create src/__init__.py
    create_file("src/__init__.py", '"""Document Processing System"""\n')
    
    # Create empty implementation files for required modules
    module_files = [
        "core/config.py",
        "core/pipeline.py",
        "core/models.py",
        "preprocessing/processor.py",
        "preprocessing/ocr_engine.py",
        "preprocessing/image_enhancer.py",
        "classification/classifier.py",
        "classification/zero_shot.py",
        "extraction/extractor.py",
        "extraction/llm_client.py",
        "integration/vector_store.py",
        "integration/relation_store.py",
        "visualization/api.py",
        "visualization/metrics.py",
        "collection/collector.py"
    ]
    
    for file in module_files:
        create_file(f"src/{file}", f'"""\n{file} implementation\n"""\n\n# TODO: Implement {file}\n')
    
    # Create upload-icon.svg
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
  <polyline points="17 8 12 3 7 8"></polyline>
  <line x1="12" y1="3" x2="12" y2="15"></line>
</svg>'''
    create_file("static/upload-icon.svg", svg_content)
    
    # Create a default config.json file
    config_content = '''{
  "vector_db_url": "sqlite:///documents.db",
  "ocr_engine": "tesseract",
  "classification_model": "transformer_classifier", 
  "extraction_model": "llm_extractor",
  "llm_provider": "openai",
  "storage": {
    "processed_dir": "data/processed",
    "failed_dir": "data/failed"
  },
  "preprocessing": {
    "image_enhancement": true,
    "deskew": true,
    "noise_removal": true
  }
}'''
    create_file("config.json", config_content)
    
    print("\nProject setup complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install flask werkzeug tqdm pytesseract pdf2image pillow pymupdf openai anthropic")
    print("2. Create your .env file with API keys (optional)")
    print("3. Implement the TODO modules in src/ directory")
    print("4. Try running: python main.py --file data/inbox/your_file.pdf --config config.json")

if __name__ == "__main__":
    setup_project()