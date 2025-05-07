# classification/classifier.py
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("classifier")

class Classifier:
    """
    Transformer-based document classifier
    """
    def __init__(self, model_path=None):
        """
        Initialize the classifier with an optional specific model
        """
        self.model_path = model_path
        # In a production implementation, load the transformer model here
        
        # Define keywords for rule-based classification
        self.keywords = {
            "invoice": ["invoice", "bill", "payment due", "amount due", "invoice number", "invoice date"],
            "receipt": ["receipt", "transaction", "payment received", "thank you for your purchase", "cashier"],
            "contract": ["agreement", "contract", "terms and conditions", "parties", "hereby agree"],
            "letter": ["dear", "sincerely", "regards", "to whom it may concern"],
            "report": ["report", "analysis", "findings", "executive summary", "conclusion"],
            "form": ["form", "please fill", "signature", "date of birth", "applicant"]
        }
    
    def classify(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document based on its content
        
        Args:
            document: The document to classify
            
        Returns:
            The document with classification added
        """
        file_type = document.get("file_type", "")
        text_content = document.get("content", "")
        
        # First pass: classify based on file extension
        doc_type = self._classify_by_extension(file_type)
        
        # If we have text content, perform more accurate classification
        if text_content:
            # In a production implementation, this would use the transformer model
            # For now, use a simple rule-based approach
            doc_type = self._rule_based_classification(text_content) or doc_type
        
        document["doc_type"] = doc_type
        logger.info(f"Classified document as: {doc_type}")
        
        return document
    
    def _classify_by_extension(self, file_type: str) -> str:
        """
        Classify a document based on its file extension
        
        Args:
            file_type: The file extension
            
        Returns:
            Document type classification
        """
        if file_type == ".pdf":
            return "pdf_document"
        elif file_type in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            return "image_document"
        elif file_type in [".doc", ".docx"]:
            return "word_document"
        elif file_type in [".xls", ".xlsx"]:
            return "spreadsheet"
        else:
            return "unknown_document"
    
    def _rule_based_classification(self, text: str) -> Optional[str]:
        """
        Classify a document based on keyword presence
        
        Args:
            text: The document text content
            
        Returns:
            Document type classification or None if no match
        """
        text = text.lower()
        
        # Check each document type's keywords
        scores = {}
        for doc_type, keywords in self.keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            scores[doc_type] = score
        
        # Get the document type with the highest score
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                # Find all document types with the max score
                max_types = [doc_type for doc_type, score in scores.items() if score == max_score]
                return max_types[0]  # Return the first one if multiple match
        
        return None
    
    def _transformer_classification(self, text: str) -> str:
        """
        Classify a document using a transformer model
        
        Args:
            text: The document text content
            
        Returns:
            Document type classification
        """
        # In a production implementation, this would use the transformer model
        # Something like:
        
        # inputs = self.tokenizer(text, truncation=True, padding=True, return_tensors="pt")
        # outputs = self.model(**inputs)
        # predictions = outputs.logits.argmax(dim=1)
        # return self.id2label[predictions.item()]
        
        # For now, return a generic classification
        return "document"