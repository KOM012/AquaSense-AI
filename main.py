# main.py - FIXED VERSION WITH PRIORITY ALERTS
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import os
import sys
import cv2
from PIL import Image, ImageTk
import threading
import numpy as np
import gc

APP_ROOT   = os.path.dirname(os.path.abspath(__file__))
ICON_PATH  = os.path.join(APP_ROOT, 'icon.ico')
def set_window_icon(window: tk.Tk):
    if os.path.isfile(ICON_PATH):
        try:
            window.iconbitmap(ICON_PATH)
        except Exception:
            pass

# ENHANCED Port Cleaner Functionality
def cleanup_ports():
    """Close any open serial ports with enhanced error handling"""
    try:
        import serial
        from serial.tools import list_ports
        
        print("🧹 Cleaning up serial ports...")
        ports = list_ports.comports()
        locked_ports = []
        available_ports = []
        
        for port in ports:
            try:
                ser = serial.Serial(port.device, 9600, timeout=0.1)
                ser.close()
                available_ports.append(port.device)
                print(f"✅ {port.device} is available")
            except serial.SerialException as e:
                if "Access is denied" in str(e) or "PermissionError" in str(e):
                    locked_ports.append(port.device)
                    print(f"❌ {port.device} is locked - close Arduino IDE and other apps")
        
        return available_ports, locked_ports
        
    except ImportError:
        print("⚠️ pyserial not available, skipping port cleanup")
        return [], []
    except Exception as e:
        print(f"⚠️ Port cleanup error: {e}")
        return [], []

def force_system_cleanup():
    """Force cleanup of all system resources"""
    print("🧹 Performing system cleanup...")
    
    cv2.destroyAllWindows()
    
    for i in range(3):
        gc.collect()
    
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            print("✅ CUDA memory cleared")
    except ImportError:
        pass
    
    cleanup_ports()
    
    time.sleep(0.5)
    print("✅ System cleanup completed")

class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AquaSense-AI")
        set_window_icon(self.root)
        self.root.geometry("400x300")
        self.root.overrideredirect(True)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        self.root.geometry(f"400x300+{x}+{y}")
        
        self.bg_color = "#E6F3FF"
        self.primary_color = "#0077BE"
        
        self.setup_ui()
        
    def setup_ui(self):
        self.root.configure(bg=self.bg_color)
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        title_label = tk.Label(main_frame, text="🤿 AquaSense-AI", 
                              font=("Arial", 20, "bold"), 
                              fg=self.primary_color, 
                              bg=self.bg_color)
        title_label.pack(pady=(20, 10))
        
        subtitle_label = tk.Label(main_frame, 
                                 text="Advanced Drowning Detection System",
                                 font=("Arial", 10), 
                                 fg="#666666", 
                                 bg=self.bg_color)
        subtitle_label.pack(pady=(0, 30))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, 
                                           variable=self.progress_var,
                                           maximum=100,
                                           length=360)
        self.progress_bar.pack(pady=10)
        
        self.status_label = tk.Label(main_frame, 
                                    text="Initializing...",
                                    font=("Arial", 9), 
                                    fg="#333333", 
                                    bg=self.bg_color)
        self.status_label.pack(pady=5)
        
    def update_progress(self, value, status):
        self.progress_var.set(value)
        self.status_label.config(text=status)
        self.root.update()
        
    def close(self):
        self.root.destroy()
        
    def run_loading(self):
        steps = [
            (10, "Initializing UI..."),
            (30, "Loading modules..."),
            (60, "Checking cameras..."),
            (80, "Setting up detection..."),
            (100, "Ready!")
        ]
        
        for value, status in steps:
            self.update_progress(value, status)
            time.sleep(0.3)
            
        time.sleep(0.5)
        return True

class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AquaSense-AI - Main Menu")
        set_window_icon(self.root) 
        self.root.geometry("800x600")
        self.root.configure(bg="#E6F3FF")
        
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#E6F3FF")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)
        
        title_label = tk.Label(main_frame, text="🤿 AquaSense-AI", 
                              font=("Arial", 24, "bold"), 
                              fg="#0077BE", 
                              bg="#E6F3FF")
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(main_frame,
                                 text="Drowning Detection System Prototype",
                                 font=("Arial", 12),
                                 fg="#666666",
                                 bg="#E6F3FF")
        subtitle_label.pack(pady=(0, 40))
        
        buttons_frame = tk.Frame(main_frame, bg="#E6F3FF")
        buttons_frame.pack(expand=True)
        
        button_style = {
            "font": ("Arial", 14, "bold"),
            "width": 20,
            "height": 3,
            "bg": "#0077BE",
            "fg": "white",
            "bd": 0,
            "relief": "flat"
        }
        
        sim_btn = tk.Button(buttons_frame,
                           text="SIMULATE MODE\nTest with Video Files",
                           command=self.open_simulate_mode,
                           **button_style)
        sim_btn.pack(pady=15)
        
        live_btn = tk.Button(buttons_frame,
                            text="LIVE MODE\nReal-time\nCamera Monitoring",
                            command=self.open_live_mode,
                            **button_style)
        live_btn.pack(pady=15)
        
        def on_enter(e):
            e.widget.config(bg="#00A8FF")
        def on_leave(e):
            e.widget.config(bg="#0077BE")
            
        sim_btn.bind("<Enter>", on_enter)
        sim_btn.bind("<Leave>", on_leave)
        live_btn.bind("<Enter>", on_enter)
        live_btn.bind("<Leave>", on_leave)
        
        footer_frame = tk.Frame(main_frame, bg="#E6F3FF")
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20) 

        footer_label = tk.Label(footer_frame,
                                text="© 2025 AquaSense-AI Team",
                                font=("Arial", 10),
                                fg="#666666",
                                bg="#E6F3FF")
        footer_label.pack(pady=5)
        
    def open_simulate_mode(self):
        force_system_cleanup()
        available_ports, locked_ports = cleanup_ports()
        if locked_ports:
            print(f"Warning: Some ports are locked: {locked_ports}")
        
        self.root.destroy()
        setup = SetupScreen(mode='simulate')
        setup.show()
        
    def open_live_mode(self):
        force_system_cleanup()
        available_ports, locked_ports = cleanup_ports()
        if locked_ports:
            print(f"Warning: Some ports are locked: {locked_ports}")
        
        self.root.destroy()
        setup = SetupScreen(mode='live')
        setup.show()
        
    def show(self):
        self.setup_ui()
        self.root.mainloop()

class SetupScreen:
    def __init__(self, mode='live'):
        self.mode = mode
        self.root = tk.Tk()
        self.root.title(f"AquaSense-AI - {mode.upper()} Mode Setup")
        self.root.geometry("900x700")
        self.root.configure(bg="#E6F3FF")
        
        self.model_path = None
        self.video_path = None
        self.camera_index = 0
        self.confidence = 0.5
        self.preview_running = False
        self.camera_cap = None
        
        self.model_path_var = tk.StringVar()
        self.video_path_var = tk.StringVar()
        self.conf_var = tk.DoubleVar(value=0.5)
        self.camera_combo = None
        self.start_btn = None
        self.preview_btn = None
        
        try:
            from transmitter import BluetoothTransmitter
            self.bt = BluetoothTransmitter()
            self.bt_available = True
        except ImportError:
            self.bt = None
            self.bt_available = False
            
        try:
            from core.perimeter import PerimeterMonitor
            self.perimeter = PerimeterMonitor()
            self.perimeter_available = True
        except ImportError:
            self.perimeter = None
            self.perimeter_available = False
            
        self.use_perimeter = tk.BooleanVar(value=False)
        self.perimeter_configured = False
            
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#E6F3FF")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        title_text = "Simulate Mode Setup" if self.mode == 'simulate' else "Live Mode Setup"
        title_label = tk.Label(main_frame, 
                              text=title_text,
                              font=("Arial", 18, "bold"),
                              fg="#0077BE",
                              bg="#E6F3FF")
        title_label.pack(pady=(0, 20))
        
        content_frame = tk.Frame(main_frame, bg="#E6F3FF")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = tk.Frame(content_frame, bg="#E6F3FF", width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_panel.pack_propagate(False)
        
        right_panel = tk.Frame(content_frame, bg="#000000", relief=tk.RAISED, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_controls(left_panel)
        self.setup_preview(right_panel)
        
        bottom_frame = tk.Frame(main_frame, bg="#E6F3FF")
        bottom_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(bottom_frame, 
                  text="← Back to Main Menu",
                  command=self.back_to_main).pack(side=tk.LEFT)
        
        self.start_btn = ttk.Button(bottom_frame,
                                   text="Start Monitoring →",
                                   command=self.start_monitoring,
                                   state=tk.DISABLED)
        self.start_btn.pack(side=tk.RIGHT)
        
        self.root.after(100, self.check_start_conditions)
        
    def setup_controls(self, parent):
        if self.bt_available:
            bluetooth_frame = ttk.LabelFrame(parent, text="Bluetooth Setup (Optional)")
            bluetooth_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(bluetooth_frame, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.serial_combo = ttk.Combobox(bluetooth_frame, state="readonly", width=15)
            self.serial_combo.grid(row=0, column=1, padx=5, pady=5)
            
            self.bt_connect_btn = ttk.Button(bluetooth_frame, 
                                            text="Connect",
                                            command=self.toggle_bluetooth)
            self.bt_connect_btn.grid(row=0, column=2, padx=5, pady=5)
            
            self.bt_status_label = ttk.Label(bluetooth_frame, text="Disconnected", foreground="red")
            self.bt_status_label.grid(row=0, column=3, padx=5, pady=5)
            
            ttk.Button(bluetooth_frame, 
                      text="Refresh Ports", 
                      command=self.refresh_serial_ports).grid(row=1, column=0, columnspan=2, pady=5)
            
            self.refresh_serial_ports()
        
        model_frame = ttk.LabelFrame(parent, text="AI Model Configuration")
        model_frame.pack(fill=tk.X, pady=(0, 15))
        
        model_path_frame = tk.Frame(model_frame, bg="#E6F3FF")
        model_path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Entry(model_path_frame, textvariable=self.model_path_var, width=30).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(model_path_frame, 
                  text="Browse Model", 
                  command=self.browse_model).pack(side=tk.LEFT)
        
        confidence_frame = tk.Frame(model_frame, bg="#E6F3FF")
        confidence_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(confidence_frame, text="Confidence:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(confidence_frame, textvariable=self.conf_var, width=6).pack(side=tk.LEFT)
        
        if self.mode == 'simulate':
            self.setup_simulate_controls(parent)
        else:
            self.setup_live_controls(parent)
        
    def setup_simulate_controls(self, parent):
        video_frame = ttk.LabelFrame(parent, text="Video File Selection")
        video_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Entry(video_frame, textvariable=self.video_path_var, width=30).pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(video_frame, 
                  text="Browse Video", 
                  command=self.browse_video).pack(side=tk.LEFT, padx=5, pady=10)
        
        preview_frame = ttk.LabelFrame(parent, text="Preview")
        preview_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.preview_btn = ttk.Button(preview_frame,
                  text="Preview Video",
                  command=self.preview_video_file)
        self.preview_btn.pack(pady=10)
        
    def setup_live_controls(self, parent):
        camera_frame = ttk.LabelFrame(parent, text="Camera Configuration")
        camera_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(camera_frame, text="Camera:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.camera_combo = ttk.Combobox(camera_frame, state="readonly", width=20)
        self.camera_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(camera_frame, 
                  text="Refresh Cameras", 
                  command=self.refresh_cameras).grid(row=1, column=0, columnspan=2, pady=5)
                  
        self.preview_btn = ttk.Button(camera_frame,
                  text="Start Preview",
                  command=self.toggle_camera_preview)
        self.preview_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        if self.perimeter_available:
            perimeter_frame = ttk.LabelFrame(parent, text="Perimeter Setup (Optional)")
            perimeter_frame.pack(fill=tk.X, pady=(0, 15))
            
            perimeter_toggle_frame = tk.Frame(perimeter_frame, bg="#E6F3FF")
            perimeter_toggle_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Checkbutton(perimeter_toggle_frame, 
                          text="Enable Perimeter Monitoring",
                          variable=self.use_perimeter,
                          command=self.toggle_perimeter_options).pack(side=tk.LEFT)
            
            self.perimeter_controls_frame = tk.Frame(perimeter_frame, bg="#E6F3FF")
            self.perimeter_controls_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self.draw_perimeter_btn = ttk.Button(self.perimeter_controls_frame,
                      text="Draw Perimeter",
                      command=self.draw_perimeter,
                      state=tk.DISABLED)
            self.draw_perimeter_btn.pack(pady=5)
                      
            self.perimeter_status = ttk.Label(self.perimeter_controls_frame, text="Not configured")
            self.perimeter_status.pack(pady=5)
            
            self.toggle_perimeter_options()
        
        self.refresh_cameras()
        
    def setup_preview(self, parent):
        self.preview_label = tk.Label(parent, bg="#000000", 
                                     text="Preview Area\n\nFor Live Mode: Start camera preview\nFor Simulate Mode: Select video file", 
                                     fg="white", font=("Arial", 12), justify=tk.CENTER)
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
    def toggle_perimeter_options(self):
        if self.use_perimeter.get():
            if hasattr(self, 'draw_perimeter_btn'):
                self.draw_perimeter_btn.config(state=tk.NORMAL)
            self.perimeter_status.config(text="Not configured")
        else:
            if hasattr(self, 'draw_perimeter_btn'):
                self.draw_perimeter_btn.config(state=tk.DISABLED)
            self.perimeter_status.config(text="Perimeter disabled")
            self.perimeter_configured = False
            
        self.check_start_conditions()
        
    def refresh_serial_ports(self):
        if self.bt_available and hasattr(self, 'serial_combo'):
            ports = self.bt.list_ports()
            self.serial_combo['values'] = ports
            if ports:
                self.serial_combo.current(0)
        
    def toggle_bluetooth(self):
        if not self.bt_available:
            messagebox.showinfo("Bluetooth", "Bluetooth module not available")
            return
            
        if not self.bt.connected:
            port = self.serial_combo.get()
            if not port:
                messagebox.showwarning("Select Port", "Please select a serial port")
                return
                
            def connect_thread():
                success = self.bt.connect(port)
                self.root.after(0, lambda: self.update_bt_status(success))
                
            threading.Thread(target=connect_thread, daemon=True).start()
            self.bt_connect_btn.config(state=tk.DISABLED, text="Connecting...")
        else:
            self.bt.disconnect()
            self.update_bt_status(False)
            
    def update_bt_status(self, connected):
        if connected:
            self.bt_status_label.config(text="Connected", foreground="green")
            self.bt_connect_btn.config(text="Disconnect")
        else:
            self.bt_status_label.config(text="Disconnected", foreground="red")
            self.bt_connect_btn.config(text="Connect")
        self.bt_connect_btn.config(state=tk.NORMAL)
        
    def browse_model(self):
        path = filedialog.askopenfilename(
            title="Select YOLO Model",
            filetypes=[("PyTorch models", "*.pt"), ("All files", "*.*")]
        )
        if path:
            self.model_path_var.set(path)
            self.check_start_conditions()
            
    def browse_video(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if path:
            self.video_path_var.set(path)
            self.check_start_conditions()
            
    def preview_video_file(self):
        if not self.video_path_var.get():
            messagebox.showwarning("No Video", "Please select a video file first")
            return
        
        if hasattr(self, 'video_preview_running') and self.video_preview_running:
            self.video_preview_running = False
            if hasattr(self, 'video_cap'):
                self.video_cap.release()
            self.preview_btn.config(text="Preview Video")
            return
            
        def preview_thread():
            self.video_preview_running = True
            self.video_cap = cv2.VideoCapture(self.video_path_var.get())
            
            if not self.video_cap.isOpened():
                messagebox.showerror("Video Error", "Cannot open video file")
                self.video_preview_running = False
                return
                
            self.preview_btn.config(text="Stop Preview")
            
            while self.video_preview_running:
                ret, frame = self.video_cap.read()
                if not ret:
                    self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                    
                frame = cv2.resize(frame, (600, 400))
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.root.after(0, lambda: self.update_preview(imgtk))
                time.sleep(0.03)
                
            self.video_cap.release()
            self.preview_btn.config(text="Preview Video")
            
        threading.Thread(target=preview_thread, daemon=True).start()
            
    def refresh_cameras(self):
        cameras = []
        for i in range(5):
            try:
                for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY]:
                    cap = cv2.VideoCapture(i, backend)
                    if cap.isOpened():
                        cameras.append(f"Camera {i}")
                        cap.release()
                        break
            except:
                pass
                
        if self.camera_combo:
            self.camera_combo['values'] = cameras
            if cameras:
                self.camera_combo.current(0)
        self.check_start_conditions()
        
    def toggle_camera_preview(self):
        if self.preview_running:
            self.stop_camera_preview()
        else:
            self.start_camera_preview()
            
    def start_camera_preview(self):
        if self.preview_running:
            return
            
        selected = self.camera_combo.get()
        if not selected:
            messagebox.showwarning("Select Camera", "Please select a camera")
            return
            
        try:
            self.camera_index = int(selected.split()[-1])
            
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                self.camera_cap = cv2.VideoCapture(self.camera_index, backend)
                if self.camera_cap.isOpened():
                    self.camera_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera_cap.set(cv2.CAP_PROP_FPS, 30)
                    self.camera_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    print(f"✅ Camera opened with backend: {backend}")
                    break
                else:
                    self.camera_cap.release()
            
            if not self.camera_cap.isOpened():
                messagebox.showerror("Camera Error", f"Cannot open camera {self.camera_index}")
                return
                
            self.preview_running = True
            if self.preview_btn:
                self.preview_btn.config(text="Stop Preview")
            if self.perimeter_available and hasattr(self, 'draw_perimeter_btn'):
                if self.use_perimeter.get():
                    self.draw_perimeter_btn.config(state=tk.NORMAL)
            
            def preview_thread():
                while self.preview_running:
                    ret, frame = self.camera_cap.read()
                    if ret:
                        frame = cv2.resize(frame, (600, 400))
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(rgb)
                        imgtk = ImageTk.PhotoImage(image=img)
                        self.root.after(0, lambda: self.update_preview(imgtk))
                    time.sleep(0.03)
                    
            threading.Thread(target=preview_thread, daemon=True).start()
            self.check_start_conditions()
            
        except Exception as e:
            messagebox.showerror("Camera Error", f"Error starting camera: {e}")
            
    def stop_camera_preview(self):
        self.preview_running = False
        if self.preview_btn:
            self.preview_btn.config(text="Start Preview" if self.mode == 'live' else "Preview Video")
        if self.perimeter_available and hasattr(self, 'draw_perimeter_btn'):
            self.draw_perimeter_btn.config(state=tk.DISABLED)
        if self.camera_cap:
            self.camera_cap.release()
            self.camera_cap = None
            
    def update_preview(self, imgtk):
        self.preview_label.config(image=imgtk, text="")
        self.preview_label.image = imgtk
        
    def draw_perimeter(self):
        if not self.camera_cap or not self.preview_running:
            messagebox.showwarning("Camera Error", "Start camera preview first")
            return
            
        ret, frame = self.camera_cap.read()
        if not ret:
            messagebox.showerror("Camera Error", "Could not read frame from camera")
            return
            
        def perimeter_callback(success):
            if success:
                self.perimeter_status.config(text="Configured ✓", foreground="green")
                self.perimeter_configured = True
            else:
                self.perimeter_status.config(text="Cancelled", foreground="red")
                self.perimeter_configured = False
            self.check_start_conditions()
            self.start_camera_preview()
                
        was_running = self.preview_running
        self.preview_running = False
        time.sleep(0.5)
        
        if self.perimeter:
            success = self.perimeter.draw_perimeter_interactive(frame)
            perimeter_callback(success)
        
    def check_start_conditions(self):
        if not hasattr(self, 'start_btn') or self.start_btn is None:
            return
            
        has_model = bool(self.model_path_var.get())
        
        if self.mode == 'simulate':
            has_video = bool(self.video_path_var.get())
            if has_model and has_video:
                self.start_btn.config(state=tk.NORMAL)
            else:
                self.start_btn.config(state=tk.DISABLED)
        else:
            has_camera = self.preview_running
            
            if self.perimeter_available and self.use_perimeter.get():
                has_perimeter = self.perimeter_configured
            else:
                has_perimeter = True
            
            if has_model and has_camera and has_perimeter:
                self.start_btn.config(state=tk.NORMAL)
            else:
                self.start_btn.config(state=tk.DISABLED)
            
    def start_monitoring(self):
        config = {
            'mode': self.mode,
            'model_path': self.model_path_var.get(),
            'confidence': float(self.conf_var.get()),
            'bluetooth_connected': self.bt.connected if self.bt_available else False,
            'bluetooth': self.bt if self.bt_available else None
        }
        
        if self.mode == 'simulate':
            config['video_path'] = self.video_path_var.get()
        else:
            config['camera_index'] = self.camera_index
            if self.perimeter_available and self.use_perimeter.get() and self.perimeter_configured:
                config['perimeter'] = self.perimeter
                config['use_perimeter'] = True
            else:
                config['perimeter'] = None
                config['use_perimeter'] = False
            
        self.cleanup_preview()
        
        force_system_cleanup()
        
        self.root.destroy()
        
        monitor = MonitorScreen(config)
        monitor.show()
        
    def cleanup_preview(self):
        self.preview_running = False
        if hasattr(self, 'video_preview_running'):
            self.video_preview_running = False
        if hasattr(self, 'video_cap'):
            self.video_cap.release()
        if self.camera_cap:
            self.camera_cap.release()
            self.camera_cap = None
        
    def back_to_main(self):
        self.cleanup_preview()
        
        force_system_cleanup()
        
        self.root.destroy()
        menu = MainMenu()
        menu.show()
        
    def show(self):
        self.root.mainloop()

class MonitorScreen:
    def __init__(self, config):
        self.config = config
        self.root = tk.Tk()
        self.root.title("AquaSense-AI - Monitoring")
        self.root.geometry("1200x800")
        self.root.configure(bg="#E6F3FF")
        
        self.running = False
        self.detector = None
        self.cap = None
        self.last_perimeter_check = 0
        self.perimeter_interval = 1.0
        
        # ALERT STATE MANAGEMENT - FIXED
        self.current_alert_state = "NONE"  # "NONE", "DROWNING", "OBSTRUCTION"
        self.alert_start_time = 0
        self.last_alert_update = 0
        
        # Obstruction tracking
        self.obstruction_detected = False
        self.obstruction_start_time = 0
        self.obstruction_duration = 0
        
        # Drowning tracking
        self.drowning_detected = False
        self.drowning_start_time = 0
        self.drowning_duration = 0
        
        # Alert persistence
        self.min_obstruction_duration = 3.0
        self.min_drowning_duration = 2.0
        
        # Performance
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_update = time.time()
        self.fps = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#E6F3FF")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        header_frame = tk.Frame(main_frame, bg="#E6F3FF")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        mode_text = "Simulate" if self.config['mode'] == 'simulate' else "Live"
        title_label = tk.Label(header_frame,
                              text=f"🤿 AquaSense-AI - {mode_text} Monitoring",
                              font=("Arial", 16, "bold"),
                              fg="#0077BE",
                              bg="#E6F3FF")
        title_label.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(header_frame,
                                    text="● READY",
                                    font=("Arial", 12, "bold"),
                                    fg="green",
                                    bg="#E6F3FF")
        self.status_label.pack(side=tk.RIGHT)
        
        content_frame = tk.Frame(main_frame, bg="#E6F3FF")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        video_frame = tk.Frame(content_frame, bg="#000000", relief=tk.RAISED, bd=2)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        
        self.video_label = tk.Label(video_frame, bg="#000000", 
                                   text="Starting monitoring...",
                                   fg="white", font=("Arial", 14))
        self.video_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        right_panel = tk.Frame(content_frame, bg="#E6F3FF", width=300)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        
        stats_frame = ttk.LabelFrame(right_panel, text="Live Statistics", width=280)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.fps_label = ttk.Label(stats_frame, text="FPS: --")
        self.fps_label.pack(anchor=tk.W, pady=2)
        
        self.detection_label = ttk.Label(stats_frame, text="Detections: 0")
        self.detection_label.pack(anchor=tk.W, pady=2)
        
        self.obstruction_label = ttk.Label(stats_frame, text="Obstructions: 0")
        self.obstruction_label.pack(anchor=tk.W, pady=2)
        
        self.detector_status_label = ttk.Label(stats_frame, text="Detector: Initializing", foreground="blue")
        self.detector_status_label.pack(anchor=tk.W, pady=2)
        
        self.alert_frame = ttk.LabelFrame(right_panel, text="Alert Status", width=280)
        self.alert_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.drowning_alert_label = ttk.Label(self.alert_frame, text="Drowning: No Alert", foreground="green")
        self.drowning_alert_label.pack(anchor=tk.W, pady=2)
        
        self.obstruction_alert_label = ttk.Label(self.alert_frame, text="Obstruction: No Alert", foreground="green")
        self.obstruction_alert_label.pack(anchor=tk.W, pady=2)
        
        self.current_alert_label = ttk.Label(self.alert_frame, text="Active: None", foreground="blue")
        self.current_alert_label.pack(anchor=tk.W, pady=2)
        
        if self.config.get('use_perimeter', False):
            self.visibility_var = tk.BooleanVar(value=True)
            visibility_frame = ttk.LabelFrame(right_panel, text="Display Options", width=280)
            visibility_frame.pack(fill=tk.X, pady=(0, 15))
            
            self.visibility_check = ttk.Checkbutton(visibility_frame, 
                                                  text="Show Perimeter", 
                                                  variable=self.visibility_var,
                                                  command=lambda: self.set_visible(self.visibility_var.get()))
            self.visibility_check.pack(anchor=tk.W, pady=2)
        
        if self.config.get('bluetooth_connected'):
            bt_frame = ttk.LabelFrame(right_panel, text="Bluetooth Status", width=280)
            bt_frame.pack(fill=tk.X, pady=(0, 15))
            
            bt_label = ttk.Label(bt_frame, text="Connected ✓", foreground="green")
            bt_label.pack(anchor=tk.W, pady=5)
        
        controls_frame = ttk.LabelFrame(right_panel, text="Controls", width=280)
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(controls_frame,
                  text="⏹️ Stop Monitoring",
                  command=self.stop_monitoring).pack(fill=tk.X, pady=5)
        
        if self.config.get('bluetooth_connected'):
            test_frame = ttk.LabelFrame(right_panel, text="Test Bluetooth", width=280)
            test_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Button(test_frame,
                      text="Test Drowning Alert",
                      command=self.test_drowning_alert).pack(fill=tk.X, pady=2)
            
            ttk.Button(test_frame,
                      text="Test Obstruction Alert",
                      command=self.test_obstruction_alert).pack(fill=tk.X, pady=2)
            
            ttk.Button(test_frame,
                      text="Clear Alerts",
                      command=self.test_clear_alerts).pack(fill=tk.X, pady=2)
        
        bottom_frame = tk.Frame(main_frame, bg="#E6F3FF")
        bottom_frame.pack(fill=tk.X, pady=(20, 0))
        
        if self.config['mode'] == 'simulate':
            source_text = f"Source: {self.config.get('video_path', 'Video File')}"
        else:
            camera_index = self.config.get('camera_index', 0)
            source_text = f"Source: Camera {camera_index}"
            if self.config.get('use_perimeter', False):
                source_text += " | Perimeter: Active"
            else:
                source_text += " | Perimeter: Disabled"
            
        source_label = tk.Label(bottom_frame, text=source_text, bg="#E6F3FF", fg="#666666")
        source_label.pack(side=tk.LEFT)
        
    def set_visible(self, visible):
        self.show_perimeter = visible
        
    def test_drowning_alert(self):
        if self.config.get('bluetooth_connected') and self.config.get('bluetooth'):
            self.config['bluetooth'].send_drowning_alert()
            self.drowning_alert_label.config(text="Drowning: TEST ALERT", foreground="red")
            
    def test_obstruction_alert(self):
        if self.config.get('bluetooth_connected') and self.config.get('bluetooth'):
            self.config['bluetooth'].send_obstruction_alert()
            self.obstruction_alert_label.config(text="Obstruction: TEST ALERT", foreground="orange")
            
    def test_clear_alerts(self):
        if self.config.get('bluetooth_connected') and self.config.get('bluetooth'):
            self.config['bluetooth'].send_clear_alert()
            self.drowning_alert_label.config(text="Drowning: No Alert", foreground="green")
            self.obstruction_alert_label.config(text="Obstruction: No Alert", foreground="green")
            self.current_alert_label.config(text="Active: None", foreground="blue")
    
    def initialize_detector_with_fallback(self):
        try:
            from detect import RealtimeDetector
            print("Attempting to initialize RealtimeDetector...")
            detector = RealtimeDetector(
                self.config['model_path'],
                conf=self.config['confidence']
            )
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            annotated, detected, detections = detector.detect_frame(test_frame)
            print("RealtimeDetector initialized successfully")
            self.detector_status_label.config(text="Detector: YOLO (Active)", foreground="green")
            return detector
                
        except Exception as e:
            print(f"Detector initialization failed: {e}")
            class BasicDetector:
                def __init__(self, model_path, conf=0.5):
                    self.model_path = model_path
                    self.conf = conf
                    
                def detect_frame(self, frame):
                    annotated = frame.copy()
                    cv2.putText(annotated, "BASIC DETECTOR", (50, 50),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(annotated, "Model compatibility issue", (50, 80),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    return annotated, False, []
            
            self.detector_status_label.config(text="Detector: Basic (Error)", foreground="red")
            return BasicDetector(self.config['model_path'], self.config['confidence'])
    
    def start_monitoring(self):
        try:
            self.detector = self.initialize_detector_with_fallback()
            
            if self.config['mode'] == 'simulate':
                video_path = self.config.get('video_path', '')
                if video_path and os.path.exists(video_path):
                    self.cap = cv2.VideoCapture(video_path)
                    print(f"Using video file: {video_path}")
                else:
                    self.cap = self.create_demo_video()
                    print("Using demo video")
            else:
                camera_index = self.config.get('camera_index', 0)
                for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                    self.cap = cv2.VideoCapture(camera_index, backend)
                    if self.cap.isOpened():
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.cap.set(cv2.CAP_PROP_FPS, 60)
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        print(f"✅ Camera opened with backend: {backend}")
                        break
                    else:
                        if self.cap:
                            self.cap.release()
                
            if not self.cap or not self.cap.isOpened():
                self.cap = self.create_demo_video()
                print("Fallback to demo video")
                
            self.running = True
            self.status_label.config(text="● RUNNING", fg="green")
            self.frame_count = 0
            self.start_time = time.time()
            self.last_fps_update = time.time()
            
            self.root.after(1, self.monitor_loop)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
            self.stop_monitoring()
    
    def create_demo_video(self):
        cap = type('DemoCapture', (), {})()
        cap.frame_count = 0
        
        def read():
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            cv2.putText(frame, "DEMO MODE", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, "AquaSense-AI Monitoring", (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            x = (cap.frame_count * 5) % 500
            cv2.rectangle(frame, (x, 150), (x + 100, 250), (0, 255, 0), 2)
            
            cap.frame_count += 1
            return True, frame
        
        cap.read = read
        cap.isOpened = lambda: True
        cap.release = lambda: None
        cap.set = lambda prop, value: True
        
        return cap
            
    def monitor_loop(self):
        if not self.running:
            return
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                if self.config['mode'] == 'simulate':
                    if hasattr(self.cap, 'set'):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    if self.running:
                        self.root.after(1, self.monitor_loop)
                    return
                else:
                    if self.running:
                        self.root.after(1, self.monitor_loop)
                    return
            
            if frame is None:
                print("Warning: Received None frame")
                if self.running:
                    self.root.after(1, self.monitor_loop)
                return
                
            frame = cv2.resize(frame, (640, 480))
            
            detected = False
            annotated = frame.copy()
            
            try:
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                    
                annotated, detected, detections = self.detector.detect_frame(frame)
                
                if annotated is None:
                    annotated = frame.copy()
                    cv2.putText(annotated, "No Detection Output", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
            except Exception as e:
                annotated = frame.copy()
                cv2.putText(annotated, f"Detection Error", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                detected = False
            
            # FIXED: Perimeter monitoring with obstruction detection
            current_obstruction = False
            obstruction_percentage = 0
            current_time = time.time()
            
            if (self.config['mode'] == 'live' and 
                self.config.get('use_perimeter', False) and
                self.config.get('perimeter') and
                current_time - self.last_perimeter_check > self.perimeter_interval):
                
                try:
                    obstructed, percentage = self.config['perimeter'].check_obstruction(frame)
                    
                    # Obstruction threshold
                    current_obstruction = obstructed and percentage >= 40.0
                    obstruction_percentage = percentage
                    
                    if current_obstruction:
                        # Start or continue obstruction timing
                        if not self.obstruction_detected:
                            self.obstruction_start_time = current_time
                            self.obstruction_detected = True
                        self.obstruction_duration = current_time - self.obstruction_start_time
                        
                        # Add obstruction overlay
                        cv2.putText(annotated, f"PERIMETER OBSTRUCTED: {percentage:.1f}%", 
                                (10, annotated.shape[0] - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        # Reset obstruction if clear
                        self.obstruction_detected = False
                        self.obstruction_duration = 0
                    
                    self.last_perimeter_check = current_time
                except Exception as e:
                    print(f"Perimeter check error: {e}")
            
            # FIXED: Drowning detection tracking
            if detected:
                if not self.drowning_detected:
                    self.drowning_start_time = current_time
                    self.drowning_detected = True
                self.drowning_duration = current_time - self.drowning_start_time
            else:
                self.drowning_detected = False
                self.drowning_duration = 0
            
            # FIXED: PRIORITY ALERT SYSTEM - OBSTRUCTION HAS HIGHEST PRIORITY
            previous_alert_state = self.current_alert_state
            
            # Determine current alert state based on priority
            if self.obstruction_detected and self.obstruction_duration >= self.min_obstruction_duration:
                self.current_alert_state = "OBSTRUCTION"
            elif self.drowning_detected and self.drowning_duration >= self.min_drowning_duration:
                self.current_alert_state = "DROWNING"
            else:
                self.current_alert_state = "NONE"
            
            # FIXED: Send Bluetooth alerts based on priority
            if self.config.get('bluetooth_connected') and self.config.get('bluetooth'):
                # Only send alert if state changed or enough time has passed
                if (self.current_alert_state != previous_alert_state or 
                    current_time - self.last_alert_update > 1.0):
                    
                    if self.current_alert_state == "OBSTRUCTION":
                        # OBSTRUCTION HAS PRIORITY - send obstruction alert
                        self.config['bluetooth'].send_obstruction_alert()
                        print("🚨 OBSTRUCTION ALERT SENT (Priority)")
                        
                        # Update UI
                        self.obstruction_alert_label.config(
                            text=f"Obstruction: ALERT ({self.obstruction_duration:.1f}s)", 
                            foreground="red"
                        )
                        self.drowning_alert_label.config(
                            text="Drowning: OVERRIDDEN (Obstruction Priority)", 
                            foreground="orange"
                        )
                        self.current_alert_label.config(
                            text=f"Active: Obstruction ({self.obstruction_duration:.1f}s)", 
                            foreground="red"
                        )
                        
                    elif self.current_alert_state == "DROWNING":
                        # Only send drowning alert if no obstruction
                        self.config['bluetooth'].send_drowning_alert()
                        print("🚨 DROWNING ALERT SENT")
                        
                        # Update UI
                        self.drowning_alert_label.config(
                            text=f"Drowning: ALERT ({self.drowning_duration:.1f}s)", 
                            foreground="red"
                        )
                        self.obstruction_alert_label.config(
                            text="Obstruction: No Alert", 
                            foreground="green"
                        )
                        self.current_alert_label.config(
                            text=f"Active: Drowning ({self.drowning_duration:.1f}s)", 
                            foreground="red"
                        )
                        
                    else:
                        # Clear all alerts
                        self.config['bluetooth'].send_clear_alert()
                        print("✅ ALL ALERTS CLEARED")
                        
                        # Update UI
                        self.drowning_alert_label.config(
                            text="Drowning: No Alert", 
                            foreground="green"
                        )
                        self.obstruction_alert_label.config(
                            text="Obstruction: No Alert", 
                            foreground="green"
                        )
                        self.current_alert_label.config(
                            text="Active: None", 
                            foreground="blue"
                        )
                    
                    self.last_alert_update = current_time
            
            # FIXED: Update main status label with priority indication
            if self.current_alert_state == "OBSTRUCTION":
                status_text = f"● PRIORITY: PERIMETER OBSTRUCTED ({self.obstruction_duration:.1f}s)"
                status_color = "red"
                
                # Add priority indicator to frame
                cv2.putText(annotated, "PRIORITY: OBSTRUCTION ALERT", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                
            elif self.current_alert_state == "DROWNING":
                status_text = f"● ALERT: DROWNING DETECTED ({self.drowning_duration:.1f}s)"
                status_color = "red"
                
                cv2.putText(annotated, "ALERT: DROWNING DETECTED", (50, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                
            else:
                status_text = "● MONITORING: NORMAL"
                status_color = "green"
            
            self.status_label.config(text=status_text, fg=status_color)
            
            # Draw perimeter if enabled and visible
            if (self.config['mode'] == 'live' and 
                self.config.get('use_perimeter', False) and
                self.config.get('perimeter') and
                self.config['perimeter'].drawing_complete and
                hasattr(self, 'show_perimeter') and self.show_perimeter):
                
                try:
                    annotated = self.config['perimeter'].draw_perimeter_on_frame(annotated)
                except Exception as e:
                    print(f"Perimeter drawing error: {e}")
            
            # Update FPS
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.last_fps_update >= 1.0:
                self.fps = self.frame_count / (current_time - self.last_fps_update)
                self.fps_label.config(text=f"FPS: {self.fps:.1f}")
                self.frame_count = 0
                self.last_fps_update = current_time
            
            # Update detection and obstruction counts in UI
            if detected:
                self.detection_label.config(text=f"Detections: {int(self.drowning_duration)}s")
            if self.obstruction_detected:
                self.obstruction_label.config(text=f"Obstructions: {int(self.obstruction_duration)}s")
            
            # Convert for display
            try:
                if annotated is None:
                    annotated = frame.copy()
                
                if annotated.dtype != np.uint8:
                    annotated = annotated.astype(np.uint8)
                    
                frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (800, 600))
                img = Image.fromarray(frame_resized)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.config(image=imgtk, text="")
                self.video_label.image = imgtk
                
            except Exception as e:
                error_frame = np.zeros((600, 800, 3), dtype=np.uint8)
                cv2.putText(error_frame, f"Display Error", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                img = Image.fromarray(error_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.config(image=imgtk, text="")
                self.video_label.image = imgtk
            
            if self.running:
                self.root.after(1, self.monitor_loop)
            
        except Exception as e:
            print(f"Monitoring loop error: {e}")
            if self.running:
                self.root.after(1, self.monitor_loop)
            
    def stop_monitoring(self):
        print("🛑 Stopping monitoring and cleaning up resources...")
        self.running = False
        
        if self.config.get('bluetooth_connected') and self.config.get('bluetooth'):
            try:
                self.config['bluetooth'].send_clear_alert()
                self.config['bluetooth'].disconnect()
            except Exception as e:
                print(f"Error clearing Bluetooth alerts: {e}")
            
        if self.cap and hasattr(self.cap, 'release'):
            try:
                self.cap.release()
            except Exception as e:
                print(f"Error releasing capture: {e}")
                
        if hasattr(self, 'detector') and self.detector:
            try:
                if hasattr(self.detector, 'cleanup'):
                    self.detector.cleanup()
                del self.detector
            except Exception as e:
                print(f"Error cleaning up detector: {e}")
        
        force_system_cleanup()
                
        try:
            self.root.destroy()
        except Exception as e:
            print(f"Error destroying window: {e}")
            
        try:
            menu = MainMenu()
            menu.show()
        except Exception as e:
            print(f"Error returning to main menu: {e}")
        
    def show(self):
        self.root.after(100, self.start_monitoring)
        self.root.mainloop()

def main():
    force_system_cleanup()
    
    splash = SplashScreen()
    splash.run_loading()
    splash.close()
    
    menu = MainMenu()
    menu.show()

if __name__ == "__main__":
    main()