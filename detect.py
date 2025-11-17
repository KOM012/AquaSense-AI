# detect.py - FIXED VERSION
import cv2
import numpy as np
import time
import threading
from queue import Queue
import gc

class RealtimeDetector:
    """
    Fixed YOLO detector with proper None handling
    """
    def __init__(self, model_path: str, conf: float = 0.5, target_fps: int = 15):
        self.conf = conf
        self.target_fps = target_fps
        self.last_event_time = 0
        self.event_hold_seconds = 1.0
        
        # Performance optimization settings
        self.frame_skip = 2  # Process every 3rd frame
        self.frame_counter = 0
        self.last_detection_time = 0
        self.min_processing_interval = 1.0 / target_fps
        
        # Threading for async processing
        self.detection_queue = Queue(maxsize=1)
        self.result_queue = Queue(maxsize=1)
        self.processing = False
        self.current_frame = None
        
        # Initialize with a default frame
        self.last_valid_result = self._create_default_result()
        
        try:
            from ultralytics import YOLO
            print(f"Loading YOLO model: {model_path}")
            
            self.model = YOLO(model_path)
            
            # Reduce model precision for faster inference
            try:
                self.model = self.model.half()
                print("Using half precision for faster inference")
            except:
                print("Half precision not available, using full precision")
            
            self.names = getattr(self.model, 'names', {})
            self.using_yolo = True
            print(f"✅ YOLO model loaded: {model_path}")
            
            # Start background processing thread
            self.start_processing_thread()
            
        except ImportError:
            from demo_detector import DemoDetector
            self.demo_detector = DemoDetector(model_path, conf)
            self.using_yolo = False
            print("Using demo detector (YOLO not available)")
    
    def _create_default_result(self):
        """Create a default result with a blank frame"""
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "INITIALIZING...", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return (blank_frame, False, [])
    
    def _create_error_frame(self, message):
        """Create an error frame"""
        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_frame, message, (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return error_frame
    
    def start_processing_thread(self):
        """Start background thread for async detection"""
        if not self.using_yolo:
            return
            
        self.processing = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        print("Started background detection thread")
    
    def _processing_loop(self):
        """Background processing loop"""
        while self.processing:
            try:
                if not self.detection_queue.empty():
                    frame = self.detection_queue.get_nowait()
                    
                    if frame is None:
                        continue
                    
                    # Run detection
                    try:
                        start_time = time.time()
                        results = self.model(frame, conf=self.conf, verbose=False)
                        processing_time = time.time() - start_time
                        
                        r0 = results[0]
                        annotated = r0.plot()
                        detections = []
                        detected_flag = False

                        try:
                            boxes = r0.boxes.xyxy.cpu().numpy() if hasattr(r0.boxes, 'xyxy') else []
                            confs = r0.boxes.conf.cpu().numpy() if hasattr(r0.boxes, 'conf') else []
                            clss = r0.boxes.cls.cpu().numpy() if hasattr(r0.boxes, 'cls') else []
                            
                            for box, conf, cls in zip(boxes, confs, clss):
                                cls = int(cls)
                                name = self.names.get(cls, str(cls))
                                detections.append({
                                    'cls': cls,
                                    'name': name,
                                    'conf': float(conf),
                                    'box': [float(x) for x in box]
                                })
                                
                                if name.lower() == 'drowning' or name.lower().startswith('drown'):
                                    detected_flag = True
                                    
                        except Exception as e:
                            print(f"Detection processing error: {e}")
                            # Create a fallback annotated frame
                            annotated = frame.copy()
                            cv2.putText(annotated, f"Processing Error: {str(e)}", (10, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                        # Ensure annotated is not None
                        if annotated is None:
                            annotated = frame.copy()
                            cv2.putText(annotated, "No detection result", (10, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                        # Temporal smoothing
                        now = time.time()
                        if detected_flag:
                            self.last_event_time = now

                        if (now - self.last_event_time) <= self.event_hold_seconds:
                            detected_flag = True
                        else:
                            detected_flag = False
                        
                        # Store result
                        self.last_valid_result = (annotated, detected_flag, detections)
                        self.last_detection_time = now
                        
                        # Force garbage collection
                        if processing_time > 0.1:
                            gc.collect()
                            
                    except Exception as e:
                        print(f"Detection error: {e}")
                        error_frame = self._create_error_frame(f"Detection Error: {str(e)}")
                        self.last_valid_result = (error_frame, False, [])
                        
            except Exception as e:
                print(f"Processing loop error: {e}")
                time.sleep(0.01)
    
    def detect_frame(self, frame):
        """Optimized frame detection with frame skipping and error handling"""
        if frame is None:
            return self.last_valid_result
            
        current_time = time.time()
        
        # Skip frames if processing is too slow
        if current_time - self.last_detection_time < self.min_processing_interval:
            return self.last_valid_result
        
        self.frame_counter += 1
        
        if self.using_yolo:
            # Use frame skipping for large models
            if self.frame_counter % (self.frame_skip + 1) != 0:
                return self.last_valid_result
            
            # Submit frame for async processing
            if self.detection_queue.empty():
                try:
                    self.detection_queue.put_nowait(frame)
                except:
                    pass  # Queue full, skip this frame
            
            return self.last_valid_result
        else:
            # Fallback to demo detector with error handling
            try:
                return self.demo_detector.detect_frame(frame)
            except Exception as e:
                print(f"Demo detector error: {e}")
                return self.last_valid_result
    
    def cleanup(self):
        """Cleanup resources"""
        self.processing = False
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join(timeout=1.0)
        gc.collect()