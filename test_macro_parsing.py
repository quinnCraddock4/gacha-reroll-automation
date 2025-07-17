#!/usr/bin/env python3
"""
Test script to debug macro parsing
"""

from macro_parser import parse_macro_file

def test_macro_parsing():
    """Test macro parsing with the reroll test.record file"""
    
    # Test with the reroll test.record file
    file_path = "reroll test.record"
    
    print(f"Testing macro parsing with file: {file_path}")
    print("=" * 50)
    
    try:
        actions = parse_macro_file(file_path)
        
        print(f"Parsed {len(actions)} actions")
        print()
        
        # Show first 10 actions with coordinate information
        print("First 10 actions:")
        for i, action in enumerate(actions[:10]):
            action_type = action.get('type', 'UNKNOWN')
            print(f"  {i+1}: {action_type}")
            
            if action_type == 'CLICK':
                x = action.get('x', 0)
                y = action.get('y', 0)
                delay = action.get('delay', 0)
                print(f"    Coordinates: ({x}, {y})")
                print(f"    Delay: {delay}ms")
            elif action_type == 'WAIT':
                delay = action.get('delay', 0)
                print(f"    Delay: {delay}ms")
            elif action_type == 'KEY':
                keycode = action.get('keycode', 0)
                print(f"    Keycode: {keycode}")
            
            print()
        
        # Show coordinate statistics
        if actions:
            click_actions = [a for a in actions if a.get('type') == 'CLICK']
            if click_actions:
                x_coords = [a.get('x', 0) for a in click_actions]
                y_coords = [a.get('y', 0) for a in click_actions]
                
                print("Coordinate Statistics:")
                print(f"  X range: {min(x_coords)} to {max(x_coords)}")
                print(f"  Y range: {min(y_coords)} to {max(y_coords)}")
                print(f"  Average X: {sum(x_coords) / len(x_coords):.1f}")
                print(f"  Average Y: {sum(y_coords) / len(y_coords):.1f}")
        
    except Exception as e:
        print(f"Error testing macro parsing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_macro_parsing() 