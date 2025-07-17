#!/usr/bin/env python3
"""
Smart Character Detection
Learns what Twin Turbo looks like from multiple images and detects the character intelligently
"""

import cv2
import numpy as np
import os
import sys
from typing import List, Dict, Any

class SmartCharacterDetector:
    """Smart detector that learns character features from multiple images"""
    
    def __init__(self, confidence_threshold=0.7):
        self.confidence_threshold = confidence_threshold
        self.character_features = []
        self.character_keypoints = []
        self.character_descriptors = []
        
    def learn_character(self, character_images_dir="characters"):
        """Learn what the character looks like from multiple images"""
        print("=== LEARNING TWIN TURBO CHARACTER ===")
        
        if not os.path.exists(character_images_dir):
            print(f"ERROR: Characters directory '{character_images_dir}' not found")
            return False
        
        # Get all character images
        character_images = []
        for file in os.listdir(character_images_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                character_images.append(os.path.join(character_images_dir, file))
        
        if not character_images:
            print(f"ERROR: No image files found in '{character_images_dir}' directory")
            return False
        
        print(f"Learning from {len(character_images)} character images:")
        for img in character_images:
            print(f"  - {os.path.basename(img)}")
        print()
        
        # Initialize SIFT detector
        sift = cv2.SIFT_create()
        
        # Extract features from all character images
        all_keypoints = []
        all_descriptors = []
        
        for img_path in character_images:
            try:
                # Load image
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Warning: Could not load {img_path}")
                    continue
                
                # Convert to grayscale
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Extract SIFT features
                keypoints, descriptors = sift.detectAndCompute(gray, None)
                
                if descriptors is not None and len(keypoints) > 0:
                    all_keypoints.extend(keypoints)
                    all_descriptors.append(descriptors)
                    print(f"✅ {os.path.basename(img_path)}: {len(keypoints)} features")
                else:
                    print(f"⚠️  {os.path.basename(img_path)}: No features found")
                    
            except Exception as e:
                print(f"Error processing {img_path}: {str(e)}")
        
        if not all_descriptors:
            print("ERROR: No features could be extracted from character images")
            return False
        
        # Combine all descriptors
        self.character_descriptors = np.vstack(all_descriptors)
        self.character_keypoints = all_keypoints
        
        print(f"\n✅ Learned {len(self.character_keypoints)} total features")
        print(f"✅ Character model ready for detection")
        return True
    
    def detect_character(self, screenshot_path):
        """Detect Twin Turbo character in screenshot using learned features"""
        print(f"\n=== DETECTING TWIN TURBO ===")
        print(f"Screenshot: {os.path.basename(screenshot_path)}")
        
        if self.character_descriptors is None or len(self.character_descriptors) == 0:
            print("ERROR: Character model not learned. Run learn_character() first.")
            return []
        
        try:
            # Load screenshot
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                print(f"ERROR: Could not load screenshot: {screenshot_path}")
                return []
            
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Initialize SIFT detector
            sift = cv2.SIFT_create()
            
            # Extract features from screenshot
            screenshot_keypoints, screenshot_descriptors = sift.detectAndCompute(gray, None)
            
            if screenshot_descriptors is None:
                print("No features found in screenshot")
                return []
            
            print(f"Found {len(screenshot_keypoints)} features in screenshot")
            
            # FLANN matcher for fast matching
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            
            # Match features
            matches = flann.knnMatch(self.character_descriptors, screenshot_descriptors, k=2)
            
            # Apply ratio test to get good matches
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:  # Lowe's ratio test
                        good_matches.append(m)
            
            print(f"Found {len(good_matches)} good matches")
            
            if len(good_matches) < 10:  # Need minimum matches
                print("Not enough good matches found")
                return []
            
            # Group matches by location to find character instances
            character_instances = self._group_matches_by_location(
                good_matches, 
                self.character_keypoints, 
                screenshot_keypoints
            )
            
            # Convert to detection format
            detections = []
            for i, instance in enumerate(character_instances):
                center_x, center_y = instance['center']
                confidence = instance['confidence']
                
                detections.append({
                    'method': 'smart_detection',
                    'template': 'Twin_Turbo',
                    'confidence': confidence,
                    'location': (int(center_x), int(center_y)),
                    'matches': instance['match_count']
                })
            
            # Sort by confidence
            detections.sort(key=lambda x: x['confidence'], reverse=True)
            
            return detections
            
        except Exception as e:
            print(f"ERROR during detection: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _group_matches_by_location(self, good_matches, char_keypoints, screenshot_keypoints):
        """Group matches by location to find distinct character instances"""
        if not good_matches:
            return []
        
        # Get matched points in screenshot
        matched_points = []
        for match in good_matches:
            point = screenshot_keypoints[match.trainIdx].pt
            matched_points.append(point)
        
        # Cluster points to find character instances
        instances = []
        used_points = set()
        
        for i, point in enumerate(matched_points):
            if i in used_points:
                continue
            
            # Find nearby points (same character instance)
            cluster_points = [point]
            used_points.add(i)
            
            for j, other_point in enumerate(matched_points):
                if j in used_points:
                    continue
                
                # Calculate distance
                distance = ((point[0] - other_point[0])**2 + (point[1] - other_point[1])**2)**0.5
                if distance < 100:  # Within 100 pixels
                    cluster_points.append(other_point)
                    used_points.add(j)
            
            # Calculate cluster center and confidence
            if len(cluster_points) >= 5:  # Minimum points for valid detection
                center_x = sum(p[0] for p in cluster_points) / len(cluster_points)
                center_y = sum(p[1] for p in cluster_points) / len(cluster_points)
                
                # Confidence based on number of matches and their quality
                confidence = min(0.95, len(cluster_points) / 20.0 + 0.5)
                
                instances.append({
                    'center': (center_x, center_y),
                    'confidence': confidence,
                    'match_count': len(cluster_points),
                    'points': cluster_points
                })
        
        return instances

def count_twin_turbo(screenshot_path, confidence_threshold=0.7):
    """Count Twin Turbo characters using smart detection"""
    print("=== SMART TWIN TURBO DETECTOR ===")
    print(f"Screenshot: {os.path.basename(screenshot_path)}")
    print(f"Confidence threshold: {confidence_threshold}")
    print()
    
    # Initialize detector
    detector = SmartCharacterDetector(confidence_threshold)
    
    # Learn character from images
    if not detector.learn_character():
        return 0
    
    # Detect characters
    detections = detector.detect_character(screenshot_path)
    
    # Filter by confidence threshold
    filtered_detections = [d for d in detections if d['confidence'] >= confidence_threshold]
    
    # Remove duplicates (characters too close together)
    unique_detections = []
    for detection in filtered_detections:
        location = detection['location']
        
        # Check if too close to existing detections
        is_duplicate = False
        for existing in unique_detections:
            existing_location = existing['location']
            distance = ((location[0] - existing_location[0])**2 + 
                       (location[1] - existing_location[1])**2)**0.5
            if distance < 80:  # Within 80 pixels
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_detections.append(detection)
    
    # Display results
    print(f"\n=== RESULTS ===")
    print(f"Total detections: {len(detections)}")
    print(f"After confidence filter: {len(filtered_detections)}")
    print(f"Unique Twin Turbo instances: {len(unique_detections)}")
    print()
    
    if unique_detections:
        print("Twin Turbo locations:")
        for i, detection in enumerate(unique_detections):
            location = detection['location']
            confidence = detection['confidence']
            matches = detection['matches']
            print(f"  {i+1}. At {location} (confidence: {confidence:.3f}, matches: {matches})")
        
        # Show visual results
        show_visual_results(screenshot_path, unique_detections)
    else:
        print("❌ No Twin Turbo characters detected")
    
    return len(unique_detections)

def show_visual_results(screenshot_path, detections):
    """Show screenshot with detection markers"""
    try:
        screenshot = cv2.imread(screenshot_path)
        if screenshot is None:
            print("Could not load screenshot for visualization")
            return
        
        debug_img = screenshot.copy()
        
        for i, detection in enumerate(detections):
            location = detection['location']
            confidence = detection['confidence']
            matches = detection['matches']
            
            # Draw circle
            cv2.circle(debug_img, location, 40, (0, 255, 0), 3)
            
            # Draw number
            cv2.circle(debug_img, location, 15, (0, 255, 0), -1)
            cv2.putText(debug_img, str(i+1), (location[0] - 8, location[1] + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Draw label
            label = f"Twin Turbo ({confidence:.2f}, {matches} matches)"
            cv2.putText(debug_img, label, (location[0] + 50, location[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Resize if too large
        height, width = debug_img.shape[:2]
        max_width = 1200
        max_height = 800
        
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            debug_img = cv2.resize(debug_img, (new_width, new_height))
        
        print("\nShowing detection results (press any key to close)...")
        cv2.imshow('Smart Twin Turbo Detection', debug_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error showing visualization: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command line mode
        screenshot_path = sys.argv[1]
        confidence = 0.7
        
        if len(sys.argv) > 2:
            try:
                confidence = float(sys.argv[2])
            except ValueError:
                print("Invalid confidence threshold. Using 0.7.")
        
        count = count_twin_turbo(screenshot_path, confidence)
        print(f"\n🎯 FINAL RESULT: {count} Twin Turbo character(s) found")
        
    else:
        # Interactive mode
        print("=== SMART TWIN TURBO DETECTOR ===")
        print()
        
        screenshot_path = input("Enter path to screenshot: ").strip()
        if not screenshot_path:
            print("No screenshot specified. Exiting.")
            return
        
        try:
            confidence = float(input("Enter confidence threshold (0.0-1.0, default 0.7): ").strip() or "0.7")
        except ValueError:
            confidence = 0.7
        
        count = count_twin_turbo(screenshot_path, confidence)
        print(f"\n🎯 FINAL RESULT: {count} Twin Turbo character(s) found")

if __name__ == "__main__":
    main() 