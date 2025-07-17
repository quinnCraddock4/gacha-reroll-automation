import json
import re
import os

def parse_macro_file(file_path):
    """
    Enhanced parser for LDPlayer .Record files
    Handles PutMultiTouch operations and coordinate scaling
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Macro file content (first 500 chars): {content[:500]}")
        
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            print(f"Parsed JSON data type: {type(data)}")
            if isinstance(data, list):
                print(f"JSON array length: {len(data)}")
                if len(data) > 0:
                    print(f"First item: {data[0]}")
            elif isinstance(data, dict):
                print(f"JSON dict keys: {list(data.keys())}")
            return parse_json_macro(data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            # If not JSON, try parsing as text format
            return parse_text_macro(content)
            
    except Exception as e:
        print(f"Error parsing macro file: {str(e)}")
        return []

def parse_json_macro(data):
    """Parse JSON format LDPlayer macro"""
    actions = []
    
    try:
        # Handle different JSON structures
        if isinstance(data, dict):
            # Check if it's a macro file with operations array
            if 'operations' in data:
                operations = data['operations']
                if isinstance(operations, list):
                    for operation in operations:
                        actions.extend(parse_operation(operation))
                else:
                    actions.extend(parse_operation(operations))
            else:
                # Single operation
                actions.extend(parse_operation(data))
        elif isinstance(data, list):
            # Multiple operations
            for operation in data:
                actions.extend(parse_operation(operation))
        
        return actions
    except Exception as e:
        print(f"Error parsing JSON macro: {str(e)}")
        return []

def parse_operation(operation):
    """Parse a single operation from JSON"""
    actions = []
    
    try:
        op_type = operation.get('operationId', '').lower()
        
        if op_type == 'imclipboard':
            # Handle special case where actions are embedded in text
            text = operation.get('text', '')
            if text and 'Parsed' in text and 'actions:' in text:
                actions.extend(parse_embedded_actions(text))
        elif op_type == 'putmultitouch':
            # Handle PutMultiTouch operation
            actions.extend(parse_putmultitouch(operation))
        elif op_type == 'putkey':
            # Handle key press
            keycode = operation.get('keycode', 0)
            actions.append({
                'type': 'KEY',
                'keycode': keycode,
                'delay': operation.get('delay', 100)
            })
        elif op_type == 'puttext':
            # Handle text input
            text = operation.get('text', '')
            actions.append({
                'type': 'TEXT',
                'text': text,
                'delay': operation.get('delay', 100)
            })
        elif op_type == 'putwheel':
            # Handle scroll/wheel
            x = operation.get('x', 0)
            y = operation.get('y', 0)
            direction = operation.get('direction', 0)
            actions.append({
                'type': 'WHEEL',
                'x': x,
                'y': y,
                'direction': direction,
                'delay': operation.get('delay', 100)
            })
        elif op_type == 'puttouch':
            # Handle single touch
            x = operation.get('x', 0)
            y = operation.get('y', 0)
            # Convert to screen coordinates (assuming they're in 1920x1080 format)
            x_scaled, y_scaled = scale_coordinates(x, y, 1920, 1080, 720, 1280)
            actions.append({
                'type': 'CLICK',
                'x': x_scaled,
                'y': y_scaled,
                'delay': operation.get('delay', 100)
            })
        
        # Add wait operation if specified
        if 'wait' in operation:
            actions.append({
                'type': 'WAIT',
                'delay': operation['wait']
            })
            
    except Exception as e:
        print(f"Error parsing operation: {str(e)}")
    
    return actions

def parse_embedded_actions(text):
    """Parse actions embedded in text string"""
    actions = []
    
    try:
        # Extract the actions part from the text
        # Format: "Parsed 118 actions:\r\n  1: {'type': 'CLICK', 'x': 181, 'y': 94, 'delay': 1395}\r\n  2: ..."
        lines = text.split('\r\n')
        
        for line in lines:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue
            
            # Extract the action dictionary part
            # Format: "1: {'type': 'CLICK', 'x': 181, 'y': 94, 'delay': 1395}"
            colon_pos = line.find(':')
            if colon_pos == -1:
                continue
            
            action_str = line[colon_pos + 1:].strip()
            
            # Parse the action dictionary
            try:
                # Convert single quotes to double quotes for JSON parsing
                action_str = action_str.replace("'", '"')
                action_dict = json.loads(action_str)
                
                # Create action
                action_type = action_dict.get('type', '').upper()
                if action_type == 'CLICK':
                    x = action_dict.get('x', 0)
                    y = action_dict.get('y', 0)
                    # The embedded coordinates appear to be in a different scale
                    # Convert them to screen coordinates (assuming they're in 1920x1080 format)
                    x_scaled, y_scaled = scale_coordinates(x, y, 1920, 1080, 720, 1280)
                    print(f"Embedded CLICK: Original ({x}, {y}) -> Screen ({x_scaled}, {y_scaled})")
                    actions.append({
                        'type': 'CLICK',
                        'x': x_scaled,
                        'y': y_scaled,
                        'delay': action_dict.get('delay', 100)
                    })
                elif action_type == 'WAIT':
                    actions.append({
                        'type': 'WAIT',
                        'delay': action_dict.get('delay', 100)
                    })
                elif action_type == 'KEY':
                    actions.append({
                        'type': 'KEY',
                        'keycode': action_dict.get('keycode', 0),
                        'delay': action_dict.get('delay', 100)
                    })
                elif action_type == 'TEXT':
                    actions.append({
                        'type': 'TEXT',
                        'text': action_dict.get('text', ''),
                        'delay': action_dict.get('delay', 100)
                    })
                
            except json.JSONDecodeError as e:
                print(f"Error parsing action string: {action_str} - {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error parsing embedded actions: {str(e)}")
    
    return actions

def parse_putmultitouch(operation):
    """Parse PutMultiTouch operation"""
    actions = []
    
    try:
        # Get touch points
        points = operation.get('points', [])
        
        if len(points) == 1:
            # Single touch - treat as click
            point = points[0]
            x = point.get('x', 0)
            y = point.get('y', 0)
            # Convert from LDPlayer virtual coordinates to actual screen coordinates
            x_scaled, y_scaled = scale_coordinates(x, y)
            print(f"PutMultiTouch CLICK: Virtual ({x}, {y}) -> Screen ({x_scaled}, {y_scaled})")
            actions.append({
                'type': 'CLICK',
                'x': x_scaled,
                'y': y_scaled,
                'delay': operation.get('delay', 100)
            })
        elif len(points) == 2:
            # Two touch points - treat as swipe
            point1 = points[0]
            point2 = points[1]
            x1 = point1.get('x', 0)
            y1 = point1.get('y', 0)
            x2 = point2.get('x', 0)
            y2 = point2.get('y', 0)
            # Convert from LDPlayer virtual coordinates to actual screen coordinates
            x1_scaled, y1_scaled = scale_coordinates(x1, y1)
            x2_scaled, y2_scaled = scale_coordinates(x2, y2)
            actions.append({
                'type': 'SWIPE',
                'x1': x1_scaled,
                'y1': y1_scaled,
                'x2': x2_scaled,
                'y2': y2_scaled,
                'duration': operation.get('duration', 500),
                'delay': operation.get('delay', 100)
            })
        
    except Exception as e:
        print(f"Error parsing PutMultiTouch: {str(e)}")
    
    return actions

def parse_text_macro(content):
    """Parse text format macro (fallback)"""
    actions = []
    
    try:
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to match different patterns
            # Click pattern: x,y
            click_match = re.match(r'(\d+),(\d+)', line)
            if click_match:
                x = int(click_match.group(1))
                y = int(click_match.group(2))
                actions.append({
                    'type': 'CLICK',
                    'x': x,
                    'y': y,
                    'delay': 100
                })
                continue
            
            # Wait pattern: wait:ms
            wait_match = re.match(r'wait:(\d+)', line)
            if wait_match:
                delay = int(wait_match.group(1))
                actions.append({
                    'type': 'WAIT',
                    'delay': delay
                })
                continue
            
            # Key pattern: key:keycode
            key_match = re.match(r'key:(\d+)', line)
            if key_match:
                keycode = int(key_match.group(1))
                actions.append({
                    'type': 'KEY',
                    'keycode': keycode,
                    'delay': 100
                })
                continue
                
    except Exception as e:
        print(f"Error parsing text macro: {str(e)}")
    
    return actions

def scale_coordinates(x, y, source_width=21600, source_height=15360, target_width=720, target_height=1280):
    """Scale coordinates from high-resolution coordinate system to LDPlayer screen resolution"""
    # Convert from high-resolution coordinates to LDPlayer screen resolution (720x1280)
    x_scaled = int(x * target_width / source_width)
    y_scaled = int(y * target_height / source_height)
    
    # Ensure coordinates are within screen bounds
    x_scaled = max(0, min(x_scaled, target_width - 1))
    y_scaled = max(0, min(y_scaled, target_height - 1))
    
    return x_scaled, y_scaled 