#!/usr/bin/env python3
"""
Quick test to show converted coordinates
"""

def scale_coordinates(x, y, source_width=21600, source_height=15360, target_width=720, target_height=1280):
    """Scale coordinates from high-resolution coordinate system to LDPlayer screen resolution"""
    x_scaled = int(x * target_width / source_width)
    y_scaled = int(y * target_height / source_height)
    x_scaled = max(0, min(x_scaled, target_width - 1))
    y_scaled = max(0, min(y_scaled, target_height - 1))
    return x_scaled, y_scaled

# Test with sample coordinates from your macro
test_coords = [
    (11175, 8895),
    (12510, 9870), 
    (15060, 5760),
    (14190, 7860),
    (13545, 10095)
]

print("=== COORDINATE CONVERSION TEST ===")
print("Converting from 21600x15360 to 720x1280")
print()

for x, y in test_coords:
    x_scaled, y_scaled = scale_coordinates(x, y)
    print(f"({x}, {y}) -> ({x_scaled}, {y_scaled})")

print()
print("Center of 720x1280 screen should be around (360, 640)")
print("Do these coordinates look reasonable?") 