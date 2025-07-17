#!/usr/bin/env python3
"""
Create Character Image Tool
Extract character images from screenshots to improve detection accuracy
"""

import cv2
import numpy as np
import os
import sys

def extract_character_region(screenshot_path, output_path=None):
    """Extract a character region from a screenshot using mouse selection"""
    
    print("=== CHARACTER IMAGE EXTRACTOR ===")
    print("Instructions:")
    print("1. The screenshot will open in a window")
    print("2. Click and drag to select the character region")
    print("3. Press 'Enter' to confirm selection")
    print("4. Press 'R' to reset selection")
    print("5. Press 'Q' to quit")
    print()
    
    # Load the screenshot
    image = cv2.imread(screenshot_path)
    if image is None:
        print(f"ERROR: Could not load screenshot: {screenshot_path}")
        return None
    
    # Create a copy for drawing
    display_image = image.copy()
    
    # Variables for selection
    drawing = False
    start_point = None
    end_point = None
    selection_made = False
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, start_point, end_point, display_image
        
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_point = (x, y)
            end_point = (x, y)
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                end_point = (x, y)
                # Redraw the image with current selection
                display_image = image.copy()
                cv2.rectangle(display_image, start_point, end_point, (0, 255, 0), 2)
        
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            end_point = (x, y)
            # Final rectangle
            display_image = image.copy()
            cv2.rectangle(display_image, start_point, end_point, (0, 255, 0), 2)
    
    # Create window and set mouse callback
    window_name = "Select Character Region"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    print("Opening screenshot for selection...")
    
    while True:
        cv2.imshow(window_name, display_image)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("Quitting...")
            break
        elif key == ord('r'):
            # Reset selection
            start_point = None
            end_point = None
            display_image = image.copy()
            print("Selection reset")
        elif key == 13:  # Enter key
            if start_point and end_point:
                # Confirm selection
                x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
                x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
                
                # Extract the region
                character_region = image[y1:y2, x1:x2]
                
                if output_path is None:
                    output_path = f"character_{os.path.basename(screenshot_path)}"
                
                # Save the extracted region
                cv2.imwrite(output_path, character_region)
                print(f"✅ Character image saved to: {output_path}")
                print(f"   Region: ({x1}, {y1}) to ({x2}, {y2})")
                print(f"   Size: {x2-x1} x {y2-y1} pixels")
                
                selection_made = True
                break
            else:
                print("Please select a region first")
    
    cv2.destroyAllWindows()
    
    if selection_made:
        return output_path
    else:
        return None

def create_character_variants(character_image_path, output_dir="character_variants"):
    """Create different variants of a character image for better detection"""
    
    print("=== CREATING CHARACTER VARIANTS ===")
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load the character image
    image = cv2.imread(character_image_path)
    if image is None:
        print(f"ERROR: Could not load character image: {character_image_path}")
        return []
    
    base_name = os.path.splitext(os.path.basename(character_image_path))[0]
    variants = []
    
    # Original image
    original_path = os.path.join(output_dir, f"{base_name}_original.png")
    cv2.imwrite(original_path, image)
    variants.append(original_path)
    print(f"✅ Original: {original_path}")
    
    # Different scales
    scales = [0.8, 0.9, 1.1, 1.2]
    for scale in scales:
        height, width = image.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        scaled = cv2.resize(image, (new_width, new_height))
        scaled_path = os.path.join(output_dir, f"{base_name}_scale_{scale:.1f}.png")
        cv2.imwrite(scaled_path, scaled)
        variants.append(scaled_path)
        print(f"✅ Scale {scale}: {scaled_path}")
    
    # Different brightness levels
    brightness_levels = [0.8, 0.9, 1.1, 1.2]
    for level in brightness_levels:
        brightened = cv2.convertScaleAbs(image, alpha=level, beta=0)
        bright_path = os.path.join(output_dir, f"{base_name}_bright_{level:.1f}.png")
        cv2.imwrite(bright_path, brightened)
        variants.append(bright_path)
        print(f"✅ Brightness {level}: {bright_path}")
    
    # Grayscale version
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    gray_path = os.path.join(output_dir, f"{base_name}_grayscale.png")
    cv2.imwrite(gray_path, gray_bgr)
    variants.append(gray_path)
    print(f"✅ Grayscale: {gray_path}")
    
    # Blurred version (for more flexible matching)
    blurred = cv2.GaussianBlur(image, (3, 3), 0)
    blur_path = os.path.join(output_dir, f"{base_name}_blurred.png")
    cv2.imwrite(blur_path, blurred)
    variants.append(blur_path)
    print(f"✅ Blurred: {blur_path}")
    
    print(f"\n✅ Created {len(variants)} character variants in '{output_dir}' directory")
    return variants

def main():
    """Main function"""
    print("Character Image Creation Tool")
    print("=" * 35)
    print()
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "extract":
            if len(sys.argv) >= 3:
                screenshot_path = sys.argv[2]
                output_path = sys.argv[3] if len(sys.argv) > 3 else None
                extract_character_region(screenshot_path, output_path)
            else:
                print("Usage: python create_character_image.py extract <screenshot> [output_path]")
        
        elif sys.argv[1] == "variants":
            if len(sys.argv) >= 3:
                character_path = sys.argv[2]
                output_dir = sys.argv[3] if len(sys.argv) > 3 else "character_variants"
                create_character_variants(character_path, output_dir)
            else:
                print("Usage: python create_character_image.py variants <character_image> [output_dir]")
        
        else:
            print("Unknown command. Use 'extract' or 'variants'")
    else:
        # Interactive mode
        print("Choose action:")
        print("1. Extract character region from screenshot")
        print("2. Create character image variants")
        print()
        
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == "1":
            screenshot_path = input("Enter path to screenshot: ").strip()
            output_path = input("Enter output path (optional): ").strip()
            if not output_path:
                output_path = None
            
            if screenshot_path:
                extract_character_region(screenshot_path, output_path)
        
        elif choice == "2":
            character_path = input("Enter path to character image: ").strip()
            output_dir = input("Enter output directory (default: character_variants): ").strip()
            if not output_dir:
                output_dir = "character_variants"
            
            if character_path:
                create_character_variants(character_path, output_dir)
        
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main() 