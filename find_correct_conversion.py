#!/usr/bin/env python3
"""
Find the correct coordinate conversion ratio
"""

def test_conversion_ratio(source_width, source_height, target_width=720, target_height=1280):
    """Test a specific conversion ratio"""
    test_coords = [
        (11175, 8895),
        (12510, 9870), 
        (15060, 5760),
        (14190, 7860),
        (13545, 10095)
    ]
    
    print(f"Testing {source_width}x{source_height} -> {target_width}x{target_height}")
    results = []
    
    for x, y in test_coords:
        x_scaled = int(x * target_width / source_width)
        y_scaled = int(y * target_height / source_height)
        x_scaled = max(0, min(x_scaled, target_width - 1))
        y_scaled = max(0, min(y_scaled, target_height - 1))
        results.append((x_scaled, y_scaled))
        print(f"  ({x}, {y}) -> ({x_scaled}, {y_scaled})")
    
    # Check if results are reasonable
    x_coords = [r[0] for r in results]
    y_coords = [r[1] for r in results]
    
    print(f"  X range: {min(x_coords)}-{max(x_coords)}")
    print(f"  Y range: {min(y_coords)}-{max(y_coords)}")
    
    # Check if center is reasonable (should be around 360, 640)
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)
    print(f"  Average: ({center_x:.0f}, {center_y:.0f})")
    print()

# Test various possible source resolutions
print("=== TESTING DIFFERENT CONVERSION RATIOS ===")
print()

# Test common ratios
test_conversion_ratio(18000, 12800)  # 25x width, 10x height
test_conversion_ratio(21600, 15360)  # 30x width, 12x height
test_conversion_ratio(14400, 10240)  # 20x width, 8x height
test_conversion_ratio(28800, 20480)  # 40x width, 16x height
test_conversion_ratio(36000, 25600)  # 50x width, 20x height

# Test some other possibilities
test_conversion_ratio(19200, 13653)  # Based on max X=17925
test_conversion_ratio(21333, 15111)  # Based on max Y=10650

print("=== INSTRUCTIONS ===")
print("1. Look at the converted coordinates above")
print("2. The center of your screen should be around (360, 640)")
print("3. Coordinates should be spread across the screen, not all clustered")
print("4. Tell me which conversion ratio looks most reasonable")
print("5. Or tell me what the actual source resolution should be") 