#!/usr/bin/env python3
"""
Simple Reroll Monitor
- Press F2 to start monitoring
- Takes screenshots when instances reach roll screen
- Uses image recognition to detect desired characters
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import time
import os
import threading
from datetime import datetime
import configparser
from smart_character_detection import SmartCharacterDetector
import pyautogui
import cv2
import hashlib

class SimpleRerollMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Reroll Monitor")
        self.root.geometry("800x600")
        
        # Configuration
        self.config = configparser.ConfigParser()
        self.config_file = "config.ini"
        self.load_config()
        
        # Variables
        self.is_monitoring = False
        self.adb_path = tk.StringVar(value=self.config.get('LDPlayer', 'adb_path', fallback='E:\\LDPlayer\\LDPlayer9\\adb.exe'))
        self.instance_ports = []
        self.instance_count = tk.IntVar(value=1)
        self.target_character = tk.StringVar(value="Kita Black")
        self.screenshot_timings = []  # List of seconds when to take screenshots
        self.monitoring_duration = tk.IntVar(value=233)  # seconds (3:53)
        self.cycle_duration = tk.IntVar(value=4)  # seconds
        self.auto_repeat = tk.BooleanVar(value=True)  # Auto repeat cycles
        self.target_pulls = tk.IntVar(value=4)  # Number of successful pulls to stop
        self.reset_counts = tk.BooleanVar(value=True)  # Reset counts after each cycle
        self.auto_discover_on_start = tk.BooleanVar(value=True)  # Auto discover instances on startup
        self.deduplication_distance = tk.IntVar(value=150)  # Distance threshold for deduplication (pixels)
        self.auto_close_instances = tk.BooleanVar(value=True)  # Auto close instances when they reach target
        self.ldplayer_console_path = tk.StringVar(value='E:\\LDPlayer\\LDPlayer9\\ldconsole.exe')  # LDPlayer console path
        
        # Smart character detector
        self.character_detector = None
        self.detector_initialized = False
        self.confidence_threshold = 0.85  # Increased from 0.7 to 0.85
        
        # Track closed instances
        self.closed_instances = set()  # Set of instance IDs that have been closed
        
        # Track duplicate screenshots
        self.instance_last_screenshots = {}  # {instance_id: last_screenshot_hash}
        self.ignored_instances = set()  # Set of instance IDs to ignore due to duplicates
        
        # Statistics
        self.current_cycles = 0
        self.successful_pulls = 0
        self.instance_pulls = {}  # Track pulls per instance: {instance_id: count}
        
        # Create saved images folder
        self.saved_images_folder = "saved_images"
        
        # Create GUI
        self.create_gui()
        
        # Create saved images folder after GUI is ready
        if not os.path.exists(self.saved_images_folder):
            os.makedirs(self.saved_images_folder)
            self.log(f"Created saved images folder: {self.saved_images_folder}")
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config['LDPlayer'] = {
                'adb_path': 'E:\\LDPlayer\\LDPlayer9\\adb.exe',
                'ldconsole_path': 'E:\\LDPlayer\\LDPlayer9\\ldconsole.exe'
            }
            self.save_config()
        
        # Load LDPlayer console path from config
        if 'LDPlayer' in self.config and 'ldconsole_path' in self.config['LDPlayer']:
            self.ldplayer_console_path.set(self.config['LDPlayer']['ldconsole_path'])
    
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
        
        # ADB Configuration
        ttk.Label(main_frame, text="ADB Configuration", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="ADB Path:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.adb_path, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        ttk.Button(main_frame, text="Browse", command=self.browse_adb).grid(row=1, column=2, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Number of Instances:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(main_frame, from_=1, to=10, textvariable=self.instance_count, width=10).grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Button(main_frame, text="Generate Ports", command=self.generate_instance_ports).grid(row=2, column=2, padx=(5, 0), pady=2)
        ttk.Button(main_frame, text="Auto Discover", command=self.auto_discover_instances).grid(row=2, column=3, padx=(5, 0), pady=2)
        
        # Monitoring Configuration
        ttk.Label(main_frame, text="Monitoring Configuration", font=('Arial', 12, 'bold')).grid(row=3, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="Monitoring Duration (seconds):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(main_frame, from_=10, to=300, textvariable=self.monitoring_duration, width=10).grid(row=4, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Cycle Duration (seconds):").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(main_frame, from_=60, to=600, textvariable=self.cycle_duration, width=10).grid(row=5, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Target Successful Pulls:").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(main_frame, from_=1, to=10, textvariable=self.target_pulls, width=10).grid(row=6, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Checkbutton(main_frame, text="Auto Repeat Cycles", variable=self.auto_repeat).grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Checkbutton(main_frame, text="Reset Counts After Each Cycle", variable=self.reset_counts).grid(row=8, column=0, columnspan=2, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Checkbutton(main_frame, text="Auto Discover Instances on Startup", variable=self.auto_discover_on_start).grid(row=9, column=0, columnspan=2, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Checkbutton(main_frame, text="Auto Close Instances When Target Reached", variable=self.auto_close_instances).grid(row=10, column=0, columnspan=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="LDPlayer Console Path:").grid(row=11, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.ldplayer_console_path, width=50).grid(row=11, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        ttk.Button(main_frame, text="Browse", command=self.browse_ldconsole).grid(row=11, column=2, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Deduplication Distance (pixels):").grid(row=12, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(main_frame, from_=20, to=200, textvariable=self.deduplication_distance, width=10).grid(row=12, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        ttk.Label(main_frame, text="(Removes duplicate detections within this distance)", font=('Arial', 8)).grid(row=12, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Screenshot Timings
        ttk.Label(main_frame, text="Screenshot Timings", font=('Arial', 12, 'bold')).grid(row=13, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        timing_frame = ttk.Frame(main_frame)
        timing_frame.grid(row=14, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.timing_entry = tk.StringVar(value="142, 155, 167, 180, 195, 207, 221")  # Default screenshot timings (2:22, 2:35, 2:47, 3:00, 3:15, 3:27, 3:41)
        ttk.Label(timing_frame, text="Screenshot times (seconds, comma-separated):").pack(side=tk.LEFT)
        ttk.Entry(timing_frame, textvariable=self.timing_entry, width=30).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(timing_frame, text="Add Timing", command=self.add_timing).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(timing_frame, text="Clear Timings", command=self.clear_timings).pack(side=tk.LEFT, padx=(5, 0))
        
        # Timing list
        self.timing_listbox = tk.Listbox(main_frame, height=4)
        self.timing_listbox.grid(row=15, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Load default timings
        self.load_default_timings()
        
        # Character Configuration
        ttk.Label(main_frame, text="Character Configuration", font=('Arial', 12, 'bold')).grid(row=16, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="Target Character:").grid(row=17, column=0, sticky=tk.W, pady=2)
        ttk.Entry(main_frame, textvariable=self.target_character, width=30).grid(row=17, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Smart Detection Info
        ttk.Label(main_frame, text="Smart Detection", font=('Arial', 12, 'bold')).grid(row=18, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=19, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(info_frame, text="Using smart detection with all images from 'characters' folder").pack(side=tk.LEFT)
        ttk.Button(info_frame, text="Initialize Detector", command=self.initialize_detector).pack(side=tk.LEFT, padx=(10, 0))
        
        # Control Buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=20, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="Test ADB Connection", command=self.test_adb_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Take Test Screenshot", command=self.take_test_screenshot).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Test LDConsole", command=self.test_ldconsole).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Open Saved Images", command=self.open_saved_images_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Debug ADB", command=self.debug_adb).pack(side=tk.LEFT)
        
        # Status and Log
        ttk.Label(main_frame, text="Status & Log", font=('Arial', 12, 'bold')).grid(row=21, column=0, columnspan=3, pady=(20, 10), sticky=tk.W)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=22, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(status_frame, text="Cycles:").pack(side=tk.LEFT)
        self.cycle_label = ttk.Label(status_frame, text="0")
        self.cycle_label.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(status_frame, text="Total Pulls:").pack(side=tk.LEFT)
        self.pull_label = ttk.Label(status_frame, text="0")
        self.pull_label.pack(side=tk.LEFT, padx=(5, 20))
        
        # Instance status frame
        self.instance_status_frame = ttk.Frame(main_frame)
        self.instance_status_frame.grid(row=23, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.instance_status_frame, text="Per-Instance Pulls:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # Instance labels will be created dynamically
        self.instance_labels = {}
        
        # Log area
        self.log_text = scrolledtext.ScrolledText(main_frame, height=10, width=80)
        self.log_text.grid(row=24, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure main frame row weights
        main_frame.rowconfigure(24, weight=1)
        
        # Bind Page Down key to trigger macro in LDPlayer
        self.root.bind('<Next>', lambda event: self.trigger_macro())
        
        # Auto discover instances on startup if enabled
        if self.auto_discover_on_start.get():
            self.root.after(1000, self.auto_discover_instances)  # Delay 1 second after startup
    
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
    
    def browse_ldconsole(self):
        """Browse for LDPlayer console executable"""
        path = filedialog.askopenfilename(
            title="Select LDPlayer Console Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
            initialdir="E:\\LDPlayer\\LDPlayer9"
        )
        if path:
            self.ldplayer_console_path.set(path)
            self.config['LDPlayer']['ldconsole_path'] = path
            self.save_config()
    
    def generate_instance_ports(self):
        """Generate ADB ports for instances"""
        count = self.instance_count.get()
        self.instance_ports = [5555 + i for i in range(count)]
        self.log(f"Generated {count} instance ports: {self.instance_ports}")
        
        # Initialize instance tracking
        self.instance_pulls = {i+1: 0 for i in range(count)}
        self.create_instance_labels()
    
    def auto_discover_instances(self):
        """Automatically discover and connect to all available LDPlayer instances"""
        try:
            adb_path = self.adb_path.get()
            if not os.path.exists(adb_path):
                messagebox.showerror("Error", f"ADB not found at: {adb_path}")
                return
            
            self.log("🔍 Auto-discovering LDPlayer instances...")
            
            # First, try to get list of devices from ADB
            try:
                self.log("Checking ADB devices...")
                result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log(f"ADB devices output: {result.stdout}")
                else:
                    self.log(f"ADB devices error: {result.stderr}")
            except Exception as e:
                self.log(f"Error running 'adb devices': {str(e)}")
            
            # Common LDPlayer ADB ports (5555-5564 for instances 1-10)
            possible_ports = list(range(5555, 5565))
            discovered_ports = []
            
            # Test each port with multiple methods
            for port in possible_ports:
                try:
                    self.log(f"Testing port {port}...")
                    
                    # Method 1: Try shell command
                    try:
                        result = subprocess.run(
                            [adb_path, '-s', f'127.0.0.1:{port}', 'shell', 'echo', 'test'], 
                            capture_output=True, text=True, timeout=5
                        )
                        
                        if result.returncode == 0:
                            discovered_ports.append(port)
                            self.log(f"✅ Found instance on port {port} (method 1)")
                            continue
                        else:
                            self.log(f"❌ Port {port} failed shell test: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        self.log(f"⏱️ Timeout on port {port} (method 1)")
                    except Exception as e:
                        self.log(f"❌ Error testing port {port} (method 1): {str(e)}")
                    
                    # Method 2: Try getprop command
                    try:
                        result = subprocess.run(
                            [adb_path, '-s', f'127.0.0.1:{port}', 'shell', 'getprop', 'ro.product.model'], 
                            capture_output=True, text=True, timeout=5
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            discovered_ports.append(port)
                            self.log(f"✅ Found instance on port {port} (method 2): {result.stdout.strip()}")
                            continue
                    except subprocess.TimeoutExpired:
                        self.log(f"⏱️ Timeout on port {port} (method 2)")
                    except Exception as e:
                        self.log(f"❌ Error testing port {port} (method 2): {str(e)}")
                    
                    # Method 3: Try connect command
                    try:
                        result = subprocess.run(
                            [adb_path, 'connect', f'127.0.0.1:{port}'], 
                            capture_output=True, text=True, timeout=5
                        )
                        
                        if result.returncode == 0 and "connected" in result.stdout.lower():
                            discovered_ports.append(port)
                            self.log(f"✅ Found instance on port {port} (method 3)")
                            continue
                    except subprocess.TimeoutExpired:
                        self.log(f"⏱️ Timeout on port {port} (method 3)")
                    except Exception as e:
                        self.log(f"❌ Error testing port {port} (method 3): {str(e)}")
                        
                except Exception as e:
                    self.log(f"❌ General error testing port {port}: {str(e)}")
            
            if discovered_ports:
                self.instance_ports = discovered_ports
                self.instance_count.set(len(discovered_ports))
                
                # Initialize instance tracking
                self.instance_pulls = {i+1: 0 for i in range(len(discovered_ports))}
                self.create_instance_labels()
                
                self.log(f"🎉 Auto-discovery complete! Found {len(discovered_ports)} instances:")
                for i, port in enumerate(discovered_ports):
                    self.log(f"  Instance {i+1}: 127.0.0.1:{port}")
                
                # Test connections
                self.test_adb_connection()
                
            else:
                self.log("❌ No LDPlayer instances found")
                self.log("Troubleshooting tips:")
                self.log("1. Make sure LDPlayer is running")
                self.log("2. Make sure at least one instance is started")
                self.log("3. Check if ADB is enabled in LDPlayer settings")
                self.log("4. Try restarting LDPlayer")
                self.log("5. Check if your ADB path is correct")
                messagebox.showwarning("No Instances", 
                    "No LDPlayer instances were discovered.\n\n"
                    "Troubleshooting:\n"
                    "• Make sure LDPlayer is running\n"
                    "• Make sure at least one instance is started\n"
                    "• Check if ADB is enabled in LDPlayer settings\n"
                    "• Try restarting LDPlayer\n"
                    "• Check if your ADB path is correct")
                
        except Exception as e:
            self.log(f"Error during auto-discovery: {str(e)}")
            messagebox.showerror("Error", f"Auto-discovery failed: {str(e)}")
    
    def create_instance_labels(self):
        """Create labels for each instance"""
        # Clear existing labels
        for widget in self.instance_status_frame.winfo_children():
            if widget != self.instance_status_frame.winfo_children()[0]:  # Keep the "Per-Instance Pulls:" label
                widget.destroy()
        
        self.instance_labels = {}
        
        # Create labels for each instance
        for instance_id in self.instance_pulls.keys():
            label = ttk.Label(self.instance_status_frame, text=f"Instance {instance_id}: 0")
            label.pack(side=tk.LEFT, padx=(10, 5))
            self.instance_labels[instance_id] = label
    
    def load_default_timings(self):
        """Load default screenshot timings"""
        default_timings = [142, 155, 167, 180, 195, 207, 221]  # Custom screenshot timings (2:22, 2:35, 2:47, 3:00, 3:15, 3:27, 3:41)
        self.screenshot_timings = default_timings.copy()
        self.update_timing_listbox()
    
    def add_timing(self):
        """Add timing from entry field"""
        try:
            timing_str = self.timing_entry.get().strip()
            if not timing_str:
                return
            
            # Parse comma-separated values
            timings = [int(t.strip()) for t in timing_str.split(',') if t.strip()]
            
            for timing in timings:
                if timing not in self.screenshot_timings and timing > 0:
                    self.screenshot_timings.append(timing)
            
            # Sort timings
            self.screenshot_timings.sort()
            self.update_timing_listbox()
            
            # Clear entry
            self.timing_entry.set("")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers separated by commas")
    
    def clear_timings(self):
        """Clear all timings"""
        self.screenshot_timings.clear()
        self.update_timing_listbox()
    
    def update_timing_listbox(self):
        """Update the timing listbox display"""
        self.timing_listbox.delete(0, tk.END)
        for timing in self.screenshot_timings:
            minutes = timing // 60
            seconds = timing % 60
            if minutes > 0:
                display_text = f"{minutes}m {seconds}s ({timing}s)"
            else:
                display_text = f"{seconds}s ({timing}s)"
            self.timing_listbox.insert(tk.END, display_text)
    
    def add_character_image(self):
        """Add character image for recognition"""
        path = filedialog.askopenfilename(
            title="Select Character Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if path:
            self.character_images.append(path)
            self.log(f"Added character image: {os.path.basename(path)}")
    
    def initialize_detector(self):
        """Initialize the smart character detector"""
        try:
            self.log("Initializing smart character detector...")
            self.character_detector = SmartCharacterDetector(confidence_threshold=self.confidence_threshold)
            
            if self.character_detector.learn_character():
                self.detector_initialized = True
                self.log("✅ Smart character detector initialized successfully!")
                self.log(f"Ready to detect Twin Turbo characters using all images from 'characters' folder (confidence threshold: {self.confidence_threshold})")
            else:
                self.log("❌ Failed to initialize character detector")
                self.detector_initialized = False
                
        except Exception as e:
            self.log(f"Error initializing detector: {str(e)}")
            self.detector_initialized = False
    
    def test_adb_connection(self):
        """Test ADB connection to instances"""
        if not self.instance_ports:
            messagebox.showerror("Error", "Please generate instance ports first")
            return
        
        adb_path = self.adb_path.get()
        if not os.path.exists(adb_path):
            messagebox.showerror("Error", f"ADB not found at: {adb_path}")
            return
        
        self.log("Testing ADB connections...")
        
        for i, port in enumerate(self.instance_ports):
            try:
                result = subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', 'shell', 'echo', 'test'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log(f"Instance {i+1} (port {port}): Connected")
                else:
                    self.log(f"Instance {i+1} (port {port}): Failed to connect")
            except Exception as e:
                self.log(f"Instance {i+1} (port {port}): Error - {str(e)}")
    
    def debug_adb(self):
        """Debug ADB connection and show detailed information"""
        try:
            adb_path = self.adb_path.get()
            if not os.path.exists(adb_path):
                messagebox.showerror("Error", f"ADB not found at: {adb_path}")
                return
            
            self.log("🔧 Debugging ADB connection...")
            self.log(f"ADB path: {adb_path}")
            
            # Test basic ADB
            try:
                self.log("Testing basic ADB...")
                result = subprocess.run([adb_path, 'version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log(f"✅ ADB version: {result.stdout.strip()}")
                else:
                    self.log(f"❌ ADB version failed: {result.stderr}")
            except Exception as e:
                self.log(f"❌ ADB version error: {str(e)}")
            
            # Test ADB devices
            try:
                self.log("Testing 'adb devices'...")
                result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log(f"✅ ADB devices output:")
                    self.log(result.stdout)
                else:
                    self.log(f"❌ ADB devices failed: {result.stderr}")
            except Exception as e:
                self.log(f"❌ ADB devices error: {str(e)}")
            
            # Test ADB kill-server and start-server
            try:
                self.log("Restarting ADB server...")
                subprocess.run([adb_path, 'kill-server'], capture_output=True, timeout=5)
                time.sleep(1)
                subprocess.run([adb_path, 'start-server'], capture_output=True, timeout=5)
                time.sleep(2)
                self.log("✅ ADB server restarted")
            except Exception as e:
                self.log(f"❌ ADB server restart error: {str(e)}")
            
            # Test specific LDPlayer ports
            self.log("Testing common LDPlayer ports...")
            for port in [5555, 5556, 5557, 5558, 5559, 5560]:
                try:
                    result = subprocess.run([adb_path, 'connect', f'127.0.0.1:{port}'], 
                                          capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        self.log(f"Port {port}: {result.stdout.strip()}")
                    else:
                        self.log(f"Port {port}: {result.stderr.strip()}")
                except Exception as e:
                    self.log(f"Port {port}: Error - {str(e)}")
            
            # Final devices check
            try:
                self.log("Final ADB devices check...")
                result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log(f"Final devices:")
                    self.log(result.stdout)
                else:
                    self.log(f"Final devices failed: {result.stderr}")
            except Exception as e:
                self.log(f"Final devices error: {str(e)}")
            
            self.log("🔧 ADB debug complete")
            
        except Exception as e:
            self.log(f"Debug error: {str(e)}")
    
    def take_test_screenshot(self):
        """Take a test screenshot from first instance"""
        if not self.instance_ports:
            messagebox.showerror("Error", "Please generate instance ports first")
            return
        
        adb_path = self.adb_path.get()
        if not os.path.exists(adb_path):
            messagebox.showerror("Error", f"ADB not found at: {adb_path}")
            return
        
        try:
            port = self.instance_ports[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_screenshot_{timestamp}.png"
            
            self.log(f"Taking test screenshot from instance 1 (port {port})...")
            
            # Take screenshot
            subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', 'shell', 'screencap', '/sdcard/screenshot.png'], check=True)
            
            # Pull screenshot
            subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', 'pull', '/sdcard/screenshot.png', filename], check=True)
            
            self.log(f"Test screenshot saved as: {filename}")
            
        except Exception as e:
            self.log(f"Error taking test screenshot: {str(e)}")
    
    def test_ldconsole(self):
        """Test LDPlayer console functionality"""
        try:
            ldconsole_path = self.ldplayer_console_path.get()
            if not os.path.exists(ldconsole_path):
                messagebox.showerror("Error", f"LDPlayer console not found at: {ldconsole_path}")
                return
            
            self.log("🔧 Testing LDPlayer console...")
            self.log(f"LDConsole path: {ldconsole_path}")
            
            # Test basic ldconsole functionality
            try:
                self.log("Testing 'ldconsole list2'...")
                result = subprocess.run([ldconsole_path, 'list2'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log(f"✅ LDConsole list2 output:")
                    self.log(result.stdout)
                else:
                    self.log(f"❌ LDConsole list2 failed: {result.stderr}")
            except Exception as e:
                self.log(f"❌ LDConsole list2 error: {str(e)}")
            
            # Test if we can get instance information
            try:
                self.log("Testing instance information...")
                result = subprocess.run([ldconsole_path, 'list2'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    self.log(f"Found {len(lines)} instance(s):")
                    for line in lines:
                        if line.strip():
                            self.log(f"  {line.strip()}")
                else:
                    self.log("No instances found or error getting instance list")
            except Exception as e:
                self.log(f"❌ Error getting instance list: {str(e)}")
            
            self.log("🔧 LDConsole test complete")
            
        except Exception as e:
            self.log(f"LDConsole test error: {str(e)}")
            messagebox.showerror("Error", f"LDConsole test failed: {str(e)}")
    
    def open_saved_images_folder(self):
        """Open the saved images folder in file explorer"""
        try:
            if os.path.exists(self.saved_images_folder):
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(self.saved_images_folder)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", self.saved_images_folder])
                else:  # Linux
                    subprocess.run(["xdg-open", self.saved_images_folder])
                
                self.log(f"Opened saved images folder: {self.saved_images_folder}")
            else:
                self.log(f"Saved images folder does not exist: {self.saved_images_folder}")
                messagebox.showwarning("Warning", f"Saved images folder does not exist: {self.saved_images_folder}")
                
        except Exception as e:
            self.log(f"Error opening saved images folder: {str(e)}")
            messagebox.showerror("Error", f"Failed to open saved images folder: {str(e)}")
    

    
    def trigger_macro(self):
        """Trigger macro execution in LDPlayer by focusing and pressing Page Down"""
        self.log("🎮 Focusing LDPlayer and sending Page Down...")
        
        try:
            # Focus LDPlayer window
            self.log("Focusing LDPlayer window...")
            ldplayer_window = pyautogui.getWindowsWithTitle("LDPlayer")
            
            if ldplayer_window:
                # Focus the first LDPlayer window found
                ldplayer_window[0].activate()
                time.sleep(0.5)  # Wait for focus
                self.log("✅ LDPlayer window focused")
                
                # Press Page Down
                pyautogui.press('pagedown')
                self.log("✅ Page Down key pressed")
                
            else:
                self.log("❌ LDPlayer window not found")
                self.log("Make sure LDPlayer is running and visible")
                
        except Exception as e:
            self.log(f"Error triggering macro: {str(e)}")
        
        self.log("Macros should now be running in LDPlayer")
    
    def close_ldplayer_instance(self, instance_id):
        """Close a specific LDPlayer instance using ldconsole"""
        try:
            ldconsole_path = self.ldplayer_console_path.get()
            if not os.path.exists(ldconsole_path):
                self.log(f"❌ LDPlayer console not found at: {ldconsole_path}")
                return False
            
            # LDPlayer instances are typically named "LDPlayer" followed by a number
            # Instance 1 = LDPlayer, Instance 2 = LDPlayer-1, Instance 3 = LDPlayer-2, etc.
            if instance_id == 1:
                instance_name = "LDPlayer"
            else:
                instance_name = f"LDPlayer-{instance_id - 1}"
            
            self.log(f"🔄 Closing LDPlayer instance {instance_id} ({instance_name})...")
            
            # Use ldconsole to quit the instance
            result = subprocess.run(
                [ldconsole_path, 'quit', '--name', instance_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                self.log(f"✅ Successfully closed instance {instance_id} ({instance_name})")
                self.closed_instances.add(instance_id)
                return True
            else:
                self.log(f"❌ Failed to close instance {instance_id}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"⏱️ Timeout while closing instance {instance_id}")
            return False
        except Exception as e:
            self.log(f"❌ Error closing instance {instance_id}: {str(e)}")
            return False
    
    def start_monitoring(self):
        """Start monitoring instances"""
        if not self.instance_ports:
            messagebox.showerror("Error", "Please generate instance ports first")
            return
        
        if not self.detector_initialized:
            messagebox.showerror("Error", "Please initialize the character detector first")
            return
        
        if not self.target_character.get():
            messagebox.showerror("Error", "Please enter target character name")
            return
        
        if not self.screenshot_timings:
            messagebox.showerror("Error", "Please add at least one screenshot timing")
            return
        
        self.is_monitoring = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Reset closed instances set
        self.closed_instances.clear()
        
        self.log("Starting monitoring...")
        self.log(f"Screenshots will be taken at: {', '.join([str(t) + 's' for t in self.screenshot_timings])}")
        self.log(f"Confidence threshold: {self.confidence_threshold}")
        self.log(f"Deduplication distance: {self.deduplication_distance.get()} pixels")
        self.log(f"Auto-close instances: {'Enabled' if self.auto_close_instances.get() else 'Disabled'}")
        self.log(f"Saved images folder: {self.saved_images_folder}")
        self.log("📸 First cycle: All screenshots from instances 1 and 5 will be saved")
        self.log("🔄 Monitoring will continue until manually stopped or all instances are closed")
        self.log("Make sure your LDPlayer instances are ready to run their macros!")
        
        # Start monitoring in separate thread
        self.monitor_thread = threading.Thread(target=self.monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring instances"""
        self.is_monitoring = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("Monitoring stopped")
    
    def monitoring_loop(self):
        """Main monitoring loop with automatic repetition"""
        try:
            adb_path = self.adb_path.get()
            duration = self.monitoring_duration.get()
            cycle_duration = self.cycle_duration.get()
            target_pulls = self.target_pulls.get()
            auto_repeat = self.auto_repeat.get()
            
            self.log(f"Starting automatic reroll monitoring...")
            self.log(f"Cycle duration: {cycle_duration}s")
            self.log(f"Target pulls: {target_pulls}")
            self.log(f"Auto repeat: {'Enabled' if auto_repeat else 'Disabled'}")
            self.log(f"Screenshots will be taken at: {', '.join([str(t) + 's' for t in self.screenshot_timings])}")
            self.log("Waiting for macro trigger (Page Down)...")
            
            while self.is_monitoring:
                self.current_cycles += 1
                self.log(f"=== Starting Cycle {self.current_cycles} ===")
                
                # Special logging for first cycle
                if self.current_cycles == 1:
                    self.log("📸 FIRST CYCLE: All screenshots from instances 1 and 5 will be saved to the saved_images folder")
                
                # Reset counts if option is enabled
                if self.reset_counts.get():
                    self.instance_pulls = {i+1: 0 for i in range(len(self.instance_ports))}
                    self.successful_pulls = 0
                    self.log("Counts reset for new cycle")
                    self.update_instance_labels()
                
                # Reset ignored instances for new cycle
                self.ignored_instances.clear()
                self.instance_last_screenshots.clear()
                self.log("Duplicate detection reset for new cycle")
                
                # Trigger macro for this cycle
                self.log("Triggering macro for this cycle...")
                self.trigger_macro()
                
                # Start monitoring immediately
                self.log("⏳ Starting screenshot monitoring...")
                
                # Run one monitoring cycle
                cycle_start_time = time.time()
                screenshot_count = 0
                next_timing_index = 0
                
                while self.is_monitoring and (time.time() - cycle_start_time) < duration:
                    current_time = time.time() - cycle_start_time
                    
                    # Check if it's time for the next screenshot
                    if (next_timing_index < len(self.screenshot_timings) and 
                        current_time >= self.screenshot_timings[next_timing_index]):
                        
                        screenshot_count += 1
                        timing = self.screenshot_timings[next_timing_index]
                        self.log(f"Taking screenshots at {timing}s mark (cycle {self.current_cycles}, round {screenshot_count})...")
                        
                        # Take screenshots from all active instances first (for exact timing)
                        screenshot_files = []
                        for i, port in enumerate(self.instance_ports):
                            instance_id = i + 1
                            
                            # Skip closed instances
                            if instance_id in self.closed_instances:
                                self.log(f"Instance {instance_id}: Skipped (already closed)")
                                continue
                            
                            try:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"screenshot_cycle{self.current_cycles}_instance_{instance_id}_t{timing}s_{timestamp}.png"
                                
                                # Take screenshot
                                subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', 'shell', 'screencap', '/sdcard/screenshot.png'], check=True)
                                
                                # Pull screenshot
                                subprocess.run([adb_path, '-s', f'127.0.0.1:{port}', 'pull', '/sdcard/screenshot.png', filename], check=True)
                                
                                # Save all images from first and last instance during first cycle
                                instance_ids = list(self.instance_pulls.keys())
                                first_instance = instance_ids[0] if instance_ids else None
                                last_instance = instance_ids[-1] if instance_ids else None
                                if self.current_cycles == 1 and instance_id in [first_instance, last_instance]:
                                    saved_filename = os.path.join(self.saved_images_folder, f"cycle1_instance{instance_id}_t{timing}s_{timestamp}.png")
                                    try:
                                        import shutil
                                        shutil.copy2(filename, saved_filename)
                                        self.log(f"Instance {instance_id}: Screenshot saved to {saved_filename}")
                                    except Exception as e:
                                        self.log(f"Error saving image for instance {instance_id}: {str(e)}")
                                
                                screenshot_files.append((instance_id, filename, port))
                                self.log(f"Instance {instance_id}: Screenshot taken and saved")
                                
                            except Exception as e:
                                self.log(f"Error taking screenshot from instance {instance_id}: {str(e)}")
                        
                        # Now scan all screenshots
                        self.log(f"Scanning {len(screenshot_files)} screenshots for Twin Turbo...")
                        for instance_id, filename, port in screenshot_files:
                            try:
                                # Check for duplicate screenshot
                                if self.is_duplicate_screenshot(instance_id, filename):
                                    self.ignored_instances.add(instance_id)
                                    self.log(f"🚫 Instance {instance_id}: Ignoring all pulls for this cycle due to duplicate screenshot")
                                    continue
                                
                                # Skip if instance is already ignored for this cycle
                                if instance_id in self.ignored_instances:
                                    self.log(f"🚫 Instance {instance_id}: Skipping scan (ignored due to previous duplicate)")
                                    continue
                                
                                # Check for target character
                                detections = self.detect_character_with_details(filename)
                                if detections:
                                    self.instance_pulls[instance_id] += 1
                                    self.successful_pulls += 1
                                    
                                    self.log(f"SUCCESS! Found {self.target_character.get()} in instance {instance_id} at {timing}s mark!")
                                    self.log(f"Instance {instance_id} pulls: {self.instance_pulls[instance_id]}")
                                    self.log(f"Total pulls: {self.successful_pulls}")
                                    
                                    # Save annotated screenshot
                                    annotated_filename = self.save_annotated_screenshot(filename, detections, instance_id, timing)
                                    self.log(f"Saved annotated screenshot: {annotated_filename}")
                                    
                                    # Check if this instance has reached target
                                    if self.instance_pulls[instance_id] >= target_pulls:
                                        self.log(f"🎉 Instance {instance_id} has reached target of {target_pulls} pulls!")
                                        self.log(f"Instance {instance_id} is ready!")
                                        
                                        # Close the instance if auto-close is enabled
                                        if self.auto_close_instances.get():
                                            self.log(f"🔄 Auto-closing instance {instance_id}...")
                                            if self.close_ldplayer_instance(instance_id):
                                                self.log(f"✅ Instance {instance_id} closed successfully")
                                            else:
                                                self.log(f"⚠️ Failed to close instance {instance_id}, but it has reached target")
                                    
                                    # Update display
                                    self.update_instance_labels()
                                else:
                                    self.log(f"Instance {instance_id}: No Twin Turbo detected")
                                
                                # Delete original screenshot after scanning
                                try:
                                    os.remove(filename)
                                    self.log(f"Instance {instance_id}: Original screenshot deleted after scanning")
                                except Exception as e:
                                    self.log(f"Instance {instance_id}: Failed to delete original screenshot: {str(e)}")
                                
                            except Exception as e:
                                self.log(f"Error scanning instance {instance_id}: {str(e)}")
                                # Try to clean up the file even if scanning failed
                                try:
                                    os.remove(filename)
                                except:
                                    pass
                        
                        next_timing_index += 1
                    
                    # Sleep for a short interval to check timing
                    time.sleep(0.1)
                
                self.log(f"Cycle {self.current_cycles} completed.")
                self.log(f"Instance pulls: {dict(self.instance_pulls)}")
                self.log(f"Total pulls: {self.successful_pulls}")
                self.update_status()
                
                # Check if any active instance has reached target
                active_instances_at_target = [instance_id for instance_id, pulls in self.instance_pulls.items() 
                                            if pulls >= target_pulls and instance_id not in self.closed_instances]
                
                if active_instances_at_target:
                    self.log(f"🎉 Active instances {active_instances_at_target} have reached target of {target_pulls} pulls!")
                    self.log("These instances are ready!")
                
                # Note: We don't stop monitoring when all instances reach target
                # Monitoring continues until manually stopped or all instances are closed
                
                # Check if all instances are closed
                active_instance_count = len([instance_id for instance_id in self.instance_pulls.keys() 
                                           if instance_id not in self.closed_instances])
                if active_instance_count == 0:
                    self.log("🔄 All instances have been closed. Stopping monitoring...")
                    break
                else:
                    self.log(f"🔄 {active_instance_count} active instances remaining, continuing monitoring...")
                
                # Check if we should continue
                if not self.is_monitoring:
                    break
                
                if auto_repeat:
                    # Wait for cycle duration before starting next cycle
                    self.log(f"Waiting {cycle_duration}s before next cycle...")
                    time.sleep(cycle_duration)
                else:
                    break
            
            # Show final results
            instances_at_target = [instance_id for instance_id, pulls in self.instance_pulls.items() if pulls >= target_pulls]
            if instances_at_target:
                self.log(f"🎉 FINAL RESULTS:")
                self.log(f"Instances that reached target ({target_pulls} pulls): {instances_at_target}")
                for instance_id, pulls in self.instance_pulls.items():
                    status = "CLOSED" if instance_id in self.closed_instances else "ACTIVE"
                    self.log(f"Instance {instance_id}: {pulls} pulls ({status})")
            else:
                self.log("No instances reached the target number of pulls")
            
            # Show monitoring status
            active_instances = [instance_id for instance_id in self.instance_pulls.keys() if instance_id not in self.closed_instances]
            if active_instances:
                self.log(f"🔄 Active instances remaining: {active_instances}")
            else:
                self.log("✅ All instances have been closed")
            
            self.log("Monitoring stopped")
            
        except Exception as e:
            self.log(f"Monitoring error: {str(e)}")
        finally:
            self.stop_monitoring()
    
    def detect_character(self, screenshot_path):
        """Detect target character in screenshot using smart detection"""
        try:
            if not self.detector_initialized or not self.character_detector:
                return False
            
            # Use smart character detection with deduplication
            detections = self.detect_character_with_details(screenshot_path)
            
            # Return True if any unique detections found
            return len(detections) > 0
            
        except Exception as e:
            self.log(f"Character detection error: {str(e)}")
            return False
    
    def detect_character_with_details(self, screenshot_path):
        """Detect target character and return detailed detection results"""
        try:
            if not self.detector_initialized or not self.character_detector:
                return []
            
            # Use smart character detection
            detections = self.character_detector.detect_character(screenshot_path)
            
            if detections:
                # Log all detections
                for detection in detections:
                    self.log(f"Detection: Twin Turbo ({detection['method']}) - Confidence: {detection['confidence']:.2f}, Matches: {detection['matches']}")
                
                # Filter by confidence threshold
                filtered_detections = [d for d in detections if d['confidence'] >= self.confidence_threshold]
                
                # Remove duplicates (characters too close together)
                unique_detections = []
                for detection in filtered_detections:
                    location = detection['location']
                    
                    # Check if too close to existing detections
                    is_duplicate = False
                    dedup_distance = self.deduplication_distance.get()
                    for existing in unique_detections:
                        existing_location = existing['location']
                        distance = ((location[0] - existing_location[0])**2 + 
                                   (location[1] - existing_location[1])**2)**0.5
                        if distance < dedup_distance:  # Within configurable distance
                            is_duplicate = True
                            self.log(f"Removing duplicate detection at {location} (too close to {existing_location}, distance: {distance:.1f}px)")
                            break
                    
                    if not is_duplicate:
                        unique_detections.append(detection)
                
                self.log(f"After deduplication: {len(unique_detections)} unique Twin Turbo instances")
                return unique_detections
            
            return []
        except Exception as e:
            self.log(f"Character detection error: {str(e)}")
            return []
    
    def save_annotated_screenshot(self, original_filename, detections, instance_id, timing):
        """Save screenshot with detection markers pointing out Twin Turbo locations"""
        try:
            # Load the screenshot
            screenshot = cv2.imread(original_filename)
            if screenshot is None:
                self.log(f"Could not load screenshot for annotation: {original_filename}")
                return None
            
            # Create annotated version
            annotated_img = screenshot.copy()
            
            # Draw detection markers
            for i, detection in enumerate(detections):
                location = detection['location']
                confidence = detection['confidence']
                matches = detection['matches']
                
                # Draw circle around detection
                cv2.circle(annotated_img, location, 40, (0, 255, 0), 3)
                
                # Draw numbered marker
                cv2.circle(annotated_img, location, 15, (0, 255, 0), -1)
                cv2.putText(annotated_img, str(i+1), (location[0] - 8, location[1] + 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                # Draw label with details
                label = f"Twin Turbo {i+1} (Conf: {confidence:.2f}, Matches: {matches})"
                cv2.putText(annotated_img, label, (location[0] + 50, location[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add title
            title = f"Instance {instance_id} - {timing}s - {len(detections)} Twin Turbo(s) Found"
            cv2.putText(annotated_img, title, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
            
            # Create filename for annotated version
            base_name = os.path.splitext(original_filename)[0]
            annotated_filename = f"{base_name}_ANNOTATED_TwinTurbo{len(detections)}.png"
            
            # Save annotated image to saved images folder
            saved_annotated_filename = os.path.join(self.saved_images_folder, os.path.basename(annotated_filename))
            cv2.imwrite(saved_annotated_filename, annotated_img)
            
            # Also save to current directory for backward compatibility
            cv2.imwrite(annotated_filename, annotated_img)
            
            return saved_annotated_filename
            
        except Exception as e:
            self.log(f"Error saving annotated screenshot: {str(e)}")
            return None
    
    def update_status(self):
        """Update status labels"""
        self.cycle_label.config(text=str(self.current_cycles))
        self.pull_label.config(text=str(self.successful_pulls))
    
    def update_instance_labels(self):
        """Update instance-specific labels"""
        for instance_id, label in self.instance_labels.items():
            pulls = self.instance_pulls.get(instance_id, 0)
            target = self.target_pulls.get()
            status = ""
            if instance_id in self.closed_instances:
                status = " (CLOSED)"
            elif instance_id in self.ignored_instances:
                status = " (IGNORED)"
            label.config(text=f"Instance {instance_id}: {pulls}/{target}{status}")
    
    def calculate_image_hash(self, image_path):
        """Calculate hash of image for duplicate detection"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.log(f"Error calculating image hash: {str(e)}")
            return None
    
    def is_duplicate_screenshot(self, instance_id, screenshot_path):
        """Check if screenshot is duplicate of previous one for this instance"""
        try:
            current_hash = self.calculate_image_hash(screenshot_path)
            if current_hash is None:
                return False
            
            last_hash = self.instance_last_screenshots.get(instance_id)
            
            if last_hash == current_hash:
                self.log(f"⚠️ Instance {instance_id}: Duplicate screenshot detected (same image as previous)")
                return True
            
            # Update last screenshot hash for this instance
            self.instance_last_screenshots[instance_id] = current_hash
            return False
            
        except Exception as e:
            self.log(f"Error checking duplicate screenshot for instance {instance_id}: {str(e)}")
            return False
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

def main():
    root = tk.Tk()
    app = SimpleRerollMonitor(root)
    root.mainloop()

if __name__ == "__main__":
    main() 