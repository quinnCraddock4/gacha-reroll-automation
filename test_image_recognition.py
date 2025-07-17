#!/usr/bin/env python3
"""
Test Image Recognition Script
Counts how many times a character appears in a screenshot
"""

import cv2
import numpy as np
import os
import sys
from image_recognition import detect_characters_in_screenshot

def test_character_detection(character_image_path, screenshot_path, confidence_threshold=0.7):
    """
    Test character detection in a screenshot
    
    Args:
        character_image_path: Path to the character image to search for
        screenshot_path: Path to the screenshot to search in
        confidence_threshold: Minimum confidence for detection (0.0 to 1.0)
    
    Returns:
        List of detections with coordinates and confidence
    """
    
    print(f"=== Testing Character Detection ===")
    print(f"Character image: {character_image_path}")
    print(f"Screenshot: {screenshot_path}")
    print(f"Confidence threshold: {confidence_threshold}")
    print()
    
    # Check if files exist
    if not os.path.exists(character_image_path):
        print(f"ERROR: Character image not found: {character_image_path}")
        return []
    
    if not os.path.exists(screenshot_path):
        print(f"ERROR: Screenshot not found: {screenshot_path}")
        return []
    
    try:
        # Use the existing image recognition function
        detections = detect_characters_in_screenshot(
            screenshot_path, 
            [character_image_path], 
            confidence_threshold=confidence_threshold
        )
        
        print(f"Found {len(detections)} detection(s):")
        print()
        
        for i, detection in enumerate(detections):
            print(f"Detection {i+1}:")
            print(f"  Method: {detection['method']}")
            print(f"  Confidence: {detection['confidence']:.3f}")
            print(f"  Location: {detection['location']}")
            
            # Show additional info if available
            if 'matches' in detection:
                print(f"  Matches: {detection['matches']}")
            if 'area' in detection:
                print(f"  Area: {detection['area']}")
            if 'text_found' in detection:
                print(f"  Text: {detection['text_found']}")
            print()
        
        # Show visual detection results
        if detections:
            show_detection_visualization(screenshot_path, detections)
        
        return detections
        
    except Exception as e:
        print(f"ERROR during detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def show_detection_visualization(screenshot_path, detections):
    """
    Display the screenshot with detection points marked
    
    Args:
        screenshot_path: Path to the screenshot
        detections: List of detection results
    """
    try:
        # Load the screenshot
        screenshot = cv2.imread(screenshot_path)
        if screenshot is None:
            print(f"ERROR: Could not load screenshot: {screenshot_path}")
            return
        
        # Create a copy for drawing
        debug_img = screenshot.copy()
        
        # Define colors for different methods
        colors = {
            'template_matching': (0, 255, 0),    # Green
            'feature_matching': (255, 0, 0),     # Blue
            'color_detection': (0, 0, 255),      # Red
            'ocr': (255, 255, 0)                 # Cyan
        }
        
        print(f"\n=== VISUAL DETECTION RESULTS ===")
        print(f"Showing {len(detections)} detection(s) on screenshot...")
        print("Press any key to close the image window")
        print()
        
        for i, detection in enumerate(detections):
            location = detection['location']
            confidence = detection['confidence']
            method = detection['method']
            template = detection['template']
            
            # Get color for this method
            color = colors.get(method, (255, 255, 255))  # White for unknown methods
            
            # Draw circle at detection point
            cv2.circle(debug_img, location, 30, color, 3)
            
            # Draw number label
            cv2.circle(debug_img, location, 10, color, -1)  # Filled circle
            cv2.putText(debug_img, str(i+1), (location[0] - 5, location[1] + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Draw text label with info
            label = f"{os.path.basename(template)} ({confidence:.2f})"
            text_pos = (location[0] + 40, location[1])
            cv2.putText(debug_img, label, text_pos, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            print(f"Detection {i+1}: {os.path.basename(template)} at {location} (confidence: {confidence:.3f})")
        
        # Add legend
        legend_y = 30
        for method, color in colors.items():
            cv2.putText(debug_img, f"{method}: ", (10, legend_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            legend_y += 20
        
        # Resize image if it's too large for screen
        height, width = debug_img.shape[:2]
        max_width = 1200
        max_height = 800
        
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            debug_img = cv2.resize(debug_img, (new_width, new_height))
        
        # Show the image
        cv2.imshow('Character Detection Results', debug_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"ERROR showing visualization: {str(e)}")
        import traceback
        traceback.print_exc()

def test_multiple_characters(character_images, screenshot_path, confidence_threshold=0.7):
    """
    Test detection of multiple character types in a screenshot
    
    Args:
        character_images: List of character image paths
        screenshot_path: Path to the screenshot
        confidence_threshold: Minimum confidence for detection
    """
    
    print(f"=== Testing Multiple Character Detection ===")
    print(f"Screenshot: {screenshot_path}")
    print(f"Character images: {len(character_images)}")
    print(f"Confidence threshold: {confidence_threshold}")
    print()
    
    try:
        # Use the existing image recognition function
        detections = detect_characters_in_screenshot(
            screenshot_path, 
            character_images, 
            confidence_threshold=confidence_threshold
        )
        
        # Group detections by character
        character_counts = {}
        for detection in detections:
            template_name = os.path.basename(detection['template'])
            if template_name not in character_counts:
                character_counts[template_name] = 0
            character_counts[template_name] += 1
        
        print("Detection Summary:")
        print(f"Total detections: {len(detections)}")
        print()
        
        for character, count in character_counts.items():
            print(f"{character}: {count} appearance(s)")
        
        print()
        print("Detailed detections:")
        for i, detection in enumerate(detections):
            template_name = os.path.basename(detection['template'])
            print(f"  {i+1}. {template_name} - Confidence: {detection['confidence']:.3f} at {detection['location']}")
        
        # Show visual detection results
        if detections:
            show_detection_visualization(screenshot_path, detections)
        
        return detections
        
    except Exception as e:
        print(f"ERROR during detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def interactive_test():
    """Interactive test mode"""
    print("=== Interactive Image Recognition Test ===")
    print()
    
    # Get character image
    character_path = input("Enter path to character image: ").strip()
    if not character_path:
        print("No character image specified. Exiting.")
        return
    
    # Get screenshot
    screenshot_path = input("Enter path to screenshot: ").strip()
    if not screenshot_path:
        print("No screenshot specified. Exiting.")
        return
    
    # Get confidence threshold
    try:
        confidence = float(input("Enter confidence threshold (0.0-1.0, default 0.7): ").strip() or "0.7")
        if confidence < 0 or confidence > 1:
            print("Invalid confidence threshold. Using 0.7.")
            confidence = 0.7
    except ValueError:
        print("Invalid confidence threshold. Using 0.7.")
        confidence = 0.7
    
    print()
    
    # Run test
    detections = test_character_detection(character_path, screenshot_path, confidence)
    
    if detections:
        print(f"✅ SUCCESS: Found {len(detections)} character appearance(s)")
    else:
        print("❌ No characters detected")
        # Show the screenshot even if no detections found
        show_detection_visualization(screenshot_path, [])

def batch_test():
    """Batch test mode - test multiple screenshots"""
    print("=== Batch Image Recognition Test ===")
    print()
    
    # Get character image
    character_path = input("Enter path to character image: ").strip()
    if not character_path:
        print("No character image specified. Exiting.")
        return
    
    # Get screenshot directory
    screenshot_dir = input("Enter directory containing screenshots: ").strip()
    if not screenshot_dir or not os.path.exists(screenshot_dir):
        print("Invalid screenshot directory. Exiting.")
        return
    
    # Get confidence threshold
    try:
        confidence = float(input("Enter confidence threshold (0.0-1.0, default 0.7): ").strip() or "0.7")
        if confidence < 0 or confidence > 1:
            print("Invalid confidence threshold. Using 0.7.")
            confidence = 0.7
    except ValueError:
        print("Invalid confidence threshold. Using 0.7.")
        confidence = 0.7
    
    print()
    
    # Find all image files
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    screenshot_files = []
    
    for file in os.listdir(screenshot_dir):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            screenshot_files.append(os.path.join(screenshot_dir, file))
    
    if not screenshot_files:
        print("No image files found in directory.")
        return
    
    print(f"Found {len(screenshot_files)} screenshot(s) to test")
    print()
    
    # Test each screenshot
    total_detections = 0
    for i, screenshot_path in enumerate(screenshot_files):
        print(f"Testing screenshot {i+1}/{len(screenshot_files)}: {os.path.basename(screenshot_path)}")
        
        detections = test_character_detection(character_path, screenshot_path, confidence)
        
        if detections:
            print(f"  ✅ Found {len(detections)} character(s)")
            total_detections += len(detections)
        else:
            print(f"  ❌ No characters found")
        
        print()
    
    print(f"=== BATCH TEST COMPLETE ===")
    print(f"Total screenshots tested: {len(screenshot_files)}")
    print(f"Total character detections: {total_detections}")

def main():
    """Main function"""
    print("Image Recognition Test Tool")
    print("=" * 40)
    print()
    
    if len(sys.argv) > 1:
        # Command line mode
        if len(sys.argv) >= 3:
            character_path = sys.argv[1]
            screenshot_path = sys.argv[2]
            confidence = 0.7
            
            if len(sys.argv) > 3:
                try:
                    confidence = float(sys.argv[3])
                except ValueError:
                    print("Invalid confidence threshold. Using 0.7.")
            
            test_character_detection(character_path, screenshot_path, confidence)
        else:
            print("Usage: python test_image_recognition.py <character_image> <screenshot> [confidence]")
            print("Example: python test_image_recognition.py character.png screenshot.png 0.7")
    else:
        # Interactive mode
        print("Choose test mode:")
        print("1. Single test (one character, one screenshot)")
        print("2. Batch test (one character, multiple screenshots)")
        print("3. Multiple characters test")
        print()
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            interactive_test()
        elif choice == "2":
            batch_test()
        elif choice == "3":
            # Multiple characters test - now uses characters folder by default
            characters_dir = "characters"
            if os.path.exists(characters_dir):
                character_images = []
                for file in os.listdir(characters_dir):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                        character_images.append(os.path.join(characters_dir, file))
                
                if character_images:
                    print(f"Found {len(character_images)} character images in '{characters_dir}' folder:")
                    for img in character_images:
                        print(f"  - {os.path.basename(img)}")
                    print()
                else:
                    print(f"No image files found in '{characters_dir}' folder")
                    character_images = []
            else:
                print(f"Characters folder '{characters_dir}' not found")
                character_images = []
            
            # Fallback to manual input if no images found
            if not character_images:
                print("Enter character image paths manually (one per line, empty line to finish):")
                while True:
                    path = input().strip()
                    if not path:
                        break
                    character_images.append(path)
            
            if not character_images:
                print("No character images specified.")
                return
            
            screenshot_path = input("Enter path to screenshot: ").strip()
            if not screenshot_path:
                print("No screenshot specified.")
                return
            
            try:
                confidence = float(input("Enter confidence threshold (0.0-1.0, default 0.7): ").strip() or "0.7")
            except ValueError:
                confidence = 0.7
            
            test_multiple_characters(character_images, screenshot_path, confidence)
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main() 