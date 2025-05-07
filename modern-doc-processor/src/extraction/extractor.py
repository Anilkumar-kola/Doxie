# extraction/extractor.py
import re
import logging
import json
from typing import Dict, Any, List, Optional
from .llm_client import LLMClient

logger = logging.getLogger("extractor")

class Extractor:
    """
    LLM-based data extraction orchestrator
    """
    def __init__(self, llm_provider="openai", api_key=None, model=None):
        """
        Initialize the extractor
        
        Args:
            llm_provider: LLM provider to use ("openai", "anthropic")
            api_key: API key for the LLM provider
            model: Specific model to use
        """
        self.llm_client = LLMClient(provider=llm_provider, api_key=api_key, model=model)
        
        # Define extraction schemas for different document types
        self.schemas = {
            "invoice": {
                "invoice_number": "string",
                "date": "string",
                "due_date": "string",
                "vendor": {
                    "name": "string",
                    "address": "string",
                    "phone": "string",
                    "email": "string"
                },
                "customer": {
                    "name": "string",
                    "address": "string",
                    "account_number": "string"
                },
                "line_items": [
                    {
                        "description": "string",
                        "quantity": "number",
                        "unit_price": "number",
                        "amount": "number"
                    }
                ],
                "subtotal": "number",
                "tax": "number",
                "total": "number",
                "payment_terms": "string"
            },
            "receipt": {
                "merchant_name": "string",
                "store_address": "string",
                "transaction_date": "string",
                "transaction_time": "string",
                "items": [
                    {
                        "description": "string",
                        "quantity": "number",
                        "price": "number"
                    }
                ],
                "subtotal": "number",
                "tax": "number",
                "total": "number",
                "payment_method": "string",
                "card_info": "string"
            }
        }
    
    def extract_data(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from a document based on its type
        
        Args:
            document: The document to extract data from
            
        Returns:
            The document with extracted data added
        """
        doc_type = document.get("doc_type", "unknown")
        text_content = document.get("content", "")
        
        if not text_content:
            logger.warning("No text content to extract from")
            document["extracted_data"] = {}
            return document
            
        logger.info(f"Extracting data from {doc_type} document")
        
        # Try LLM extraction first
        extracted_data = self._extract_with_llm(text_content, doc_type)
        
        # If LLM extraction fails or is empty, fall back to rule-based extraction
        if not extracted_data:
            logger.warning("LLM extraction failed, falling back to rule-based extraction")
            if doc_type == "invoice":
                extracted_data = self._rule_based_invoice_extraction(text_content)
            elif doc_type == "receipt":
                extracted_data = self._rule_based_receipt_extraction(text_content)
            else:
                # Generic extraction using key-value pattern matching
                extracted_data = self._generic_rule_based_extraction(text_content)
            
        document["extracted_data"] = extracted_data
        return document
    
    def _extract_with_llm(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        Extract data using an LLM
        
        Args:
            text: The text to extract from
            doc_type: The document type
            
        Returns:
            Dictionary of extracted fields
        """
        schema = self.schemas.get(doc_type)
        
        if not schema:
            logger.warning(f"No schema defined for document type: {doc_type}")
            return {}
            
        logger.info(f"Extracting data with LLM using {doc_type} schema")
        return self.llm_client.extract_from_text(text, schema)
    
    def extract_invoice_data(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data specific to invoices
        
        Args:
            document: The invoice document
            
        Returns:
            Dictionary of extracted invoice fields
        """
        text_content = document.get("content", "")
        return self._extract_with_llm(text_content, "invoice")
    
    def _rule_based_invoice_extraction(self, text: str) -> Dict[str, Any]:
        """
        Rule-based extraction for invoices as a fallback
        
        Args:
            text: The text to extract from
            
        Returns:
            Dictionary of extracted invoice fields
        """
        # Initialize result structure
        result = {
            "invoice_number": None,
            "date": None,
            "due_date": None,
            "vendor": {
                "name": None,
                "address": None,
                "phone": None,
                "email": None
            },
            "customer": {
                "name": None,
                "address": None,
                "account_number": None
            },
            "line_items": [],
            "subtotal": None,
            "tax": None,
            "total": None,
            "payment_terms": None
        }
        
        # Example patterns
        patterns = {
            "invoice_number": r"Invoice\s*(?:#|No|Number|NUM)?\s*[:#]?\s*([A-Z0-9\-]+)",
            "date": r"(?:Invoice\s*)?Date\s*[:#]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",
            "due_date": r"Due\s*Date\s*[:#]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",
            "subtotal": r"(?:Sub[ -]?total|Amount)[^0-9$€£¥]*([0-9,.]+)",
            "tax": r"(?:Tax|VAT|GST)[^0-9$€£¥]*([0-9,.]+)",
            "total": r"(?:Total|TOTAL|Amount\s*Due)[^0-9$€£¥]*([0-9,.]+)",
            "payment_terms": r"(?:Payment\s*Terms|Terms)[^:]*:\s*([^\.]+)"
        }
        
        # Apply patterns
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Handle nested fields
                if field in ["subtotal", "tax", "total"]:
                    value = match.group(1).strip()
                    # Remove currency symbols and convert to float
                    value = re.sub(r'[^\d\.]', '', value)
                    try:
                        result[field] = float(value)
                    except:
                        result[field] = value
                elif "." in field:
                    # Handle nested fields like vendor.name
                    parts = field.split(".")
                    if len(parts) == 2:
                        if parts[0] in result and isinstance(result[parts[0]], dict):
                            result[parts[0]][parts[1]] = match.group(1).strip()
                else:
                    result[field] = match.group(1).strip()
                
        return result
    
    def _rule_based_receipt_extraction(self, text: str) -> Dict[str, Any]:
        """
        Rule-based extraction for receipts as a fallback
        
        Args:
            text: The text to extract from
            
        Returns:
            Dictionary of extracted receipt fields
        """
        # Similar implementation as _rule_based_invoice_extraction
        # Would be implemented for receipt-specific fields
        return {}
    
    def _generic_rule_based_extraction(self, text: str) -> Dict[str, Any]:
        """
        Generic key-value extraction for unknown document types
        
        Args:
            text: The text content to extract from
            
        Returns:
            Dictionary of extracted key-value pairs
        """
        # Simple key-value pattern
        kv_pattern = r"([A-Za-z\s]+)[\s:]*\s+([$€£¥]?[0-9,.]+|[A-Za-z0-9\s,]+)"
        
        result = {}
        for match in re.finditer(kv_pattern, text):
            if len(match.groups()) == 2:
                key = match.group(1).strip().lower().replace(" ", "_")
                value = match.group(2).strip()
                result[key] = value
                
        return result