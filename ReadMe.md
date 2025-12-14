<p align="center"><img 
width="250"
height="250"
style="object-fit: contain;" 
alt="AquaSenseAI" 
src="https://github.com/user-attachments/assets/28c37a23-736b-4c86-8fdc-acdca0e66120" 
/><p></p>

## System Overview<br>
**AquaSense-AI** is a comprehensive drowning detection system that combines computer vision, machine learning, and hardware integration for aquatic safety monitoring. The system operates in two primary modes: Simulation Mode (pre-recorded video analysis) and Live Mode (real-time camera monitoring).

**Hardware Integration**<br>
Computer Vision: Webcam/Camera input<br>
Alert System: Arduino-controlled LED and buzzer via Bluetooth<br>
Processing: Optimized for Intel i5-12450H (CPU/GPU)

**Application Startup**
1. **Splash Screen** (`SplashScreen` class)<br>
   ├── System cleanup (`force_system_cleanup()`)<br>
   ├── Port checking (`cleanup_ports()`)<br>
   └── Progress bar with initialization steps

2. **Main Menu** (`MainMenu` class)<br>
   ├── Simulate Mode (video file processing)<br>
   └── Live Mode (camera monitoring)
---------------------------------------------
3. **Setup Screen** (SetupScreen class)<br>
   ├── Mode-specific configuration<br>
   │   ├── Simulate Mode: Video file selection<br>
   │   └── Live Mode: Camera selection + Perimeter setup<br>
   ├── AI Model configuration<br>
   ├── Bluetooth pairing (optional)<br>
   └── Preview functionality
--------------------------------------------
4. **Monitor Screen** (MonitorScreen class) - MAIN OPERATION<br>
   ├── Detector initialization (RealtimeDetector)<br>
   ├── Dual-thread processing:<br>
   │   ├── Main thread: GUI updates, FPS calculation<br>
   │   └── Background thread: YOLO inference + tracking<br>
   ├── Dual alert system:<br>
   │   ├── Drowning detection (YOLO + behavioral analysis)<br>
   │   └── Perimeter obstruction (background subtraction)<br>
   └── Priority-based alert management<br>
--------------------------------------------
**Alert Processing**<br>
5. Alert Priority Hierarchy (FIXED in MonitorScreen)<br>
   └── OBSTRUCTION (Highest Priority) > DROWNING > NONE
   
6. Alert Transmission<br>
   └── Python → Serial → Arduino → LED/Buzzer<br>
       ├── Command 0: Clear all alerts<br>
       ├── Command 1: Drowning alert (continuous)<br>
       └── Command 2: Obstruction alert (pulsing)

**System Flow Diagram**<br>
  [Camera/Video]&nbsp;&nbsp;&nbsp;&nbsp;→&nbsp;&nbsp;&nbsp;&nbsp;[Frame Capture]&nbsp;&nbsp;&nbsp;&nbsp;→&nbsp;&nbsp;&nbsp;&nbsp;[Dual Processing]<br>
        ↓&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ↓<br>
[Perimeter Analysis]&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [YOLO Detection]<br>
        ↓&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓<br>
[Obstruction %]&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [Drowning Detection]<br>
        ↓&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓<br>
[Priority Decision]&nbsp;&nbsp;←&nbsp;&nbsp;←&nbsp;&nbsp;←&nbsp;&nbsp;←&nbsp;&nbsp;←&nbsp;&nbsp;←&nbsp;&nbsp;[Behavioral Analysis]<br>
 &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
[Alert State Machine]<br>
 &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
[Bluetooth Transmission]<br>
 &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
[Arduino Hardware]<br>
 &nbsp;&nbsp;&nbsp;&nbsp;↓<br>
[LED/Buzzer Output]<br>


**Dependencies**<br>
Python 3.8+<br>
OpenCV, PyTorch, Ultralytics YOLO<br>
Tkinter, PIL, NumPy<br>
pyserial for Bluetooth
