**System Overview**
**AquaSense-AI** is a comprehensive drowning detection system that combines computer vision, machine learning, and hardware integration for aquatic safety monitoring. The system operates in two primary modes: Simulation Mode (pre-recorded video analysis) and Live Mode (real-time camera monitoring).

**Hardware Integration**
Computer Vision: Webcam/Camera input
Alert System: Arduino-controlled LED and buzzer via Bluetooth
Processing: Optimized for Intel i5-12450H (CPU/GPU)

**Application Startup**
1. Splash Screen (SplashScreen class)
   ├── System cleanup (force_system_cleanup())
   ├── Port checking (cleanup_ports())
   └── Progress bar with initialization steps

2. Main Menu (MainMenu class)
   ├── Simulate Mode (video file processing)
   └── Live Mode (camera monitoring)
---------------------------------------------
**Setup Config**
3. Setup Screen (SetupScreen class)
   ├── Mode-specific configuration
   │   ├── Simulate Mode: Video file selection
   │   └── Live Mode: Camera selection + Perimeter setup
   ├── AI Model configuration
   ├── Bluetooth pairing (optional)
   └── Preview functionality
--------------------------------------------
**Monitoring Execution**
4. Monitor Screen (MonitorScreen class) - MAIN OPERATION
   ├── Detector initialization (RealtimeDetector)
   ├── Dual-thread processing:
   │   ├── Main thread: GUI updates, FPS calculation
   │   └── Background thread: YOLO inference + tracking
   ├── Dual alert system:
   │   ├── Drowning detection (YOLO + behavioral analysis)
   │   └── Perimeter obstruction (background subtraction)
   └── Priority-based alert management
--------------------------------------------
**Alert Processing**
5. Alert Priority Hierarchy (FIXED in MonitorScreen)
   └── OBSTRUCTION (Highest Priority) > DROWNING > NONE
   
6. Alert Transmission
   └── Python → Serial → Arduino → LED/Buzzer
       ├── Command 0: Clear all alerts
       ├── Command 1: Drowning alert (continuous)
       └── Command 2: Obstruction alert (pulsing)

**System Flow Diagram**
  [Camera/Video]   →   [Frame Capture]   →   [Dual Processing]
        ↓                                            ↓
[Perimeter Analysis]                         [YOLO Detection]
        ↓                                            ↓
[Obstruction %]                             [Drowning Detection]
        ↓                                            ↓
[Priority Decision]  ←   ←   ←   ←   ←   ← [Behavioral Analysis]
        ↓
[Alert State Machine]
        ↓
[Bluetooth Transmission]
        ↓
[Arduino Hardware]
        ↓
[LED/Buzzer Output]


**Dependencies**
Python 3.8+
OpenCV, PyTorch, Ultralytics YOLO
Tkinter, PIL, NumPy
pyserial for Bluetooth
