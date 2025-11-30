# detect.py - MAXIMUM PERFORMANCE VERSION WITH TRACKING
import cv2
import numpy as np
import time
import threading
from queue import Queue
import gc

class RealtimeDetector:
    """
    Maximum performance YOLO detector for 12th Gen Intel i5-12450H with tracking
    """
    def __init__(self, model_path: str, conf: float = 0.5):
        self.conf = conf
        self.last_event_time = 0
        self.event_hold_seconds = 1.0
        
        # MAXIMUM PERFORMANCE - NO THROTTLING
        self.frame_skip = 0  # Process EVERY frame
        self.frame_counter = 0
        self.last_detection_time = 0
        
        # Tracking state management
        self.tracking_states = {}  # Dictionary to track each ID's behavior over time
        self.max_track_history = 30  # Keep last 30 positions for each track
        
        # Optimized threading
        self.detection_queue = Queue(maxsize=3)  # Increased buffer
        self.result_queue = Queue(maxsize=3)
        self.processing = False
        self.current_frame = None
        
        # Initialize with a default frame
        self.last_valid_result = self._create_default_result()
        
        # HARDWARE-SPECIFIC OPTIMIZATION
        print(f"🚀 MAXIMUM PERFORMANCE MODE - Intel i5-12450H")
        print(f"🔧 Loading YOLO model: {model_path}")
        
        try:
            from ultralytics import YOLO
            import torch
            
            # Load model with hardware optimization
            self.model = YOLO(model_path)
            
            # AGGRESSIVE HARDWARE UTILIZATION
            if torch.cuda.is_available():
                # NVIDIA GPU
                self.model = self.model.cuda()
                torch.backends.cudnn.benchmark = True  # Optimize CUDA
                torch.set_grad_enabled(False)  # Disable gradients for inference
                print("✅ USING NVIDIA CUDA GPU - MAXIMUM PERFORMANCE")
                
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # Apple Silicon
                self.model = self.model.to('mps')
                print("✅ USING APPLE MPS GPU")
                
            else:
                # INTEL CPU OPTIMIZATION - Your hardware
                # Use all CPU cores and optimize for Intel - FIXED COMPATIBILITY
                import multiprocessing as mp
                torch.set_num_threads(mp.cpu_count())  # Use ALL cores
                
                # Try FP16 for CPU if supported, otherwise use FP32
                try:
                    self.model = self.model.half()  # FP16 for CPU
                    print("✅ Using FP16 precision for CPU")
                except:
                    self.model = self.model.float()
                    print("✅ Using FP32 precision for CPU")
                
                # FIXED: Updated MKL-DNN configuration for newer PyTorch versions
                try:
                    # Newer PyTorch versions use different API
                    if hasattr(torch.backends, 'mkldnn'):
                        torch.backends.mkldnn.enabled = True
                    print("✅ Intel MKL-DNN optimization enabled")
                except Exception as e:
                    print(f"⚠️ MKL-DNN optimization not available: {e}")
                
                print(f"✅ USING INTEL CPU OPTIMIZATION - {mp.cpu_count()} CORES")
            
            self.names = getattr(self.model, 'names', {})
            self.using_yolo = True
            print(f"✅ YOLO model loaded and optimized for Intel i5-12450H")
            
            # Start HIGH PERFORMANCE background processing
            self.start_processing_thread()
            
        except Exception as e:
            print(f"❌ CRITICAL: YOLO initialization failed: {e}")
            raise RuntimeError(f"Cannot initialize YOLO detector: {e}")
    
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
    
    def _update_tracking_states(self, detections, frame_shape):
        """
        Update tracking states with new detections for behavioral analysis
        """
        current_time = time.time()
        
        for detection in detections:
            track_id = detection.get('track_id')
            if track_id is not None:
                # Initialize or update tracking state for this ID
                if track_id not in self.tracking_states:
                    self.tracking_states[track_id] = {
                        'first_seen': current_time,
                        'positions': [],
                        'last_update': current_time,
                        'vertical_count': 0,
                        'motionless_count': 0,
                        'drowning_alert_sent': False
                    }
                
                # Update position history
                state = self.tracking_states[track_id]
                box = detection.get('box', [])
                if len(box) == 4:
                    x1, y1, x2, y2 = box
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    # Add current position to history
                    state['positions'].append((center_x, center_y, current_time))
                    
                    # Keep only recent history
                    if len(state['positions']) > self.max_track_history:
                        state['positions'].pop(0)
                    
                    # BEHAVIORAL ANALYSIS: Check for vertical/still behavior
                    self._analyze_behavior(state, detection, frame_shape)
                
                state['last_update'] = current_time
        
        # Clean up old tracks (remove tracks not seen for 5 seconds)
        current_time = time.time()
        expired_tracks = [
            track_id for track_id, state in self.tracking_states.items()
            if current_time - state['last_update'] > 5.0
        ]
        for track_id in expired_tracks:
            del self.tracking_states[track_id]
    
    def _analyze_behavior(self, state, detection, frame_shape):
        """
        Analyze behavior for drowning detection based on tracking history
        """
        if len(state['positions']) < 2:
            return
        
        # Calculate motion metrics
        recent_positions = state['positions'][-10:]  # Last 10 positions
        if len(recent_positions) < 2:
            return
        
        # Calculate movement (distance traveled)
        total_movement = 0
        for i in range(1, len(recent_positions)):
            x1, y1, t1 = recent_positions[i-1]
            x2, y2, t2 = recent_positions[i]
            distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            total_movement += distance
        
        # Check for motionlessness (little movement)
        motion_threshold = 20.0  # pixels over last 10 frames
        if total_movement < motion_threshold:
            state['motionless_count'] += 1
        else:
            state['motionless_count'] = max(0, state['motionless_count'] - 1)
        
        # Check for vertical position (near bottom of frame)
        box = detection.get('box', [])
        if len(box) == 4:
            x1, y1, x2, y2 = box
            frame_height = frame_shape[0]
            bottom_threshold = frame_height * 0.8  # Bottom 20% of frame
            
            if y2 > bottom_threshold:
                state['vertical_count'] += 1
            else:
                state['vertical_count'] = max(0, state['vertical_count'] - 1)
        
        # Drowning detection logic based on behavioral patterns
        motionless_frames_threshold = 15  # 15 frames of motionlessness
        vertical_frames_threshold = 15    # 15 frames in vertical position
        
        if (state['motionless_count'] >= motionless_frames_threshold and 
            state['vertical_count'] >= vertical_frames_threshold and
            not state['drowning_alert_sent']):
            
            # Trigger drowning alert for this specific track
            detection['behavioral_drowning'] = True
            state['drowning_alert_sent'] = True
            print(f"🚨 BEHAVIORAL ALERT: Track ID {list(self.tracking_states.keys()).index(state) + 1} "
                  f"- Motionless: {state['motionless_count']} frames, "
                  f"Vertical: {state['vertical_count']} frames")
    
    def start_processing_thread(self):
        """Start HIGH PERFORMANCE background thread"""
        if not self.using_yolo:
            return
            
        self.processing = True
        self.processing_thread = threading.Thread(
            target=self._processing_loop, 
            daemon=True,
            name="YOLO_Processing_Thread"
        )
        self.processing_thread.start()
        print("✅ Started high-performance detection thread")
    
    def _processing_loop(self):
        """MAXIMUM PERFORMANCE processing loop with tracking"""
        import torch
        batch_frames = []
        batch_size = 4  # Process multiple frames for better GPU utilization
        
        while self.processing:
            try:
                # Batch processing for better GPU utilization
                while len(batch_frames) < batch_size and not self.detection_queue.empty():
                    frame = self.detection_queue.get_nowait()
                    if frame is not None:
                        batch_frames.append(frame)
                
                if batch_frames:
                    start_time = time.time()
                    
                    try:
                        # BATCH PROCESSING with TRACKING for maximum GPU utilization
                        results = self.model.track(
                            batch_frames, 
                            conf=self.conf, 
                            verbose=False, 
                            batch=batch_size,
                            persist=True,  # Maintain tracks between frames
                            tracker="bytetrack.yaml"  # Use ByteTrack algorithm
                        )
                        processing_time = time.time() - start_time
                        
                        # Process each result in batch
                        for i, r in enumerate(results):
                            if i < len(batch_frames):
                                annotated = r.plot()
                                detections = []
                                detected_flag = False

                                try:
                                    # Extract tracking information
                                    track_ids = r.boxes.id.cpu().numpy().astype(int) if hasattr(r.boxes, 'id') and r.boxes.id is not None else []
                                    boxes = r.boxes.xyxy.cpu().numpy() if hasattr(r.boxes, 'xyxy') else []
                                    confs = r.boxes.conf.cpu().numpy() if hasattr(r.boxes, 'conf') else []
                                    clss = r.boxes.cls.cpu().numpy() if hasattr(r.boxes, 'cls') else []
                                    
                                    for idx, (box, conf, cls) in enumerate(zip(boxes, confs, clss)):
                                        cls = int(cls)
                                        name = self.names.get(cls, str(cls))
                                        
                                        # Get track ID if available
                                        track_id = track_ids[idx] if idx < len(track_ids) else None
                                        
                                        detection_data = {
                                            'cls': cls,
                                            'name': name,
                                            'conf': float(conf),
                                            'box': [float(x) for x in box],
                                            'track_id': track_id
                                        }
                                        
                                        # Add tracking visualization if available
                                        if track_id is not None:
                                            detection_data['track_id_display'] = f"ID:{track_id}"
                                        
                                        detections.append(detection_data)
                                        
                                        # Check for drowning detection (both direct and behavioral)
                                        if name.lower() == 'drowning' or name.lower().startswith('drown'):
                                            detected_flag = True
                                            detection_data['drowning_detected'] = True
                                    
                                    # Update tracking states for behavioral analysis
                                    if detections:
                                        self._update_tracking_states(detections, batch_frames[i].shape)
                                    
                                    # Check for behavioral drowning alerts
                                    for detection in detections:
                                        if detection.get('behavioral_drowning', False):
                                            detected_flag = True
                                            detection['drowning_detected'] = True
                                            
                                except Exception as e:
                                    print(f"⚠️ Detection processing error: {e}")
                                    annotated = batch_frames[i].copy()
                                    cv2.putText(annotated, f"Processing Error", (10, 30),
                                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                                # Ensure annotated is not None
                                if annotated is None:
                                    annotated = batch_frames[i].copy()
                                    cv2.putText(annotated, "No detection result", (10, 30),
                                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                                # Add tracking information to annotated frame
                                for detection in detections:
                                    if 'track_id_display' in detection:
                                        box = detection.get('box', [])
                                        if len(box) == 4:
                                            x1, y1, x2, y2 = map(int, box)
                                            track_text = detection['track_id_display']
                                            
                                            # Draw track ID
                                            cv2.putText(annotated, track_text, (x1, y1 - 30),
                                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                                            
                                            # Add behavioral status if applicable
                                            if detection.get('behavioral_drowning', False):
                                                cv2.putText(annotated, "BEHAVIOR ALERT!", (x1, y1 - 50),
                                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

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
                        
                        # Performance monitoring
                        fps = len(batch_frames) / processing_time if processing_time > 0 else 0
                        if processing_time > 0.1:
                            print(f"⚡ Batch processed {len(batch_frames)} frames in {processing_time:.3f}s ({fps:.1f} FPS)")
                            
                    except Exception as e:
                        print(f"❌ Batch detection error: {e}")
                        error_frame = self._create_error_frame(f"Batch Error: {str(e)[:50]}")
                        self.last_valid_result = (error_frame, False, [])
                    
                    finally:
                        batch_frames.clear()
                        # Aggressive optimization
                        if processing_time > 0.2:
                            gc.collect()
                            
            except Exception as e:
                print(f"⚠️ Processing loop error: {e}")
                time.sleep(0.001)  # Minimal sleep for maximum responsiveness
    
    def detect_frame(self, frame):
        """MAXIMUM PERFORMANCE frame detection - NO LIMITS"""
        if frame is None:
            return self.last_valid_result
            
        # SUBMIT FRAME IMMEDIATELY - NO THROTTLING
        if self.using_yolo:
            if self.detection_queue.qsize() < 3:  # Allow buffering
                try:
                    self.detection_queue.put_nowait(frame)
                except:
                    pass  # Queue full, continue with last result
            
            return self.last_valid_result
        else:
            # This should never happen with demo detector removed
            error_frame = self._create_error_frame("YOLO NOT AVAILABLE")
            return (error_frame, False, [])
    
    def detect_frame_with_perimeter(self, frame, perimeter_mask=None):
        """
        MAXIMUM PERFORMANCE perimeter-filtered detection with tracking
        """
        if frame is None:
            return self.last_valid_result
            
        # Run standard detection first
        annotated, detected, detections = self.detect_frame(frame)
        
        # If no perimeter mask or no detections, return original result
        if perimeter_mask is None or not detections:
            return annotated, detected, detections
        
        # Filter detections to only those inside perimeter
        filtered_detections = []
        filtered_detected = False
        
        for detection in detections:
            if self._is_detection_in_perimeter(detection, perimeter_mask):
                filtered_detections.append(detection)
                # Check if it's a drowning detection (both direct and behavioral)
                if (detection.get('name', '').lower().startswith('drown') or 
                    detection.get('drowning_detected', False) or
                    detection.get('behavioral_drowning', False)):
                    filtered_detected = True
        
        # Update annotated frame to show only perimeter detections
        if filtered_detections != detections:
            annotated = self._redraw_detections_in_perimeter(frame, filtered_detections, perimeter_mask)
        
        return annotated, filtered_detected, filtered_detections

    def _is_detection_in_perimeter(self, detection, perimeter_mask):
        """
        Check if detection bounding box is inside perimeter
        """
        try:
            box = detection.get('box', [])
            if len(box) != 4:
                return False
                
            x1, y1, x2, y2 = map(int, box)
            
            # Check if center point of bounding box is inside perimeter
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            # Ensure coordinates are within mask bounds
            if (0 <= center_y < perimeter_mask.shape[0] and 
                0 <= center_x < perimeter_mask.shape[1]):
                return perimeter_mask[center_y, center_x] > 0
            
            return False
            
        except Exception as e:
            print(f"Perimeter check error: {e}")
            return False

    def _redraw_detections_in_perimeter(self, frame, detections, perimeter_mask):
        """
        Redraw only detections that are inside perimeter with tracking info
        """
        annotated = frame.copy()
        
        for detection in detections:
            box = detection.get('box', [])
            name = detection.get('name', '')
            conf = detection.get('conf', 0)
            track_id = detection.get('track_id')
            
            if len(box) == 4:
                x1, y1, x2, y2 = map(int, box)
                
                # Determine color based on alert type
                if detection.get('behavioral_drowning', False):
                    color = (0, 165, 255)  # Orange for behavioral alerts
                elif 'drown' in name.lower() or detection.get('drowning_detected', False):
                    color = (0, 0, 255)  # Red for direct drowning detection
                else:
                    color = (0, 255, 0)  # Green for normal detections
                
                # Draw bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
                # Draw label with tracking info
                label = f"{name} {conf:.2f}"
                if track_id is not None:
                    label = f"ID:{track_id} {label}"
                
                cv2.putText(annotated, label, (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Add behavioral alert text if applicable
                if detection.get('behavioral_drowning', False):
                    cv2.putText(annotated, "BEHAVIOR ALERT!", (x1, y1-30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Add perimeter status text
        cv2.putText(annotated, "PERIMETER FILTER: ACTIVE", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return annotated
    
    def cleanup(self):
        """AGGRESSIVE resource cleanup"""
        print("🧹 MAXIMUM CLEANUP: Releasing all detector resources...")
        self.processing = False
        
        # Clear tracking states
        self.tracking_states.clear()
        
        # Wait for processing thread to finish
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join(timeout=1.0)
        
        # CLEAR ALL QUEUES
        while not self.detection_queue.empty():
            try:
                self.detection_queue.get_nowait()
            except:
                break
                
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except:
                break
        
        # AGGRESSIVE MEMORY CLEANUP
        if hasattr(self, 'model'):
            try:
                del self.model
            except:
                pass
        
        # FORCE GARBAGE COLLECTION
        for i in range(5):
            gc.collect()
            
        # CLEAR GPU MEMORY
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                print("✅ CUDA memory cleared")
        except:
            pass
            
        print("✅ MAXIMUM CLEANUP COMPLETED")