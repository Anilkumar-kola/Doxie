# src/preprocessing/image_enhancer.py
import cv2
import numpy as np
import logging
import asyncio

logger = logging.getLogger(__name__)

class DocumentImageEnhancer:
    """Enhances document images for better OCR and processing"""
    
    async def enhance(self, image):
        """Enhance document image for better readability and OCR"""
        try:
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
                
            # Apply initial denoising
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Detect if document is skewed
            enhanced = await self._correct_skew(binary)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Image enhancement failed: {str(e)}")
            # Return original image if enhancement fails
            return image
            
    async def _correct_skew(self, image):
        """Detect and correct skew in document image"""
        try:
            # Find all contours
            contours, hierarchy = cv2.findContours(
                image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Find contours with significant area
            mask = np.zeros(image.shape, dtype=np.uint8)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Adjust threshold as needed
                    cv2.drawContours(mask, [contour], -1, 255, -1)
                    
            # Find lines using Hough transform
            lines = cv2.HoughLinesP(
                mask, 1, np.pi/180, 100, minLineLength=100, maxLineGap=50
            )
            
            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    if x2 - x1 == 0:  # Vertical line
                        continue
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    if -45 < angle < 45:  # Filter out vertical-ish lines
                        angles.append(angle)
                        
                if angles:
                    # Use median angle to avoid outliers
                    median_angle = np.median(angles)
                    
                    # Rotate image if skew is significant
                    if abs(median_angle) > 0.5:
                        h, w = image.shape
                        center = (w//2, h//2)
                        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        rotated = cv2.warpAffine(
                            image, M, (w, h), flags=cv2.INTER_CUBIC, 
                            borderMode=cv2.BORDER_REPLICATE
                        )
                        return rotated
            
            # Return original if no significant skew detected
            return image
            
        except Exception as e:
            logger.error(f"Skew correction failed: {str(e)}")
            return image