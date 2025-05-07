# src/classification/zero_shot.py
import asyncio
import logging
import random
import re
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ZeroShotDocumentClassifier:
    """Zero-shot document classifier that works without pre-trained models"""
    
    def __init__(self):
        # Define candidate document classes with their key indicators
        self.document_classes = {
            "invoice": {
                "indicators": [
                    "invoice", "bill", "payment", "amount due", "tax", "total",
                    "invoice number", "invoice date", "customer", "vendor"
                ],
                "weight": 1.0
            },
            "receipt": {
                "indicators": [
                    "receipt", "thank you for your purchase", "store", "item",
                    "cashier", "cash", "change", "total", "paid", "customer copy"
                ],
                "weight": 0.9
            },
            "contract": {
                "indicators": [
                    "agreement", "contract", "terms", "conditions", "parties",
                    "hereby agree", "signature", "signed", "dated", "legal"
                ],
                "weight": 1.0
            },
            "medical_record": {
                "indicators": [
                    "patient", "diagnosis", "doctor", "treatment", "hospital",
                    "medical", "health", "prescription", "symptoms", "medication"
                ],
                "weight": 1.1
            },
            "resume": {
                "indicators": [
                    "resume", "cv", "curriculum vitae", "experience", "education",
                    "skills", "employment", "job", "career", "professional"
                ],
                "weight": 0.8
            },
            "email": {
                "indicators": [
                    "from:", "to:", "subject:", "sent:", "cc:", "bcc:",
                    "forwarded", "replied", "original message", "regards"
                ],
                "weight": 0.9
            },
            "scientific_paper": {
                "indicators": [
                    "abstract", "introduction", "methodology", "results", "conclusion",
                    "references", "journal", "doi", "fig.", "et al."
                ],
                "weight": 1.1
            },
            "letter": {
                "indicators": [
                    "dear", "sincerely", "regards", "to whom it may concern",
                    "letter", "addressed", "writing to", "yours truly", "date:"
                ],
                "weight": 0.8
            }
        }
    
    async def classify(self, text):
        """Classify document text using zero-shot approach"""
        try:
            # Calculate scores for each class
            scores = {}
            
            text_lower = text.lower()
            
            for doc_class, class_info in self.document_classes.items():
                indicators = class_info["indicators"]
                weight = class_info["weight"]
                
                # Count indicator matches
                match_count = 0
                for indicator in indicators:
                    if re.search(r"\b" + re.escape(indicator.lower()) + r"\b", text_lower):
                        match_count += 1
                        
                # Calculate score
                if indicators:
                    score = (match_count / len(indicators)) * weight
                    scores[doc_class] = score
            
            # Find class with highest score
            if scores:
                best_class = max(scores.items(), key=lambda x: x[1])
                confidence = min(best_class[1], 1.0)  # Cap confidence at 1.0
                
                if confidence > 0:
                    return {
                        "class": best_class[0],
                        "confidence": confidence,
                        "all_scores": scores
                    }
            
            # If no clear match, return unknown
            return {
                "class": "unknown",
                "confidence": 0.1,
                "all_scores": scores
            }
            
        except Exception as e:
            logger.error(f"Zero-shot classification error: {str(e)}")
            return {
                "class": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }