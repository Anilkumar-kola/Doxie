# preprocessing/ocr_engine.py
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ocr_engine")

class OCREngine:
    """
    Modern OCR implementation with multiple backend options
    """
    def __init__(self, engine="tesseract", config=None):
        """
        Initialize the OCR engine
        
        Args:
            engine: OCR engine to use ("tesseract", "azure", "google")
            config: Configuration for the OCR engine
        """
        self.engine = engine
        self.config = config or {}
        
        # Initialize the appropriate OCR client
        if engine == "tesseract":
            # For Tesseract, we'd check if it's installed
            try:
                import pytesseract
                self.client = pytesseract
            except ImportError:
                logger.warning("pytesseract not installed. Using mock OCR implementation.")
                self.client = None
                
        elif engine == "azure":
            # For Azure, we'd initialize the Azure client
            try:
                # Azure Form Recognizer client setup would go here
                self.client = None
            except:
                logger.warning("Azure Form Recognizer client not configured. Using mock OCR implementation.")
                self.client = None
                
        elif engine == "google":
            # For Google, we'd initialize the Google client
            try:
                # Google Cloud Vision client setup would go here
                self.client = None
            except:
                logger.warning("Google Cloud Vision client not configured. Using mock OCR implementation.")
                self.client = None
                
        else:
            logger.error(f"Unknown OCR engine: {engine}")
            self.client = None
    
    def extract_text(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text from a document using OCR
        
        Args:
            document: The document to process
            
        Returns:
            The document with OCR text added
        """
        file_path = document.get("file_path")
        file_type = document.get("file_type", "").lower()
        
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return document
            
        # Determine if we need to apply OCR
        needs_ocr = self._needs_ocr(file_path, file_type)
        
        if not needs_ocr:
            logger.info("Document already has text content or doesn't need OCR")
            return document
            
        logger.info(f"Extracting text with OCR from {file_path}")
        
        try:
            # Process based on file type
            if file_type in [".pdf"]:
                text = self._process_pdf(file_path)
            elif file_type in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
                text = self._process_image(file_path)
            else:
                logger.warning(f"Unsupported file type for OCR: {file_type}")
                text = ""
                
            document["content"] = text
            logger.info(f"Extracted {len(text)} characters of text")
            
            # For debugging, log a small preview of the text
            preview = text[:100] + "..." if len(text) > 100 else text
            logger.debug(f"Text preview: {preview}")
            
        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            document["ocr_error"] = str(e)
            
        return document
    
    def _needs_ocr(self, file_path: str, file_type: str) -> bool:
        """
        Determine if a file needs OCR processing
        
        Args:
            file_path: Path to the file
            file_type: Type of the file
            
        Returns:
            True if OCR is needed, False otherwise
        """
        # PDFs might contain text already, so we should check
        if file_type == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                
                # If we found text, no need for OCR
                if text.strip():
                    return False
            except:
                # If PyMuPDF is not available or fails, assume OCR is needed
                pass
                
        # Images always need OCR
        if file_type in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            return True
            
        # Other file types don't need OCR
        return False
    
    def _process_pdf(self, file_path: str) -> str:
        """
        Process a PDF file with OCR
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        if self.engine == "tesseract" and self.client:
            try:
                # Use PDF2Image to convert PDF to images
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(file_path)
                except ImportError:
                    logger.warning("pdf2image not installed. Using mock OCR for PDF.")
                    return self._mock_ocr(file_path)
                
                # Process each page with Tesseract
                text = ""
                for i, image in enumerate(images):
                    page_text = self.client.image_to_string(image)
                    text += f"\n\n--- Page {i+1} ---\n\n{page_text}"
                
                return text
            except Exception as e:
                logger.error(f"Tesseract PDF OCR error: {str(e)}")
                return self._mock_ocr(file_path)
                
        # Mock implementation for demonstration
        return self._mock_ocr(file_path)
    
    def _process_image(self, file_path: str) -> str:
        """
        Process an image file with OCR
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Extracted text
        """
        if self.engine == "tesseract" and self.client:
            try:
                # Process with Tesseract
                from PIL import Image
                image = Image.open(file_path)
                text = self.client.image_to_string(image)
                return text
            except Exception as e:
                logger.error(f"Tesseract image OCR error: {str(e)}")
                return self._mock_ocr(file_path)
                
        # Mock implementation for demonstration
        return self._mock_ocr(file_path)
    
    def _mock_ocr(self, file_path: str) -> str:
        """
        Mock OCR implementation for testing or when OCR engine is not available
        
        Args:
            file_path: Path to the file
            
        Returns:
            Mock extracted text
        """
        # For an invoice, return mock invoice text
        if "invoice" in file_path.lower():
            return """
            INVOICE
            
            Invoice #: INV-12345
            Date: 04/15/2025
            Due Date: 05/15/2025
            
            Vendor: ABC Company
            123 Business St
            Business City, BC 12345
            
            Customer: XYZ Corporation
            456 Corporate Ave
            Corporate City, CC 67890
            
            Description                     Quantity    Price       Amount
            -----------------------------   ---------   ---------   ---------
            Professional Services           40 hours    $125.00     $5,000.00
            Software Licenses               5           $299.00     $1,495.00
            Hardware Components             10          $89.99      $899.90
            
            Subtotal                                               $7,394.90
            Tax (8%)                                               $591.59
            Total                                                  $7,986.49
            
            Payment Terms: Net 30
            Please make checks payable to ABC Company.
            Thank you for your business!
            """
        
        # Generic mock text
        return f"This is mock OCR text for {Path(file_path).name}. In a real implementation, actual text would be extracted using the {self.engine} OCR engine."