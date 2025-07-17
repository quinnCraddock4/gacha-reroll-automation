#!/usr/bin/env python3
"""
Test script to verify deduplication logic
"""

def test_deduplication():
    """Test the deduplication logic with sample detections"""
    
    # Simulate multiple detections of the same Twin Turbo character
    # These would be the raw detections from the smart character detector
    raw_detections = [
        {'method': 'smart_detection', 'template': 'Twin_Turbo', 'confidence': 0.85, 'location': (100, 150), 'matches': 15},
        {'method': 'smart_detection', 'template': 'Twin_Turbo', 'confidence': 0.82, 'location': (105, 155), 'matches': 14},  # Very close to first
        {'method': 'smart_detection', 'template': 'Twin_Turbo', 'confidence': 0.78, 'location': (110, 160), 'matches': 13},  # Also close
        {'method': 'smart_detection', 'template': 'Twin_Turbo', 'confidence': 0.90, 'location': (300, 200), 'matches': 18},  # Different location
        {'method': 'smart_detection', 'template': 'Twin_Turbo', 'confidence': 0.75, 'location': (305, 205), 'matches': 12},  # Close to the different one
    ]
    
    print("=== TESTING DEDUPLICATION LOGIC ===")
    print(f"Raw detections: {len(raw_detections)}")
    for i, det in enumerate(raw_detections):
        print(f"  {i+1}. {det['location']} (conf: {det['confidence']:.2f}, matches: {det['matches']})")
    
    # Test different deduplication distances
    test_distances = [50, 80, 100, 150]
    
    for dedup_distance in test_distances:
        print(f"\n--- Testing with deduplication distance: {dedup_distance} pixels ---")
        
        # Filter by confidence threshold (0.7)
        filtered_detections = [d for d in raw_detections if d['confidence'] >= 0.7]
        
        # Remove duplicates
        unique_detections = []
        for detection in filtered_detections:
            location = detection['location']
            
            # Check if too close to existing detections
            is_duplicate = False
            for existing in unique_detections:
                existing_location = existing['location']
                distance = ((location[0] - existing_location[0])**2 + 
                           (location[1] - existing_location[1])**2)**0.5
                if distance < dedup_distance:
                    is_duplicate = True
                    print(f"  Removing duplicate at {location} (too close to {existing_location}, distance: {distance:.1f}px)")
                    break
            
            if not is_duplicate:
                unique_detections.append(detection)
        
        print(f"  After deduplication: {len(unique_detections)} unique detections")
        for i, det in enumerate(unique_detections):
            print(f"    {i+1}. {det['location']} (conf: {det['confidence']:.2f}, matches: {det['matches']})")

if __name__ == "__main__":
    test_deduplication() 