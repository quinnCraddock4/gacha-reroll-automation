import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import cv2
import numpy as np
import subprocess
import time
import json
import os
import threading
from PIL import Image, ImageTk
import configparser
import re
from datetime import datetime
from macro_parser import parse_macro_file
from image_recognition import ImageRecognition, detect_characters_in_screenshot

class GachaRerollAutomation:
    def __init__(self, root):
        self.root = root
        self.root.title("Gacha Reroll Automation")
        self.root.geometry("900x700")
        
        # Configuration
        self.config = configparser.ConfigParser()
        self.config_file = "config.ini"
        self.load_config()
        
        # Variables
        self.is_running = False
        self.ldplayer_path = tk.StringVar(value=self.config.get('LDPlayer', 'path', fallback=''))
        self.adb_path = tk.StringVar(value=self.config.get('LDPlayer', 'adb_path', fallback='E:\\LDPlayer\\LDPlayer9\\adb.exe'))
        self.adb_port = tk.StringVar(value=self.config.get('LDPlayer', 'adb_port', fallback='5555'))
        self.target_character = tk.StringVar()
        self.target_count = tk.IntVar(value=1)
        self.character_images = []
        self.current_rerolls = 0
        self.successful_pulls = 0
        
        # Multi-instance support
        self.instance_ports = []  # List of ADB ports for all instances
        self.master_instance_port = tk.StringVar(value='5555')  # Port for macro execution
        self.instance_count = tk.IntVar(value=1)  # Number of instances to monitor
        
        # Create GUI
        self.create_gui()
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config['LDPlayer'] = {
                'path': 'E:\\LDPlayer\\LDPlayer9\\LDPlayer9.exe',
                'adb_path': 'E:\\LDPlayer\\LDPlayer9\\adb.exe',
                'adb_port': '5555'
            }
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def create_gui(self):
        """Create the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # LDPlayer Configuration
        ttk.Label(main_frame, text="LDPlayer Configuration", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="LDPlayer Path:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.ldplayer_path, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        ttk.Button(main_frame, text="Browse", command=self.browse_ldplayer).grid(row=1, column=2, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="ADB Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.adb_path, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        ttk.Button(main_frame, text="Browse", command=self.browse_adb).grid(row=2, column=2, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Master Instance Port:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.master_instance_port, width=10).grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Number of Instances:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(main_frame, from_=1, to=10, textvariable=self.instance_count, width=10).grid(row=4, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Button(main_frame, text="Generate Ports", command=self.generate_instance_ports).grid(row=4, column=2, padx=(5, 0), pady=2)
        
        # Character Configuration
        ttk.Label(main_frame, text="Character Configuration", font=('Arial', 12, 'bold')).grid(row=5, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="Target Character:").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.target_character, width=30).grid(row=6, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Target Count:").grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(main_frame, from_=1, to=10, textvariable=self.target_count, width=10).grid(row=7, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Character Images
        ttk.Label(main_frame, text="Character Images", font=('Arial', 12, 'bold')).grid(row=8, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        image_frame = ttk.Frame(main_frame)
        image_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(image_frame, text="Add Character Image", command=self.add_character_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(image_frame, text="Clear Images", command=self.clear_character_images).pack(side=tk.LEFT)
        
        # Macro Configuration
        ttk.Label(main_frame, text="Macro Configuration", font=('Arial', 12, 'bold')).grid(row=10, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        macro_frame = ttk.Frame(main_frame)
        macro_frame.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.macro_path = tk.StringVar()
        ttk.Entry(macro_frame, textvariable=self.macro_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(macro_frame, text="Browse", command=self.browse_macro).pack(side=tk.LEFT)
        
        # Control Buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=12, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(control_frame, text="Start Reroll", command=self.start_reroll)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Reroll", command=self.stop_reroll, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="Test ADB Connection", command=self.test_adb_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Take Screenshot", command=self.take_screenshot).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Test Macro", command=self.test_macro).pack(side=tk.LEFT)
        
        # Status and Log
        ttk.Label(main_frame, text="Status & Log", font=('Arial', 12, 'bold')).grid(row=13, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=14, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(status_frame, text="Rerolls:").pack(side=tk.LEFT)
        self.reroll_label = ttk.Label(status_frame, text="0")
        self.reroll_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(status_frame, text="Successful Pulls:").pack(side=tk.LEFT)
        self.pull_label = ttk.Label(status_frame, text="0")
        self.pull_label.pack(side=tk.LEFT, padx=(5, 20))
        
        # Log area
        self.log_text = scrolledtext.ScrolledText(main_frame, height=10, width=80)
        self.log_text.grid(row=15, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure main frame row weights
        main_frame.rowconfigure(15, weight=1)
    
    def browse_ldplayer(self):
        """Browse for LDPlayer executable"""
        path = filedialog.askopenfilename(
            title="Select LDPlayer Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.ldplayer_path.set(path)
            self.config['LDPlayer']['path'] = path
            self.save_config()
    
    def browse_adb(self):
        """Browse for ADB executable"""
        path = filedialog.askopenfilename(
            title="Select ADB Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.adb_path.set(path)
            self.config['LDPlayer']['adb_path'] = path
            self.save_config()
    
    def browse_macro(self):
        """Browse for macro file"""
        path = filedialog.askopenfilename(
            title="Select Macro File",
            filetypes=[("Record files", "*.Record"), ("All files", "*.*")],
            initialdir="E:\\LDPlayer\\LDPlayer9\\vms\\operationRecords"
        )
        if path:
            self.macro_path.set(path)
    
    def add_character_image(self):
        """Add character image for recognition"""
        path = filedialog.askopenfilename(
            title="Select Character Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if path:
            self.character_images.append(path)
            self.log(f"Added character image: {os.path.basename(path)}")
    
    def clear_character_images(self):
        """Clear all character images"""
        self.character_images.clear()
        self.log("Cleared all character images")
    
    def generate_instance_ports(self):
        """Generate ADB ports for multiple instances"""
        try:
            count = self.instance_count.get()
            master_port = int(self.master_instance_port.get())
            
            self.instance_ports = []
            for i in range(count):
                if i == 0:
                    # First instance is the master (macro execution)
                    port = master_port
                else:
                    # Additional instances use sequential ports
                    port = master_port + i
                self.instance_ports.append(port)
            
            self.log(f"Generated ports for {count} instances: {self.instance_ports}")
            
        except ValueError as e:
            self.log(f"Error generating ports: {str(e)}")
            messagebox.showerror("Error", "Please enter valid port numbers")
    
    def test_adb_connection(self):
        """Test ADB connection to LDPlayer"""
        try:
            adb_path = self.adb_path.get()
            if not os.path.exists(adb_path):
                self.log(f"ADB not found at: {adb_path}")
                messagebox.showerror("Error", f"ADB not found at: {adb_path}")
                return
            
            result = subprocess.run(
                [adb_path, 'connect', f'127.0.0.1:{self.adb_port.get()}'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.log("ADB connection successful")
                messagebox.showinfo("Success", "ADB connection established!")
            else:
                self.log(f"ADB connection failed: {result.stderr}")
                messagebox.showerror("Error", f"ADB connection failed: {result.stderr}")
        except Exception as e:
            self.log(f"ADB test error: {str(e)}")
            messagebox.showerror("Error", f"ADB test error: {str(e)}")
    
    def take_screenshot(self):
        """Take a screenshot from LDPlayer"""
        try:
            adb_path = self.adb_path.get()
            if not os.path.exists(adb_path):
                self.log(f"ADB not found at: {adb_path}")
                messagebox.showerror("Error", f"ADB not found at: {adb_path}")
                return
            
            # Use ADB to take screenshot
            subprocess.run([adb_path, 'shell', 'screencap', '/sdcard/screenshot.png'], check=True)
            subprocess.run([adb_path, 'pull', '/sdcard/screenshot.png', '.'], check=True)
            
            # Display screenshot
            img = cv2.imread('screenshot.png')
            if img is not None:
                cv2.imshow('Screenshot', img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                self.log("Screenshot taken and displayed")
            else:
                self.log("Failed to load screenshot")
        except Exception as e:
            self.log(f"Screenshot error: {str(e)}")
            messagebox.showerror("Error", f"Screenshot error: {str(e)}")
    
    def test_macro(self):
        """Test macro execution without image recognition"""
        try:
            if not self.macro_path.get():
                messagebox.showerror("Error", "Please select a macro file first")
                return
            
            if not self.instance_ports:
                messagebox.showerror("Error", "Please generate instance ports first")
                return
            
            # Read macro file
            actions = self.read_macro_file(self.macro_path.get())
            if not actions:
                self.log("No actions found in macro file")
                return
            
            self.log(f"Testing macro with {len(actions)} actions...")
            self.log("Starting macro execution in 3 seconds...")
            
            # Start test in separate thread
            self.test_thread = threading.Thread(target=self._run_test_macro, args=(actions,))
            self.test_thread.daemon = True
            self.test_thread.start()
            
        except Exception as e:
            self.log(f"Test macro error: {str(e)}")
            messagebox.showerror("Error", f"Test macro error: {str(e)}")
    
    def _run_test_macro(self, actions):
        """Run macro test in separate thread"""
        try:
            # Wait 3 seconds before starting
            time.sleep(3)
            
            self.log("Executing macro...")
            
            # Execute macro on master instance only
            master_port = self.instance_ports[0]
            
            for i, action in enumerate(actions):
                action_type = action.get('type', '').upper()
                
                if action_type == 'CLICK':
                    x = action['x']
                    y = action['y']
                    self.log(f"Action {i+1}: CLICK at ({x}, {y})")
                    
                    subprocess.run([self.adb_path.get(), '-s', f'127.0.0.1:{master_port}', 'shell', 'input', 'tap', str(x), str(y)])
                    
                    # Apply delay
                    delay = action.get('delay', 100) / 1000.0
                    time.sleep(delay)
                    
                elif action_type == 'WAIT':
                    delay = action['delay'] / 1000.0
                    self.log(f"Action {i+1}: WAIT for {delay:.2f}s")
                    time.sleep(delay)
            
            self.log("Macro test completed!")
            
        except Exception as e:
            self.log(f"Test macro execution error: {str(e)}")
    
    def read_macro_file(self, file_path):
        """Read and parse macro file using enhanced parser"""
        try:
            actions = parse_macro_file(file_path)
            self.log(f"Parsed {len(actions)} actions from macro file")
            return actions
        except Exception as e:
            self.log(f"Error reading macro file: {str(e)}")
            return []
    
    def execute_macro(self, actions):
        """Execute macro actions"""
        try:
            adb_path = self.adb_path.get()
            if not os.path.exists(adb_path):
                self.log(f"ADB not found at: {adb_path}")
                return
            
            for action in actions:
                if not self.is_running:
                    break
                
                action_type = action.get('type', '').upper()
                
                if action_type == 'CLICK':
                    subprocess.run([adb_path, 'shell', 'input', 'tap', str(action['x']), str(action['y'])])
                elif action_type == 'SWIPE':
                    subprocess.run([adb_path, 'shell', 'input', 'swipe', 
                                  str(action['x1']), str(action['y1']), 
                                  str(action['x2']), str(action['y2']), 
                                  str(action.get('duration', 500))])
                elif action_type == 'KEY':
                    subprocess.run([adb_path, 'shell', 'input', 'keyevent', str(action['keycode'])])
                elif action_type == 'WAIT':
                    time.sleep(action['delay'] / 1000.0)
                elif action_type == 'SCREENSHOT':
                    # Take screenshot during macro execution
                    subprocess.run([adb_path, 'shell', 'screencap', '/sdcard/screenshot.png'])
                
                # Apply delay if specified
                if 'delay' in action and action_type != 'WAIT':
                    time.sleep(action['delay'] / 1000.0)
                
        except Exception as e:
            self.log(f"Macro execution error: {str(e)}")
    
    def detect_character(self, screenshot_path):
        """Detect target character in screenshot using enhanced image recognition"""
        try:
            if not self.character_images:
                return False
            
            # Use enhanced image recognition
            detections = detect_characters_in_screenshot(
                screenshot_path, 
                self.character_images, 
                confidence_threshold=0.7
            )
            
            if detections:
                # Log all detections
                for detection in detections:
                    self.log(f"Detection: {detection['template']} ({detection['method']}) - Confidence: {detection['confidence']:.2f}")
                
                # Return True if any detection meets threshold
                return any(d['confidence'] >= 0.7 for d in detections)
            
            return False
        except Exception as e:
            self.log(f"Character detection error: {str(e)}")
            return False
    
    def start_reroll(self):
        """Start the reroll automation process"""
        if not self.ldplayer_path.get():
            messagebox.showerror("Error", "Please set LDPlayer path")
            return
        
        if not self.macro_path.get():
            messagebox.showerror("Error", "Please select a macro file")
            return
        
        if not self.character_images:
            messagebox.showerror("Error", "Please add at least one character image")
            return
        
        if not self.target_character.get():
            messagebox.showerror("Error", "Please enter target character name")
            return
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Start reroll in separate thread
        self.reroll_thread = threading.Thread(target=self.reroll_loop)
        self.reroll_thread.daemon = True
        self.reroll_thread.start()
    
    def stop_reroll(self):
        """Stop the reroll automation process"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("Reroll stopped by user")
    
    def reroll_loop(self):
        """Main reroll loop"""
        try:
            # Read macro file
            actions = self.read_macro_file(self.macro_path.get())
            if not actions:
                self.log("No actions found in macro file")
                return
            
            while self.is_running and self.successful_pulls < self.target_count.get():
                self.log(f"Starting reroll #{self.current_rerolls + 1}")
                
                # Execute macro
                self.execute_macro(actions)
                
                # Wait for animation to complete
                time.sleep(3)
                
                # Take screenshot and detect character
                try:
                    adb_path = self.adb_path.get()
                    subprocess.run([adb_path, 'shell', 'screencap', '/sdcard/screenshot.png'], check=True)
                    subprocess.run([adb_path, 'pull', '/sdcard/screenshot.png', '.'], check=True)
                    
                    if self.detect_character('screenshot.png'):
                        self.successful_pulls += 1
                        self.log(f"SUCCESS! Found {self.target_character.get()}! ({self.successful_pulls}/{self.target_count.get()})")
                        
                        if self.successful_pulls >= self.target_count.get():
                            self.log("Target count reached! Stopping automation.")
                            break
                    else:
                        self.log("Target character not found, continuing...")
                
                except Exception as e:
                    self.log(f"Screenshot/detection error: {str(e)}")
                
                self.current_rerolls += 1
                
                # Update GUI
                self.root.after(0, self.update_status)
                
                # Small delay between rerolls
                time.sleep(1)
            
            if self.successful_pulls >= self.target_count.get():
                self.log(f"SUCCESS! Completed {self.successful_pulls} pulls in {self.current_rerolls} rerolls!")
                messagebox.showinfo("Success", f"Target reached! {self.successful_pulls} pulls in {self.current_rerolls} rerolls!")
            
        except Exception as e:
            self.log(f"Reroll loop error: {str(e)}")
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
    
    def update_status(self):
        """Update status labels"""
        self.reroll_label.config(text=str(self.current_rerolls))
        self.pull_label.config(text=str(self.successful_pulls))
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        print(log_message.strip())

def main():
    root = tk.Tk()
    app = GachaRerollAutomation(root)
    root.mainloop()

if __name__ == "__main__":
    main() 