# src/extraction/schemas/__init__.py
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_extraction_schema(doc_class):
    """Get extraction schema for a document class"""
    # First check if there's a schema file
    schema_path = Path(f"src/extraction/schemas/{doc_class}.json")
    
    if schema_path.exists():
        try:
            with open(schema_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schema for {doc_class}: {str(e)}")
    
    # If no file exists, return a default schema based on document class
    if doc_class == "invoice":
        from src.extraction.schemas.invoice import INVOICE_SCHEMA
        return INVOICE_SCHEMA
    elif doc_class == "receipt":
        from src.extraction.schemas.invoice import RECEIPT_SCHEMA
        return RECEIPT_SCHEMA
    elif doc_class == "medical_record":
        from src.extraction.schemas.medical_record import MEDICAL_RECORD_SCHEMA
        return MEDICAL_RECORD_SCHEMA
    elif doc_class == "contract":
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "patterns": [
                        r"(?:^|\n)([A-Z][A-Z\s]+)(?:\n|$)",
                        r"(?:AGREEMENT|CONTRACT):?\s*(.*?)(?:\n|$)"
                    ]
                },
                "parties": {
                    "type": "array",
                    "patterns": [
                        r"BETWEEN\s+(.*?)(?:\s+AND\s+|\s*,\s*)(.*?)(?:\.|\n)",
                        r"(?:This|The) Agreement is (?:made and entered into )?(?:by and )?between\s+(.*?)(?:\s+and\s+|\s*,\s*)(.*?)(?:\.|\n)"
                    ]
                },
                "effective_date": {
                    "type": "string",
                    "patterns": [
                        r"(?:EFFECTIVE DATE|DATE)[:.\s]*([\d\/\-\.]+)",
                        r"dated\s+(?:this\s+)?(\d+(?:st|nd|rd|th)?\s+day\s+of\s+[A-Za-z]+,?\s+\d{4})",
                        r"dated\s+(?:this\s+)?((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
                    ]
                },
                "term": {
                    "type": "string",
                    "patterns": [
                        r"(?:TERM|DURATION)[:.\s]*(.*?)(?:\n|\.)",
                        r"(?:shall|will) (?:remain in|be in|continue in) (?:full )?(?:force|effect)(?:.*?)(?:for|until)\s+(.*?)(?:\n|\.)"
                    ]
                },
                "value": {
                    "type": "number",
                    "patterns": [
                        r"(?:CONSIDERATION|PAYMENT|VALUE|AMOUNT|SUM)[:.\s]*\$?\s*([\d,]+(?:\.\d+)?)",
                        r"(?:total|amount|sum)(?:.*?)(?:of)\s+\$?\s*([\d,]+(?:\.\d+)?)"
                    ]
                }
            }
        }
    elif doc_class == "resume":
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "patterns": [
                        r"(?:^|\n)([A-Z][a-z]+(?: [A-Z][a-z]+)+)(?:\n|$)",
                        r"(?:^|\n)([A-Z][A-Z\s]+)(?:\n|$)"
                    ]
                },
                "email": {
                    "type": "string",
                    "patterns": [
                        r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"
                    ]
                },
                "phone": {
                    "type": "string",
                    "patterns": [
                        r"(?:Phone|Tel|Mobile)(?::|\s+)?([\+\(\)\d\s\-\.]{10,})"
                    ]
                },
                "education": {
                    "type": "array",
                    "patterns": [
                        r"(?:EDUCATION|ACADEMIC BACKGROUND)(?:.*?)(?:\n|$)((?:.*\n){1,10})"
                    ]
                },
                "experience": {
                    "type": "array",
                    "patterns": [
                        r"(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|PROFESSIONAL EXPERIENCE)(?:.*?)(?:\n|$)((?:.*\n){1,20})"
                    ]
                },
                "skills": {
                    "type": "array",
                    "patterns": [
                        r"(?:SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES)(?:.*?)(?:\n|$)((?:.*\n){1,10})"
                    ]
                }
            }
        }
    else:
        # Generic schema for unknown document types
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "patterns": [
                        r"(?:^|\n)([A-Z][A-Z\s]+)(?:\n|$)",
                        r"(?:^|\n)([A-Z][a-z]+(?: [A-Z][a-z]+){1,5})(?:\n|$)"
                    ]
                },
                "date": {
                    "type": "string",
                    "patterns": [
                        r"(?:Date|Dated)[:.\s]*([\d\/\-\.]+)",
                        r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
                        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
                    ]
                },
                "key_entities": {
                    "type": "array",
                    "default": []
                },
                "content_summary": {
                    "type": "string",
                    "default": ""
                }
            }
        }