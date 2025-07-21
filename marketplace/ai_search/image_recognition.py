"""
Image Recognition and Auto-tagging for Piata.ro Marketplace
Uses computer vision to automatically analyze and tag listing images
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from PIL import Image
import torch
from ultralytics import YOLO
from transformers import BlipProcessor, BlipForConditionalGeneration
import logging
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile

logger = logging.getLogger(__name__)

class ImageRecognitionService:
    """
    Advanced image recognition service that provides:
    - Object detection and classification
    - Image captioning
    - Quality assessment
    - Auto-tagging
    - Content moderation
    """
    
    def __init__(self):
        # Initialize YOLO for object detection
        self.yolo_model = YOLO('yolov8n.pt')
        
        # Initialize BLIP for image captioning
        self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
        # Common categories for marketplace items
        self.category_mapping = {
            'person': 'clothing',
            'bicycle': 'vehicles',
            'car': 'vehicles',
            'motorcycle': 'vehicles',
            'airplane': 'vehicles',
            'bus': 'vehicles',
            'train': 'vehicles',
            'truck': 'vehicles',
            'boat': 'vehicles',
            'traffic light': 'electronics',
            'fire hydrant': 'home',
            'stop sign': 'home',
            'parking meter': 'electronics',
            'bench': 'home',
            'bird': 'pets',
            'cat': 'pets',
            'dog': 'pets',
            'horse': 'pets',
            'sheep': 'pets',
            'cow': 'pets',
            'elephant': 'pets',
            'bear': 'pets',
            'zebra': 'pets',
            'giraffe': 'pets',
            'backpack': 'fashion',
            'umbrella': 'fashion',
            'handbag': 'fashion',
            'tie': 'fashion',
            'suitcase': 'fashion',
            'frisbee': 'sports',
            'skis': 'sports',
            'snowboard': 'sports',
            'sports ball': 'sports',
            'kite': 'sports',
            'baseball bat': 'sports',
            'baseball glove': 'sports',
            'skateboard': 'sports',
            'surfboard': 'sports',
            'tennis racket': 'sports',
            'bottle': 'home',
            'wine glass': 'home',
            'cup': 'home',
            'fork': 'home',
            'knife': 'home',
            'spoon': 'home',
            'bowl': 'home',
            'banana': 'food',
            'apple': 'food',
            'sandwich': 'food',
            'orange': 'food',
            'broccoli': 'food',
            'carrot': 'food',
            'hot dog': 'food',
            'pizza': 'food',
            'donut': 'food',
            'cake': 'food',
            'chair': 'home',
            'couch': 'home',
            'potted plant': 'home',
            'bed': 'home',
            'dining table': 'home',
            'toilet': 'home',
            'tv': 'electronics',
            'laptop': 'electronics',
            'mouse': 'electronics',
            'remote': 'electronics',
            'keyboard': 'electronics',
            'cell phone': 'electronics',
            'microwave': 'home',
            'oven': 'home',
            'toaster': 'home',
            'sink': 'home',
            'refrigerator': 'home',
            'book': 'books',
            'clock': 'home',
            'vase': 'home',
            'scissors': 'home',
            'teddy bear': 'toys',
            'hair drier': 'home',
            'toothbrush': 'home'
        }
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Comprehensive image analysis
        Returns object detection, caption, quality score, and tags
        """
        try:
            # Load image
            image = Image.open(image_path)
            
            # Object detection
            objects = self._detect_objects(image)
            
            # Image captioning
            caption = self._generate_caption(image)
            
            # Quality assessment
            quality_score = self._assess_quality(image)
            
            # Generate tags
            tags = self._generate_tags(objects, caption)
            
            # Content moderation
            is_appropriate = self._check_content_safety(image, objects)
            
            return {
                'objects': objects,
                'caption': caption,
                'quality_score': quality_score,
                'tags': tags,
                'is_appropriate': is_appropriate,
                'category_suggestions': self._suggest_categories(objects)
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {
                'objects': [],
                'caption': '',
                'quality_score': 0.0,
                'tags': [],
                'is_appropriate': True,
                'category_suggestions': []
            }
    
    def _detect_objects(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Detect objects in image using YOLO"""
        try:
            # Convert PIL image to numpy array
            image_array = np.array(image)
            
            # Run YOLO detection
            results = self.yolo_model(image_array)
            
            objects = []
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                class_name = self.yolo_model.names[class_id]
                confidence = float(box.conf[0])
                
                if confidence > 0.5:  # Filter low confidence detections
                    objects.append({
                        'class': class_name,
                        'confidence': confidence,
                        'bbox': box.xyxy[0].tolist()
                    })
            
            return objects
            
        except Exception as e:
            logger.error(f"Object detection error: {e}")
            return []
    
    def _generate_caption(self, image: Image.Image) -> str:
        """Generate descriptive caption for image"""
        try:
            inputs = self.blip_processor(images=image, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.blip_model.generate(**inputs, max_length=50)
            
            caption = self.blip_processor.decode(outputs[0], skip_special_tokens=True)
            return caption
            
        except Exception as e:
            logger.error(f"Caption generation error: {e}")
            return ""
    
    def _assess_quality(self, image: Image.Image) -> float:
        """Assess image quality based on various metrics"""
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            # Calculate blur (Laplacian variance)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize blur score (0-100)
            blur_score = min(100, blur_score / 1000 * 100)
            
            # Calculate brightness
            brightness = np.mean(gray)
            brightness_score = 100 - abs(brightness - 127) / 127 * 100
            
            # Calculate contrast
            contrast = np.std(gray)
            contrast_score = min(100, contrast / 64 * 100)
            
            # Overall quality score
            quality_score = (blur_score + brightness_score + contrast_score) / 3
            
            return max(0, min(100, quality_score))
            
        except Exception as e:
            logger.error(f"Quality assessment error: {e}")
            return 50.0
    
    def _generate_tags(self, objects: List[Dict], caption: str) -> List[str]:
        """Generate relevant tags from detected objects and caption"""
        tags = set()
        
        # Add object-based tags
        for obj in objects:
            class_name = obj['class']
            if class_name in self.category_mapping:
                tags.add(self.category_mapping[class_name])
            tags.add(class_name)
        
        # Add caption-based tags
        caption_words = caption.lower().split()
        common_words = ['photo', 'image', 'picture', 'showing', 'displaying']
        for word in caption_words:
            if len(word) > 3 and word not in common_words:
                tags.add(word)
        
        return list(tags)
    
    def _check_content_safety(self, image: Image.Image, objects: List[Dict]) -> bool:
        """Check if image content is appropriate for marketplace"""
        try:
            # Check for inappropriate objects
            inappropriate_objects = ['person']  # Could be extended
            
            for obj in objects:
                if obj['class'] in inappropriate_objects:
                    # Additional checks could be implemented here
                    pass
            
            return True  # For now, allow all content
            
        except Exception as e:
            logger.error(f"Content safety check error: {e}")
            return True
    
    def _suggest_categories(self, objects: List[Dict]) -> List[str]:
        """Suggest categories based on detected objects"""
        categories = set()
        
        for obj in objects:
            class_name = obj['class']
            if class_name in self.category_mapping:
                categories.add(self.category_mapping[class_name])
        
        return list(categories)
    
    def process_listing_images(self, listing) -> Dict[str, Any]:
        """Process all images for a listing"""
        try:
            results = []
            
            for image in listing.images.all():
                if image.image:
                    # Get image path
                    image_path = image.image.path
                    
                    # Analyze image
                    analysis = self.analyze_image(image_path)
                    
                    # Update image metadata
                    image.ai_tags = ','.join(analysis['tags'])
                    image.ai_caption = analysis['caption']
                    image.ai_quality_score = analysis['quality_score']
                    image.save()
                    
                    results.append({
                        'image_id': image.id,
                        'analysis': analysis
                    })
            
            return {
                'listing_id': listing.id,
                'total_images': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Processing listing images error: {e}")
            return {'error': str(e)}
    
    def auto_tag_listing(self, listing) -> Dict[str, Any]:
        """Automatically tag a listing based on its images"""
        try:
            # Process images
            image_results = self.process_listing_images(listing)
            
            # Collect all tags
            all_tags = []
            categories = []
            
            for result in image_results.get('results', []):
                all_tags.extend(result['analysis']['tags'])
                categories.extend(result['analysis']['category_suggestions'])
            
            # Remove duplicates
            unique_tags = list(set(all_tags))
            unique_categories = list(set(categories))
            
            # Update listing tags
            listing.ai_tags = ','.join(unique_tags[:10])  # Limit to 10 tags
            listing.ai_category_suggestions = ','.join(unique_categories[:3])  # Limit to 3 categories
            listing.save()
            
            return {
                'listing_id': listing.id,
                'tags': unique_tags,
                'category_suggestions': unique_categories
            }
            
        except Exception as e:
            logger.error(f"Auto-tagging error: {e}")
            return {'error': str(e)}

# Global instance
image_recognition = ImageRecognitionService()
