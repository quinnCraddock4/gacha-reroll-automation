#!/usr/bin/env python3
"""
Fine-tune Character Detection
Test different confidence thresholds and parameters to improve accuracy
"""

import cv2
import numpy as np
import os
import sys
from image_recognition import detect_characters_in_screenshot

def test_confidence_thresholds(character_image_path=None, screenshot_path=None):
    """Test different confidence thresholds to find the optimal setting"""
    
    print("=== TESTING CONFIDENCE THRESHOLDS ===")
    
    # Use characters folder if no specific image provided
    if character_image_path is None:
        characters_dir = "characters"
        if os.path.exists(characters_dir):
            character_images = []
            for file in os.listdir(characters_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    character_images.append(os.path.join(characters_dir, file))
            
            if character_images:
                print(f"Using {len(character_images)} character images from '{characters_dir}' folder")
                character_image_path = character_images  # Pass as list
            else:
                print(f"No image files found in '{characters_dir}' folder")
                return []
        else:
            print(f"Characters folder '{characters_dir}' not found")
            return []
    else:
        print(f"Character: {os.path.basename(character_image_path)}")
    
    if screenshot_path:
        print(f"Screenshot: {os.path.basename(screenshot_path)}")
    print()
    
    # Test different confidence thresholds
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
    
    results = []
    for threshold in thresholds:
        print(f"Testing confidence threshold: {threshold}")
        
        try:
            detections = detect_characters_in_screenshot(
                screenshot_path, 
                character_image_path, 
                confidence_threshold=threshold
            )
            
            print(f"  Found {len(detections)} detection(s)")
            
            # Show details of each detection
            for i, detection in enumerate(detections):
                confidence = detection['confidence']
                method = detection['method']
                location = detection['location']
                print(f"    Detection {i+1}: {method} - Confidence: {confidence:.3f} at {location}")
            
            results.append({
                'threshold': threshold,
                'detections': detections,
                'count': len(detections)
            })
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'threshold': threshold,
                'detections': [],
                'count': 0
            })
        
        print()
    
    # Find optimal threshold
    print("=== RECOMMENDATIONS ===")
    
    # Find threshold with exactly 1 detection (assuming you want 1 character)
    single_detections = [r for r in results if r['count'] == 1]
    if single_detections:
        best = max(single_detections, key=lambda x: x['detections'][0]['confidence'] if x['detections'] else 0)
        print(f"✅ RECOMMENDED: Use confidence threshold {best['threshold']}")
        print(f"   This gives exactly 1 detection with confidence {best['detections'][0]['confidence']:.3f}")
    else:
        # Find threshold with highest confidence single detection
        all_detections = []
        for r in results:
            for d in r['detections']:
                all_detections.append((r['threshold'], d))
        
        if all_detections:
            best_threshold, best_detection = max(all_detections, key=lambda x: x[1]['confidence'])
            print(f"✅ RECOMMENDED: Use confidence threshold {best_threshold}")
            print(f"   Best detection has confidence {best_detection['confidence']:.3f}")
        else:
            print("❌ No detections found at any threshold")
    
    return results

def test_region_constraints(character_image_path=None, screenshot_path=None, confidence_threshold=0.8):
    """Test detection in specific regions of the screenshot"""
    
    print("=== TESTING REGION CONSTRAINTS ===")
    print("This will help identify where characters typically appear")
    print()
    
    # Use characters folder if no specific image provided
    if character_image_path is None:
        characters_dir = "characters"
        if os.path.exists(characters_dir):
            character_images = []
            for file in os.listdir(characters_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    character_images.append(os.path.join(characters_dir, file))
            
            if character_images:
                print(f"Using {len(character_images)} character images from '{characters_dir}' folder")
                character_image_path = character_images  # Pass as list
            else:
                print(f"No image files found in '{characters_dir}' folder")
                return
        else:
            print(f"Characters folder '{characters_dir}' not found")
            return
    
    try:
        # Load screenshot to get dimensions
        screenshot = cv2.imread(screenshot_path)
        if screenshot is None:
            print("ERROR: Could not load screenshot")
            return
        
        height, width = screenshot.shape[:2]
        print(f"Screenshot dimensions: {width} x {height}")
        print()
        
        # Define common regions where characters might appear
        regions = {
            'Top-left': (0, 0, width//2, height//2),
            'Top-right': (width//2, 0, width, height//2),
            'Bottom-left': (0, height//2, width//2, height),
            'Bottom-right': (width//2, height//2, width, height),
            'Center': (width//4, height//4, 3*width//4, 3*height//4),
            'Top-third': (0, 0, width, height//3),
            'Middle-third': (0, height//3, width, 2*height//3),
            'Bottom-third': (0, 2*height//3, width, height)
        }
        
        for region_name, (x1, y1, x2, y2) in regions.items():
            print(f"Testing region: {region_name} ({x1},{y1}) to ({x2},{y2})")
            
            # Crop the screenshot to this region
            cropped = screenshot[y1:y2, x1:x2]
            
            # Save cropped region temporarily
            temp_path = f"temp_region_{region_name.lower().replace('-', '_')}.png"
            cv2.imwrite(temp_path, cropped)
            
            try:
                detections = detect_characters_in_screenshot(
                    temp_path, 
                    character_image_path, 
                    confidence_threshold=confidence_threshold
                )
                
                if detections:
                    print(f"  ✅ Found {len(detections)} detection(s) in this region")
                    for i, detection in enumerate(detections):
                        # Adjust coordinates back to original image
                        orig_x = detection['location'][0] + x1
                        orig_y = detection['location'][1] + y1
                        print(f"    Detection {i+1}: Confidence {detection['confidence']:.3f} at ({orig_x}, {orig_y})")
                else:
                    print(f"  ❌ No detections in this region")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            print()
        
    except Exception as e:
        print(f"ERROR: {str(e)}")

def compare_character_images(character_images, screenshot_path, confidence_threshold=0.8):
    """Compare different character images to see which works best"""
    
    print("=== COMPARING CHARACTER IMAGES ===")
    print(f"Testing {len(character_images)} character images")
    print()
    
    results = []
    for i, char_image in enumerate(character_images):
        print(f"Testing character image {i+1}: {os.path.basename(char_image)}")
        
        try:
            detections = detect_characters_in_screenshot(
                screenshot_path, 
                [char_image], 
                confidence_threshold=confidence_threshold
            )
            
            print(f"  Found {len(detections)} detection(s)")
            
            for j, detection in enumerate(detections):
                confidence = detection['confidence']
                method = detection['method']
                location = detection['location']
                print(f"    Detection {j+1}: {method} - Confidence: {confidence:.3f} at {location}")
            
            results.append({
                'image': char_image,
                'detections': detections,
                'count': len(detections),
                'best_confidence': max([d['confidence'] for d in detections]) if detections else 0
            })
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'image': char_image,
                'detections': [],
                'count': 0,
                'best_confidence': 0
            })
        
        print()
    
    # Find best character image
    if results:
        best_result = max(results, key=lambda x: x['best_confidence'])
        print("=== BEST CHARACTER IMAGE ===")
        print(f"✅ RECOMMENDED: {os.path.basename(best_result['image'])}")
        print(f"   Best confidence: {best_result['best_confidence']:.3f}")
        print(f"   Detections: {best_result['count']}")
    
    return results

def main():
    """Main function"""
    print("Fine-tune Character Detection Tool")
    print("=" * 40)
    print()
    
    if len(sys.argv) > 1:
        # Command line mode
        if len(sys.argv) >= 2:
            screenshot_path = sys.argv[1]
            character_path = sys.argv[2] if len(sys.argv) > 2 else None
            
            print("Choose test type:")
            print("1. Test confidence thresholds")
            print("2. Test region constraints")
            print("3. Both")
            print()
            
            choice = input("Enter choice (1-3): ").strip()
            
            if choice == "1":
                test_confidence_thresholds(character_path, screenshot_path)
            elif choice == "2":
                confidence = float(input("Enter confidence threshold (default 0.8): ").strip() or "0.8")
                test_region_constraints(character_path, screenshot_path, confidence)
            elif choice == "3":
                test_confidence_thresholds(character_path, screenshot_path)
                print("\n" + "="*50 + "\n")
                confidence = float(input("Enter confidence threshold for region test (default 0.8): ").strip() or "0.8")
                test_region_constraints(character_path, screenshot_path, confidence)
            else:
                print("Invalid choice")
        else:
            print("Usage: python fine_tune_detection.py <screenshot> [character_image]")
            print("If no character_image is provided, will use all images from 'characters' folder")
    else:
        # Interactive mode
        print("Choose test type:")
        print("1. Test confidence thresholds")
        print("2. Test region constraints")
        print("3. Compare multiple character images")
        print()
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            screenshot_path = input("Enter path to screenshot: ").strip()
            character_path = input("Enter path to character image (or empty to use characters folder): ").strip()
            if not character_path:
                character_path = None
            if screenshot_path:
                test_confidence_thresholds(character_path, screenshot_path)
        
        elif choice == "2":
            screenshot_path = input("Enter path to screenshot: ").strip()
            character_path = input("Enter path to character image (or empty to use characters folder): ").strip()
            if not character_path:
                character_path = None
            confidence = float(input("Enter confidence threshold (default 0.8): ").strip() or "0.8")
            if screenshot_path:
                test_region_constraints(character_path, screenshot_path, confidence)
        
        elif choice == "3":
            print("Enter character image paths (one per line, empty line to finish):")
            character_images = []
            while True:
                path = input().strip()
                if not path:
                    break
                character_images.append(path)
            
            if character_images:
                screenshot_path = input("Enter path to screenshot: ").strip()
                confidence = float(input("Enter confidence threshold (default 0.8): ").strip() or "0.8")
                if screenshot_path:
                    compare_character_images(character_images, screenshot_path, confidence)
        
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main() 