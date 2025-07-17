#!/usr/bin/env python3
"""
Test different coordinate conversion methods
"""

def test_conversions():
    """Test different coordinate conversion methods"""
    
    # Sample coordinates from the macro file
    test_coords = [
        (11175, 8895),   # Sample from macro
        (12510, 9870),   # Sample from macro
        (15060, 5760),   # Sample from macro
        (360, 640),      # Center of 720x1280 screen
    ]
    
    print("=== TESTING COORDINATE CONVERSIONS ===")
    print("Original coordinates from macro file:")
    for x, y in test_coords:
        print(f"  ({x}, {y})")
    print()
    
    # Method 1: Assume coordinates are in 1920x1080 and convert to 720x1280
    print("Method 1: 1920x1080 -> 720x1280")
    for x, y in test_coords:
        x_scaled = int(x * 720 / 1920)
        y_scaled = int(y * 1280 / 1080)
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    print()
    
    # Method 2: Assume coordinates are in 1440x2560 and convert to 720x1280
    print("Method 2: 1440x2560 -> 720x1280")
    for x, y in test_coords:
        x_scaled = int(x * 720 / 1440)
        y_scaled = int(y * 1280 / 2560)
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    print()
    
    # Method 3: Assume coordinates are in 2160x3840 and convert to 720x1280
    print("Method 3: 2160x3840 -> 720x1280")
    for x, y in test_coords:
        x_scaled = int(x * 720 / 2160)
        y_scaled = int(y * 1280 / 3840)
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    print()
    
    # Method 4: Assume coordinates are in 2880x5120 and convert to 720x1280
    print("Method 4: 2880x5120 -> 720x1280")
    for x, y in test_coords:
        x_scaled = int(x * 720 / 2880)
        y_scaled = int(y * 1280 / 5120)
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    print()
    
    # Method 5: Assume coordinates are in 3600x6400 and convert to 720x1280
    print("Method 5: 3600x6400 -> 720x1280")
    for x, y in test_coords:
        x_scaled = int(x * 720 / 3600)
        y_scaled = int(y * 1280 / 6400)
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    print()
    
    # Method 6: Assume coordinates are in 7200x12800 and convert to 720x1280
    print("Method 6: 7200x12800 -> 720x1280")
    for x, y in test_coords:
        x_scaled = int(x * 720 / 7200)
        y_scaled = int(y * 1280 / 12800)
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    print()
    
    # Method 7: Assume coordinates are in 14400x25600 and convert to 720x1280
    print("Method 7: 14400x25600 -> 720x1280")
    for x, y in test_coords:
        x_scaled = int(x * 720 / 14400)
        y_scaled = int(y * 1280 / 25600)
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    print()
    
    print("=== INSTRUCTIONS ===")
    print("1. Look at the converted coordinates above")
    print("2. The center of your screen should be around (360, 640) for 720x1280")
    print("3. Tell me which method gives reasonable coordinates")
    print("4. Or tell me your actual LDPlayer screen resolution")

if __name__ == "__main__":
    test_conversions() 