#!/usr/bin/env python3
"""
Test script to verify Gacha Reroll Automation installation
"""

import sys
import importlib
import subprocess
import os

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✓ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"✗ {package_name or module_name} - FAILED: {e}")
        return False

def test_command(command, description):
    """Test if a command is available"""
    try:
        result = subprocess.run([command, '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ {description} - OK")
            return True
        else:
            print(f"✗ {description} - FAILED: Command not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        print(f"✗ {description} - FAILED: Command not found or timeout")
        return False

def main():
    print("Gacha Reroll Automation - Installation Test")
    print("=" * 50)
    
    # Test Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro} - OK")
    else:
        print(f"✗ Python {python_version.major}.{python_version.minor}.{python_version.micro} - FAILED: Need Python 3.8+")
        return False
    
    print("\nTesting Python Dependencies:")
    print("-" * 30)
    
    # Test required modules
    modules = [
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('PIL', 'Pillow'),
        ('tkinter', 'Tkinter'),
        ('configparser', 'ConfigParser'),
        ('threading', 'Threading'),
        ('subprocess', 'Subprocess'),
        ('json', 'JSON'),
        ('time', 'Time'),
        ('os', 'OS'),
        ('re', 'Regular Expressions'),
        ('datetime', 'DateTime'),
    ]
    
    all_modules_ok = True
    for module, name in modules:
        if not test_import(module, name):
            all_modules_ok = False
    
    # Test optional modules
    print("\nTesting Optional Dependencies:")
    print("-" * 30)
    
    optional_modules = [
        ('pytesseract', 'Tesseract OCR'),
        ('pyautogui', 'PyAutoGUI'),
    ]
    
    for module, name in optional_modules:
        test_import(module, name)
    
    # Test external commands
    print("\nTesting External Commands:")
    print("-" * 30)
    
    commands = [
        ('adb', 'Android Debug Bridge (ADB)'),
        ('tesseract', 'Tesseract OCR'),
    ]
    
    for command, description in commands:
        test_command(command, description)
    
    # Test file structure
    print("\nTesting File Structure:")
    print("-" * 30)
    
    required_files = [
        'gacha_reroll.py',
        'macro_parser.py',
        'image_recognition.py',
        'requirements.txt',
        'README.md',
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} - OK")
        else:
            print(f"✗ {file} - MISSING")
            all_modules_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_modules_ok:
        print("✓ Installation test PASSED!")
        print("The application should work correctly.")
        print("\nNext steps:")
        print("1. Configure LDPlayer settings")
        print("2. Prepare character images")
        print("3. Create or record a macro")
        print("4. Run: python gacha_reroll.py")
    else:
        print("✗ Installation test FAILED!")
        print("Please fix the issues above before running the application.")
        print("\nCommon solutions:")
        print("1. Install missing Python packages: pip install -r requirements.txt")
        print("2. Install ADB: Download Android SDK Platform Tools")
        print("3. Install Tesseract: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    
    return all_modules_ok

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 