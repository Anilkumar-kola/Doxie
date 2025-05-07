# src/extraction/extractor.py
import logging
import datetime

logger = logging.getLogger(__name__)

class Extractor:
    """Simple data extractor for documents"""
    
    def __init__(self):
        """Initialize the extractor"""
        logger.info("Extractor initialized")
        
    def extract_data(self, document):
        """Extract data from a document (mock implementation)"""
        doc_type = document.get("doc_type", "unknown")
        
        # Prepare extracted data based on document type
        if doc_type == "invoice":
            extracted_data = self.extract_invoice_data(document)
        elif doc_type == "receipt":
            extracted_data = self.extract_receipt_data(document)
        else:
            extracted_data = {}
            
        document["extracted_data"] = extracted_data
        return document
        
    def extract_invoice_data(self, document):
        """Extract invoice data (mock implementation)"""
        # Return mock invoice data
        return {
            "invoice_number": f"INV-{datetime.datetime.now().strftime('%Y%m%d')}",
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
            "total": "123.45",
            "vendor": {
                "name": "Sample Vendor",
                "address": "123 Vendor St, Vendor City"
            },
            "customer": {
                "name": "Sample Customer",
                "address": "456 Customer Ave, Customer Town"
            }
        }
        
    def extract_receipt_data(self, document):
        """Extract receipt data (mock implementation)"""
        # Return mock receipt data
        return {
            "merchant": "Sample Store",
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "total": "45.67"
        }