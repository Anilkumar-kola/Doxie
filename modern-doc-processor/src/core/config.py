# core/config.py
import os
import json
from pathlib import Path

class Config:
    """Configuration manager for the document processing system"""
    
    DEFAULT_CONFIG = {
        "vector_db_url": "sqlite:///documents.db",
        "ocr_engine": "tesseract",
        "classification_model": "transformer_classifier",
        "extraction_model": "llm_extractor",
        "storage": {
            "processed_dir": "data/processed",
            "failed_dir": "data/failed"
        },
        "preprocessing": {
            "image_enhancement": True,
            "deskew": True,
            "noise_removal": True
        },
        "document_types": [
            "invoice", 
            "receipt", 
            "contract", 
            "letter", 
            "report",
            "form"
        ],
        "extraction_schemas": {
            "invoice": [
                "invoice_number",
                "date",
                "due_date",
                "vendor_name",
                "vendor_address",
                "customer_name",
                "customer_address",
                "line_items",
                "subtotal",
                "tax",
                "total"
            ]
        }
    }
    
    def __init__(self, config_file=None):
        """Initialize configuration, optionally from a file"""
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                custom_config = json.load(f)
                self._update_config(custom_config)
                
        # Ensure directories exist
        self._ensure_directories()
    
    def _update_config(self, custom_config):
        """Update configuration with custom values"""
        def update_dict(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    update_dict(target[key], value)
                else:
                    target[key] = value
        
        update_dict(self.config, custom_config)
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        for dir_path in [
            self.config["storage"]["processed_dir"],
            self.config["storage"]["failed_dir"]
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get(self, key, default=None):
        """Get a configuration value"""
        keys = key.split('.')
        result = self.config
        
        for k in keys:
            if isinstance(result, dict) and k in result:
                result = result[k]
            else:
                return default
                
        return result
    
    def save(self, config_file):
        """Save current configuration to a file"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)