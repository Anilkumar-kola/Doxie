# src/preprocessing/processor.py
import asyncio
import numpy as np
import cv2
from pathlib import Path
import json
import torch
from PIL import Image

from transformers import AutoProcessor, DonutProcessor
from src.preprocessing.ocr_engine import OCREngine
from src.preprocessing.image_enhancer import DocumentImageEnhancer
from src.core.config import get_settings

settings = get_settings()

class MultimodalDocumentProcessor:
    """Processes documents using multimodal techniques combining visual and textual analysis"""
    
    def __init__(self):
        self.processed_dir = Path(settings.storage.processed_documents_path)
        self.processed_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize document image enhancer
        self.image_enhancer = DocumentImageEnhancer()
        
        # Initialize OCR engine
        self.ocr_engine = OCREngine()
        
        # Initialize visual document processor
        self.visual_processor = AutoProcessor.from_pretrained(
            settings.models.visual_processor
        )
        
        # Device configuration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    async def process_document(self, file_info):
        """Process a document based on its format"""
        file_path = Path(file_info["path"])
        metadata = file_info["metadata"]
        
        # Create output directory
        doc_id = metadata["id"]
        output_dir = self.processed_dir / doc_id
        output_dir.mkdir(exist_ok=True)
        
        # Determine document type from mime type
        mime_type = metadata.get("mime_type", "")
        
        if mime_type.startswith("image/"):
            result = await self._process_image_document(file_path, output_dir)
        elif mime_type == "application/pdf":
            result = await self._process_pdf_document(file_path, output_dir)
        elif mime_type.startswith("application/vnd.openxmlformats"):
            result = await self._process_office_document(file_path, output_dir, mime_type)
        else:
            result = await self._process_other_document(file_path, output_dir, mime_type)
            
        # Save processing result
        result_path = output_dir / "processing_result.json"
        async with aiofiles.open(result_path, "w") as f:
            await f.write(json.dumps(result, indent=2))
            
        # Return processed document information
        return {
            "id": doc_id,
            "processed_dir": str(output_dir),
            "processing_result": result,
            "original_metadata": metadata
        }
        
    async def _process_image_document(self, file_path, output_dir):
        """Process an image-based document"""
        # Read image
        image = cv2.imread(str(file_path))
        
        # Enhance image
        enhanced_image = await self.image_enhancer.enhance(image)
        
        # Save enhanced image
        enhanced_path = output_dir / "enhanced.png"
        cv2.imwrite(str(enhanced_path), enhanced_image)
        
        # Perform OCR
        ocr_result = await self.ocr_engine.recognize(enhanced_image)
        
        # Save OCR text
        text_path = output_dir / "extracted_text.txt"
        async with aiofiles.open(text_path, "w") as f:
            await f.write(ocr_result["text"])
            
        # Save OCR details (word positions, confidence scores)
        ocr_details_path = output_dir / "ocr_details.json"
        async with aiofiles.open(ocr_details_path, "w") as f:
            await f.write(json.dumps(ocr_result["details"], indent=2))
            
        # Get visual embeddings
        visual_embeddings = await self._get_visual_embeddings(enhanced_image)
        
        # Save visual embeddings
        embeddings_path = output_dir / "visual_embeddings.npy"
        np.save(str(embeddings_path), visual_embeddings.cpu().numpy())
        
        return {
            "document_type": "image",
            "extracted_text_path": str(text_path),
            "enhanced_image_path": str(enhanced_path),
            "ocr_details_path": str(ocr_details_path),
            "visual_embeddings_path": str(embeddings_path),
            "total_words": len(ocr_result["details"]["words"]),
            "average_confidence": ocr_result["details"]["avg_confidence"]
        }
        
    async def _process_pdf_document(self, file_path, output_dir):
        """Process a PDF document with visual and textual analysis"""
        # Similar implementation as image document but with PDF page handling...
        # This would extract each page as an image, process it, and combine results
        
    async def _process_office_document(self, file_path, output_dir, mime_type):
        """Process Microsoft Office documents"""
        # Implementation for processing Word, Excel documents...
        
    async def _process_other_document(self, file_path, output_dir, mime_type):
        """Process other types of documents"""
        # Fallback processing for other document types...
        
    async def _get_visual_embeddings(self, image):
        """Get visual embeddings from document image"""
        # Convert OpenCV image to PIL
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Process image with visual processor
        inputs = self.visual_processor(images=pil_image, return_tensors="pt").to(self.device)
        
        # Get visual embeddings
        with torch.no_grad():
            visual_embeddings = self.visual_model.get_image_features(**inputs)
            
        return visual_embeddings