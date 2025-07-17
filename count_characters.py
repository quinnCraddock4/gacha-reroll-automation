#!/usr/bin/env python3
"""
Simple Character Counter
Counts how many Twin Turbo characters appear on screen using all images from characters folder
"""

import cv2
import os
import sys
from image_recognition import detect_characters_in_screenshot

def count_characters(screenshot_path, confidence_threshold=0.7):
    """
    Count Twin Turbo characters on screen
    
    Args:
        screenshot_path: Path to screenshot
        confidence_threshold: Detection confidence (0.0-1.0)
    
    Returns:
        Number of characters found
    """
    
    print(f"=== TWIN TURBO CHARACTER COUNTER ===")
    print(f"Screenshot: {os.path.basename(screenshot_path)}")
    print(f"Confidence threshold: {confidence_threshold}")
    print()
    
    # Check if screenshot exists
    if not os.path.exists(screenshot_path):
        print(f"ERROR: Screenshot not found: {screenshot_path}")
        return 0
    
    # Check if characters folder exists
    characters_dir = "characters"
    if not os.path.exists(characters_dir):
        print(f"ERROR: Characters folder '{characters_dir}' not found")
        return 0
    
    # Get all character images from the folder
    character_images = []
    for file in os.listdir(characters_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            character_images.append(os.path.join(characters_dir, file))
    
    if not character_images:
        print(f"ERROR: No image files found in '{characters_dir}' folder")
        return 0
    
    print(f"Using {len(character_images)} character images:")
    for img in character_images:
        print(f"  - {os.path.basename(img)}")
    print()
    
    try:
        # Detect characters using all images from the folder
        detections = detect_characters_in_screenshot(
            screenshot_path, 
            None,  # This will use characters folder automatically
            confidence_threshold=confidence_threshold
        )
        
        # Count unique detections (avoid counting same character multiple times)
        unique_detections = []
        for detection in detections:
            location = detection['location']
            confidence = detection['confidence']
            
            # Check if this detection is too close to existing ones
            is_duplicate = False
            for existing in unique_detections:
                existing_location = existing['location']
                distance = ((location[0] - existing_location[0])**2 + 
                           (location[1] - existing_location[1])**2)**0.5
                if distance < 50:  # If within 50 pixels, consider it duplicate
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_detections.append(detection)
        
        # Display results
        print(f"=== RESULTS ===")
        print(f"Total detections: {len(detections)}")
        print(f"Unique characters: {len(unique_detections)}")
        print()
        
        if unique_detections:
            print("Character locations:")
            for i, detection in enumerate(unique_detections):
                location = detection['location']
                confidence = detection['confidence']
                method = detection['method']
                template = detection['template']
                print(f"  {i+1}. {os.path.basename(template)} at {location} (confidence: {confidence:.3f}, method: {method})")
            
            # Show visual results
            show_visual_results(screenshot_path, unique_detections)
        else:
            print("❌ No Twin Turbo characters detected")
        
        return len(unique_detections)
        
    except Exception as e:
        print(f"ERROR during detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0

def show_visual_results(screenshot_path, detections):
    """Show screenshot with detection markers"""
    try:
        # Load screenshot
        screenshot = cv2.imread(screenshot_path)
        if screenshot is None:
            print("Could not load screenshot for visualization")
            return
        
        # Create copy for drawing
        debug_img = screenshot.copy()
        
        # Draw detection markers
        for i, detection in enumerate(detections):
            location = detection['location']
            confidence = detection['confidence']
            template = detection['template']
            
            # Draw circle
            cv2.circle(debug_img, location, 30, (0, 255, 0), 3)
            
            # Draw number
            cv2.circle(debug_img, location, 10, (0, 255, 0), -1)
            cv2.putText(debug_img, str(i+1), (location[0] - 5, location[1] + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Draw label
            label = f"{os.path.basename(template)} ({confidence:.2f})"
            cv2.putText(debug_img, label, (location[0] + 40, location[1]), 
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
        
        # Show image
        print("\nShowing detection results (press any key to close)...")
        cv2.imshow('Twin Turbo Detections', debug_img)
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
        
        count = count_characters(screenshot_path, confidence)
        print(f"\n🎯 FINAL RESULT: {count} Twin Turbo character(s) found")
        
    else:
        # Interactive mode
        print("=== TWIN TURBO CHARACTER COUNTER ===")
        print()
        
        screenshot_path = input("Enter path to screenshot: ").strip()
        if not screenshot_path:
            print("No screenshot specified. Exiting.")
            return
        
        try:
            confidence = float(input("Enter confidence threshold (0.0-1.0, default 0.7): ").strip() or "0.7")
        except ValueError:
            confidence = 0.7
        
        count = count_characters(screenshot_path, confidence)
        print(f"\n🎯 FINAL RESULT: {count} Twin Turbo character(s) found")

if __name__ == "__main__":
    main() 