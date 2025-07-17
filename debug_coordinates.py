#!/usr/bin/env python3
"""
Debug script to show exact coordinate values from macro file
"""

import json

def debug_macro_coordinates():
    """Debug the coordinate values in the macro file"""
    
    file_path = "reroll test.record"
    
    print("=== DEBUGGING MACRO COORDINATES ===")
    print(f"File: {file_path}")
    print()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = json.loads(content)
        
        print("JSON structure:")
        print(f"Keys: {list(data.keys())}")
        print()
        
        operations = data.get('operations', [])
        print(f"Number of operations: {len(operations)}")
        print()
        
        # Look at first few operations
        for i, op in enumerate(operations[:5]):
            print(f"Operation {i+1}:")
            print(f"  Type: {op.get('operationId', 'UNKNOWN')}")
            print(f"  Timing: {op.get('timing', 'N/A')}")
            
            if op.get('operationId') == 'ImeClipboard':
                text = op.get('text', '')
                print(f"  Text preview: {text[:200]}...")
                
                # Try to extract some coordinates from the text
                if 'Parsed' in text and 'actions:' in text:
                    lines = text.split('\r\n')
                    for line in lines[:5]:  # First 5 lines
                        if line.strip() and line[0].isdigit():
                            print(f"    {line.strip()}")
            
            elif op.get('operationId') == 'PutMultiTouch':
                points = op.get('points', [])
                print(f"  Points: {len(points)}")
                for j, point in enumerate(points):
                    x = point.get('x', 0)
                    y = point.get('y', 0)
                    state = point.get('state', 0)
                    print(f"    Point {j+1}: x={x}, y={y}, state={state}")
            
            print()
        
        # Show some coordinate statistics
        print("=== COORDINATE ANALYSIS ===")
        
        # Analyze PutMultiTouch coordinates
        multitouch_coords = []
        for op in operations:
            if op.get('operationId') == 'PutMultiTouch':
                points = op.get('points', [])
                for point in points:
                    x = point.get('x', 0)
                    y = point.get('y', 0)
                    if x > 0 or y > 0:
                        multitouch_coords.append((x, y))
        
        if multitouch_coords:
            x_coords = [coord[0] for coord in multitouch_coords]
            y_coords = [coord[1] for coord in multitouch_coords]
            
            print("PutMultiTouch coordinates:")
            print(f"  X range: {min(x_coords)} to {max(x_coords)}")
            print(f"  Y range: {min(y_coords)} to {max(y_coords)}")
            print(f"  Sample coordinates: {multitouch_coords[:10]}")
        
        # Analyze embedded coordinates
        embedded_coords = []
        for op in operations:
            if op.get('operationId') == 'ImeClipboard':
                text = op.get('text', '')
                if 'Parsed' in text and 'actions:' in text:
                    lines = text.split('\r\n')
                    for line in lines:
                        if line.strip() and line[0].isdigit():
                            # Try to extract coordinates
                            try:
                                colon_pos = line.find(':')
                                if colon_pos != -1:
                                    action_str = line[colon_pos + 1:].strip()
                                    action_str = action_str.replace("'", '"')
                                    action_dict = json.loads(action_str)
                                    
                                    if action_dict.get('type') == 'CLICK':
                                        x = action_dict.get('x', 0)
                                        y = action_dict.get('y', 0)
                                        embedded_coords.append((x, y))
                            except:
                                pass
        
        if embedded_coords:
            x_coords = [coord[0] for coord in embedded_coords]
            y_coords = [coord[1] for coord in embedded_coords]
            
            print("\nEmbedded coordinates:")
            print(f"  X range: {min(x_coords)} to {max(x_coords)}")
            print(f"  Y range: {min(y_coords)} to {max(y_coords)}")
            print(f"  Sample coordinates: {embedded_coords[:10]}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_macro_coordinates() 