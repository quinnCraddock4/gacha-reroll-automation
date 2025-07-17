import cv2
import numpy as np
import os
from typing import List, Tuple, Dict, Any
from PIL import Image
import pytesseract

class ImageRecognition:
    """Enhanced image recognition for gacha character detection"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self.character_templates = {}
        self.ocr_config = '--oem 3 --psm 6'  # OCR configuration
        
    def load_character_images(self, image_paths: List[str]) -> Dict[str, np.ndarray]:
        """Load and preprocess character images"""
        templates = {}
        
        for path in image_paths:
            if os.path.exists(path):
                try:
                    # Load image
                    img = cv2.imread(path)
                    if img is not None:
                        # Preprocess image
                        processed = self._preprocess_image(img)
                        filename = os.path.basename(path)
                        templates[filename] = processed
                        print(f"Loaded template: {filename}")
                    else:
                        print(f"Failed to load image: {path}")
                except Exception as e:
                    print(f"Error loading image {path}: {str(e)}")
        
        return templates
    
    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """Preprocess image for better matching"""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def detect_characters(self, screenshot_path: str, templates: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        """Detect characters in screenshot using multiple methods"""
        results = []
        
        try:
            # Load screenshot
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                print(f"Failed to load screenshot: {screenshot_path}")
                return results
            
            # Preprocess screenshot
            processed_screenshot = self._preprocess_image(screenshot)
            
            # Method 1: Template matching
            template_results = self._template_matching(processed_screenshot, templates)
            results.extend(template_results)
            
            # Method 2: Feature matching
            feature_results = self._feature_matching(screenshot, templates)
            results.extend(feature_results)
            
            # Method 3: OCR text detection (if character names are visible)
            ocr_results = self._ocr_detection(screenshot)
            results.extend(ocr_results)
            
            # Method 4: Color-based detection - DISABLED to avoid false positives
            # color_results = self._color_detection(screenshot, templates)
            # results.extend(color_results)
            
            # Remove duplicates and sort by confidence
            results = self._deduplicate_results(results)
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
        except Exception as e:
            print(f"Error in character detection: {str(e)}")
        
        return results
    
    def _template_matching(self, screenshot: np.ndarray, templates: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        """Template matching method"""
        results = []
        
        for template_name, template in templates.items():
            try:
                # Multiple template matching methods
                methods = [
                    cv2.TM_CCOEFF_NORMED,
                    cv2.TM_CCORR_NORMED,
                    cv2.TM_SQDIFF_NORMED
                ]
                
                best_confidence = 0
                best_location = None
                best_method = None
                
                for method in methods:
                    result = cv2.matchTemplate(screenshot, template, method)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if method == cv2.TM_SQDIFF_NORMED:
                        confidence = 1 - min_val  # Invert for SQDIFF
                        location = min_loc
                    else:
                        confidence = max_val
                        location = max_loc
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_location = location
                        best_method = method
                
                if best_confidence >= self.confidence_threshold:
                    results.append({
                        'method': 'template_matching',
                        'template': template_name,
                        'confidence': best_confidence,
                        'location': best_location,
                        'method_used': best_method
                    })
            
            except Exception as e:
                print(f"Template matching error for {template_name}: {str(e)}")
        
        return results
    
    def _feature_matching(self, screenshot: np.ndarray, templates: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        """Feature matching using SIFT/SURF"""
        results = []
        
        try:
            # Initialize SIFT detector
            sift = cv2.SIFT_create()
            
            # Find keypoints and descriptors for screenshot
            kp1, des1 = sift.detectAndCompute(screenshot, None)
            
            if des1 is None:
                return results
            
            for template_name, template in templates.items():
                try:
                    # Find keypoints and descriptors for template
                    kp2, des2 = sift.detectAndCompute(template, None)
                    
                    if des2 is None:
                        continue
                    
                    # FLANN matcher
                    FLANN_INDEX_KDTREE = 1
                    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
                    search_params = dict(checks=50)
                    flann = cv2.FlannBasedMatcher(index_params, search_params)
                    
                    matches = flann.knnMatch(des1, des2, k=2)
                    
                    # Apply ratio test
                    good_matches = []
                    for match_pair in matches:
                        if len(match_pair) == 2:
                            m, n = match_pair
                            if m.distance < 0.7 * n.distance:
                                good_matches.append(m)
                    
                    # Calculate confidence based on number of good matches
                    confidence = len(good_matches) / max(len(kp1), len(kp2)) if max(len(kp1), len(kp2)) > 0 else 0
                    
                    if confidence >= self.confidence_threshold * 0.5:  # Lower threshold for feature matching
                        # Calculate center point of matches
                        if good_matches:
                            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                            
                            # Calculate center
                            center_x = int(np.mean(src_pts[:, 0, 0]))
                            center_y = int(np.mean(src_pts[:, 0, 1]))
                            
                            results.append({
                                'method': 'feature_matching',
                                'template': template_name,
                                'confidence': confidence,
                                'location': (center_x, center_y),
                                'matches': len(good_matches)
                            })
                
                except Exception as e:
                    print(f"Feature matching error for {template_name}: {str(e)}")
        
        except Exception as e:
            print(f"Feature matching setup error: {str(e)}")
        
        return results
    
    def _ocr_detection(self, screenshot: np.ndarray) -> List[Dict[str, Any]]:
        """OCR-based text detection"""
        results = []
        
        try:
            # Convert to PIL Image for OCR
            pil_image = Image.fromarray(cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB))
            
            # Extract text
            text = pytesseract.image_to_string(pil_image, config=self.ocr_config)
            
            # Look for character names in the text
            # This would need to be customized based on the specific game
            character_keywords = [
                'SSR', 'SR', 'R', 'UR',  # Rarity indicators
                '5★', '4★', '3★',  # Star ratings
                # Add specific character names here
            ]
            
            for keyword in character_keywords:
                if keyword.lower() in text.lower():
                    results.append({
                        'method': 'ocr',
                        'template': keyword,
                        'confidence': 0.9,  # High confidence for text detection
                        'location': (0, 0),  # Text location not specific
                        'text_found': keyword
                    })
        
        except Exception as e:
            print(f"OCR detection error: {str(e)}")
        
        return results
    
    def _color_detection(self, screenshot: np.ndarray, templates: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        """Color-based detection for specific character colors"""
        results = []
        
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            
            # Define color ranges for different rarities/characters
            color_ranges = {
                'gold': ([20, 100, 100], [30, 255, 255]),  # Gold/Orange
                'purple': ([130, 50, 50], [170, 255, 255]),  # Purple
                'blue': ([100, 50, 50], [130, 255, 255]),  # Blue
                'green': ([40, 50, 50], [80, 255, 255]),  # Green
            }
            
            for color_name, (lower, upper) in color_ranges.items():
                # Create mask for color range
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                
                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 1000:  # Minimum area threshold
                        # Calculate contour center
                        M = cv2.moments(contour)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            
                            results.append({
                                'method': 'color_detection',
                                'template': color_name,
                                'confidence': 0.7,  # Medium confidence for color detection
                                'location': (cx, cy),
                                'area': area
                            })
        
        except Exception as e:
            print(f"Color detection error: {str(e)}")
        
        return results
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate detections"""
        if not results:
            return results
        
        # Group by template and method
        grouped = {}
        for result in results:
            key = (result['template'], result['method'])
            if key not in grouped or result['confidence'] > grouped[key]['confidence']:
                grouped[key] = result
        
        return list(grouped.values())
    
    def create_debug_image(self, screenshot_path: str, detections: List[Dict[str, Any]], output_path: str = None):
        """Create debug image with detection markers"""
        try:
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                return
            
            debug_img = screenshot.copy()
            
            for detection in detections:
                location = detection['location']
                confidence = detection['confidence']
                method = detection['method']
                template = detection['template']
                
                # Draw circle at detection point
                cv2.circle(debug_img, location, 20, (0, 255, 0), 2)
                
                # Draw text label
                label = f"{template} ({confidence:.2f})"
                cv2.putText(debug_img, label, (location[0] + 25, location[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            if output_path:
                cv2.imwrite(output_path, debug_img)
            else:
                cv2.imshow('Debug Detection', debug_img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
        
        except Exception as e:
            print(f"Error creating debug image: {str(e)}")

def detect_characters_in_screenshot(screenshot_path: str, template_paths: List[str] = None, 
                                  confidence_threshold: float = 0.8) -> List[Dict[str, Any]]:
    """Convenience function for character detection"""
    # If no template paths provided, use all images from characters folder
    if template_paths is None:
        characters_dir = "characters"
        if os.path.exists(characters_dir):
            template_paths = []
            for file in os.listdir(characters_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    template_paths.append(os.path.join(characters_dir, file))
            print(f"Using {len(template_paths)} character images from '{characters_dir}' folder")
        else:
            print(f"Warning: Characters directory '{characters_dir}' not found")
            return []
    
    if not template_paths:
        print("Warning: No character images provided")
        return []
    
    recognizer = ImageRecognition(confidence_threshold)
    templates = recognizer.load_character_images(template_paths)
    return recognizer.detect_characters(screenshot_path, templates)

if __name__ == "__main__":
    # Test the image recognition
    import sys
    
    if len(sys.argv) > 2:
        screenshot_path = sys.argv[1]
        template_paths = sys.argv[2:]
        
        detections = detect_characters_in_screenshot(screenshot_path, template_paths)
        print(f"Found {len(detections)} detections:")
        for detection in detections:
            print(f"  {detection}")
    else:
        print("Usage: python image_recognition.py <screenshot_path> <template_path1> [template_path2] ...") 