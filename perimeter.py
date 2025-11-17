# core/perimeter.py - WITH HIDDEN PERIMETER OPTION
import cv2
import numpy as np
import time
import threading
from typing import Callable, Tuple, Optional

class PerimeterMonitor:
    """
    Perimeter monitoring system with hidden mode option
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        
        # State variables
        self.reference_frame = None
        self.perimeter_points = []
        self.mask = None
        self.drawing_complete = False
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.stop_flag = threading.Event()
        self.lock = threading.Lock()
        
        # Detection state
        self.obstruction_detected = False
        self.current_obstruction_pct = 0.0
        self.obstruction_callback = None
        
        # Thresholds
        self.obstruction_threshold = 80.0  # percentage
        self.check_interval = 0.3  # seconds between checks
        
        # Display settings
        self.visible = True  # Set to False to hide perimeter overlay
        self.show_detection_boxes = True  # Show bounding boxes on obstructions
        
        # Background subtraction parameters
        self.min_contour_area = 1500  # Minimum contour area to consider as obstruction
        self.difference_threshold = 45  # Pixel difference threshold
    
    def set_visible(self, visible: bool):
        """
        Set whether the perimeter overlay is visible
        """
        self.visible = visible
        if self.logger:
            status = "visible" if visible else "hidden"
            self.logger.info(f"Perimeter overlay set to {status}")
    
    def set_show_detection_boxes(self, show: bool):
        """
        Set whether to show detection boxes on obstructions
        """
        self.show_detection_boxes = show
        if self.logger:
            status = "shown" if show else "hidden"
            self.logger.info(f"Detection boxes set to {status}")
    
    def draw_perimeter_interactive(self, frame, window_name="Draw Perimeter"):
        """
        Interactive perimeter drawing - with visibility option
        """
        self.reset()
        
        temp_frame = frame.copy()
        drawing_active = True
        perimeter_complete = False
        
        def mouse_callback(event, x, y, flags, param):
            nonlocal temp_frame
            
            if event == cv2.EVENT_LBUTTONDOWN:
                self.perimeter_points.append((x, y))
                temp_frame = frame.copy()
                self._draw_points_on_frame(temp_frame, closed=False)
                cv2.imshow(window_name, temp_frame)
                if self.logger:
                    self.logger.info(f"Point {len(self.perimeter_points)}: ({x}, {y})")
            
            elif event == cv2.EVENT_RBUTTONDOWN:
                if len(self.perimeter_points) >= 3:
                    temp_frame = frame.copy()
                    self._draw_points_on_frame(temp_frame, closed=True)
                    cv2.imshow(window_name, temp_frame)
                    if self.logger:
                        self.logger.info("Perimeter closed - Press ENTER to confirm")
        
        # Setup window
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, mouse_callback)
        
        # Draw instructions
        self._draw_instructions(temp_frame)
        cv2.imshow(window_name, temp_frame)
        
        # Wait for user input
        while drawing_active:
            key = cv2.waitKey(50) & 0xFF
            
            if key == 27:  # ESC - Cancel
                if self.logger:
                    self.logger.warning("Perimeter drawing cancelled")
                perimeter_complete = False
                drawing_active = False
            
            elif key == 13:  # ENTER - Confirm
                if len(self.perimeter_points) >= 3:
                    self._finalize_perimeter(frame)
                    perimeter_complete = True
                    drawing_active = False
                    if self.logger:
                        self.logger.info(f"Perimeter set with {len(self.perimeter_points)} points")
                else:
                    if self.logger:
                        self.logger.warning("Need at least 3 points")
        
        cv2.destroyWindow(window_name)
        return perimeter_complete
    
    def _draw_instructions(self, frame):
        """Draw instruction overlay"""
        instructions = [
            "LEFT-CLICK: Add perimeter point",
            "RIGHT-CLICK: Close polygon (min 3)",
            "ENTER: Confirm | ESC: Cancel",
            f"Points placed: {len(self.perimeter_points)}"
        ]
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (450, 130), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw text
        y_offset = 25
        for i, text in enumerate(instructions):
            color = (0, 255, 255) if i < 3 else (255, 255, 0)
            cv2.putText(frame, text, (10, y_offset + i*25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    def _draw_points_on_frame(self, frame, closed=False):
        """Draw perimeter points and lines"""
        if len(self.perimeter_points) == 0:
            return
        
        # Draw lines
        for i in range(len(self.perimeter_points) - 1):
            cv2.line(frame, self.perimeter_points[i], 
                    self.perimeter_points[i+1], (0, 255, 0), 2)
        
        # Close polygon if requested
        if closed and len(self.perimeter_points) >= 3:
            cv2.line(frame, self.perimeter_points[-1], 
                    self.perimeter_points[0], (0, 255, 0), 2)
            
            # Semi-transparent fill
            overlay = frame.copy()
            pts = np.array(self.perimeter_points, dtype=np.int32)
            cv2.fillPoly(overlay, [pts], (0, 255, 0))
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Draw points
        for i, pt in enumerate(self.perimeter_points):
            cv2.circle(frame, pt, 6, (0, 255, 0), -1)
            cv2.circle(frame, pt, 8, (255, 255, 255), 2)
            # Number the points
            cv2.putText(frame, str(i+1), (pt[0]+10, pt[1]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def _finalize_perimeter(self, frame):
        """Finalize perimeter setup"""
        # Create mask
        self.mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        points = np.array(self.perimeter_points, dtype=np.int32)
        cv2.fillPoly(self.mask, [points], 255)
        
        # Save reference frame (background)
        self.reference_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.drawing_complete = True
        
        # Calculate mask area for info
        mask_area = cv2.countNonZero(self.mask)
        total_area = frame.shape[0] * frame.shape[1]
        coverage = (mask_area / total_area) * 100
        if self.logger:
            self.logger.info(f"Perimeter covers {coverage:.1f}% of frame")
            self.logger.info("Background reference captured")

    # SIMPLE BACKGROUND SUBTRACTION METHODS
    def _check_obstruction_internal(self, current_frame) -> Tuple[bool, float]:
        """
        Simple background subtraction for obstruction detection
        """
        if self.reference_frame is None or self.mask is None:
            return False, 0.0
        
        try:
            # Convert current frame to grayscale
            current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            
            # Ensure frame sizes match
            if current_gray.shape != self.reference_frame.shape:
                current_gray = cv2.resize(current_gray, 
                                        (self.reference_frame.shape[1], self.reference_frame.shape[0]))
            
            # Step 1: Calculate absolute difference between current frame and reference
            diff = cv2.absdiff(self.reference_frame, current_gray)
            
            # Step 2: Apply threshold to get binary image of changes
            _, thresh = cv2.threshold(diff, self.difference_threshold, 255, cv2.THRESH_BINARY)
            
            # Step 3: Apply perimeter mask to focus only on the monitored area
            masked_diff = cv2.bitwise_and(thresh, thresh, mask=self.mask)
            
            # Step 4: Find contours of the changed areas
            contours, _ = cv2.findContours(masked_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Step 5: Calculate total changed area within perimeter
            total_changed_pixels = cv2.countNonZero(masked_diff)
            mask_area = cv2.countNonZero(self.mask)
            
            if mask_area == 0:
                return False, 0.0
            
            # Calculate percentage of perimeter area that has changed
            percentage = (total_changed_pixels / mask_area) * 100
            
            # Step 6: Check if any significant contours are found
            significant_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_contour_area:
                    significant_contours.append(contour)
            
            # Obstruction detected if significant changes OR large percentage change
            is_obstructed = (len(significant_contours) > 0 and percentage > 5) or percentage >= self.obstruction_threshold
            
            return is_obstructed, percentage
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Background subtraction failed: {e}")
            return False, 0.0

    def get_obstruction_visualization(self, current_frame):
        """
        Returns a visualization frame showing the background subtraction process
        Useful for debugging and understanding what's being detected
        """
        if self.reference_frame is None or self.mask is None:
            return current_frame
        
        try:
            # Create a multi-panel visualization
            current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            
            if current_gray.shape != self.reference_frame.shape:
                current_gray = cv2.resize(current_gray, 
                                        (self.reference_frame.shape[1], self.reference_frame.shape[0]))
                current_frame = cv2.resize(current_frame, 
                                         (self.reference_frame.shape[1], self.reference_frame.shape[0]))
            
            # Calculate difference
            diff = cv2.absdiff(self.reference_frame, current_gray)
            _, thresh = cv2.threshold(diff, self.difference_threshold, 255, cv2.THRESH_BINARY)
            masked_diff = cv2.bitwise_and(thresh, thresh, mask=self.mask)
            
            # Find contours
            contours, _ = cv2.findContours(masked_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Create visualization frame
            vis_frame = current_frame.copy()
            
            # Draw perimeter (always show in visualization mode)
            points = np.array(self.perimeter_points, dtype=np.int32)
            cv2.polylines(vis_frame, [points], True, (0, 255, 0), 2)
            
            # Draw significant contours in red
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_contour_area:
                    # Draw bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(vis_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    
                    # Draw contour
                    cv2.drawContours(vis_frame, [contour], -1, (0, 0, 255), 2)
                    
                    # Label with area
                    cv2.putText(vis_frame, f"Area: {int(area)}", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Add status text
            total_changed = cv2.countNonZero(masked_diff)
            mask_area = cv2.countNonZero(self.mask)
            percentage = (total_changed / mask_area * 100) if mask_area > 0 else 0
            
            status_color = (0, 0, 255) if percentage >= self.obstruction_threshold else (0, 255, 0)
            status_text = f"Obstruction: {percentage:.1f}% ({len(contours)} contours)"
            
            cv2.putText(vis_frame, status_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            return vis_frame
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Visualization failed: {e}")
            return current_frame

    def update_background(self, frame):
        """
        Update the background reference frame
        Useful when lighting conditions change
        """
        if self.drawing_complete:
            with self.lock:
                self.reference_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if self.logger:
                self.logger.info("Background reference updated")
            return True
        return False

    def set_detection_parameters(self, difference_threshold=25, min_contour_area=500, obstruction_threshold=50.0):
        """
        Set detection parameters for background subtraction
        """
        self.difference_threshold = difference_threshold
        self.min_contour_area = min_contour_area
        self.obstruction_threshold = obstruction_threshold
        
        if self.logger:
            self.logger.info(f"Detection params: diff_thresh={difference_threshold}, "
                           f"min_area={min_contour_area}, obst_thresh={obstruction_threshold}")

    def draw_perimeter_on_frame(self, frame):
        """
        Draw perimeter overlay - respects visibility setting
        """
        return self.draw_overlay(frame)
    
    def draw_overlay(self, frame):
        """
        Draw perimeter overlay on frame with status indicators
        Respects the visibility setting
        """
        if not self.drawing_complete or len(self.perimeter_points) < 3:
            return frame
        
        # If perimeter is hidden, return original frame
        if not self.visible:
            return frame
        
        with self.lock:
            obstructed = self.obstruction_detected
            pct = self.current_obstruction_pct
        
        # Choose colors based on state
        if obstructed:
            color = (0, 0, 255)  # Red
            status = "BREACH"
        else:
            color = (0, 255, 0)  # Green
            status = "ACTIVE"
        
        # Create a copy of the frame to avoid modifying the original
        result_frame = frame.copy()
        
        # Draw perimeter polygon with filled background
        points = np.array(self.perimeter_points, dtype=np.int32)
        
        # Draw filled polygon first (background)
        overlay = result_frame.copy()
        cv2.fillPoly(overlay, [points], color)
        cv2.addWeighted(overlay, 0.15, result_frame, 0.85, 0, result_frame)
        
        # Draw perimeter outline
        cv2.polylines(result_frame, [points], True, color, 3)
        
        # Draw corner points
        for pt in self.perimeter_points:
            cv2.circle(result_frame, pt, 6, color, -1)
            cv2.circle(result_frame, pt, 8, (255, 255, 255), 2)
        
        # Status panel background - draw once per state change
        panel_height = 80 if obstructed else 60
        cv2.rectangle(result_frame, (5, 5), (350, panel_height), (0, 0, 0), -1)
        cv2.rectangle(result_frame, (5, 5), (350, panel_height), color, 2)
        
        # Status text
        cv2.putText(result_frame, f"PERIMETER: {status}", (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Obstruction percentage (only when obstructed)
        if obstructed:
            cv2.putText(result_frame, f"OBSTRUCTION: {pct:.1f}%", (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return result_frame

    def draw_minimal_overlay(self, frame):
        """
        Draw only obstruction boxes without perimeter outline
        Useful for hidden perimeter mode but still showing detections
        """
        if not self.drawing_complete or not self.show_detection_boxes:
            return frame
        
        try:
            # Check for obstructions and draw boxes if found
            obstructed, percentage = self._check_obstruction_internal(frame)
            
            if obstructed:
                # Convert to grayscale for detection
                current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if current_gray.shape != self.reference_frame.shape:
                    current_gray = cv2.resize(current_gray, 
                                            (self.reference_frame.shape[1], self.reference_frame.shape[0]))
                    frame = cv2.resize(frame, 
                                     (self.reference_frame.shape[1], self.reference_frame.shape[0]))
                
                # Calculate difference and find contours
                diff = cv2.absdiff(self.reference_frame, current_gray)
                _, thresh = cv2.threshold(diff, self.difference_threshold, 255, cv2.THRESH_BINARY)
                masked_diff = cv2.bitwise_and(thresh, thresh, mask=self.mask)
                
                contours, _ = cv2.findContours(masked_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Draw bounding boxes for significant contours
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > self.min_contour_area:
                        x, y, w, h = cv2.boundingRect(contour)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(frame, "OBSTRUCTION", (x, y-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            return frame
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Minimal overlay failed: {e}")
            return frame

    # KEEP ALL YOUR EXISTING METHODS BELOW - they remain the same
    def set_perimeter_points(self, points: list):
        """
        Set perimeter points directly without interactive drawing
        Points should be a list of (x, y) tuples
        """
        self.reset()
        
        if len(points) < 3:
            if self.logger:
                self.logger.error("Need at least 3 points for perimeter")
            return False
        
        self.perimeter_points = points.copy()
        
        if self.logger:
            self.logger.info(f"Perimeter set with {len(points)} points")
        
        return True
    
    def finalize_perimeter(self, frame):
        """
        Finalize perimeter with the current frame as reference
        """
        if len(self.perimeter_points) < 3:
            if self.logger:
                self.logger.error("Cannot finalize - need at least 3 perimeter points")
            return False
        
        # Create mask
        self.mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        points = np.array(self.perimeter_points, dtype=np.int32)
        cv2.fillPoly(self.mask, [points], 255)
        
        # Save reference frame (background)
        self.reference_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.drawing_complete = True
        
        # Calculate mask area for info
        mask_area = cv2.countNonZero(self.mask)
        total_area = frame.shape[0] * frame.shape[1]
        coverage = (mask_area / total_area) * 100
        if self.logger:
            self.logger.info(f"Perimeter covers {coverage:.1f}% of frame")
        
        return True
    
    def set_rectangular_perimeter(self, frame, x1: int, y1: int, x2: int, y2: int):
        """
        Set a rectangular perimeter using two corner points
        """
        points = [
            (x1, y1),
            (x2, y1),
            (x2, y2),
            (x1, y2)
        ]
        
        if self.set_perimeter_points(points):
            return self.finalize_perimeter(frame)
        return False
    
    def set_polygonal_perimeter(self, frame, points: list):
        """
        Set a polygonal perimeter and finalize with reference frame
        """
        if self.set_perimeter_points(points):
            return self.finalize_perimeter(frame)
        return False

    def start_continuous_monitoring(self, get_frame_callback: Callable, 
                                   obstruction_callback: Optional[Callable] = None,
                                   check_interval: float = 0.3):
        """
        Start continuous background monitoring - OPTIMIZED
        """
        if not self.drawing_complete:
            if self.logger:
                self.logger.error("Cannot start monitoring - perimeter not configured")
            return False
        
        if self.monitoring_active:
            if self.logger:
                self.logger.warning("Monitoring already active")
            return True
        
        self.obstruction_callback = obstruction_callback
        self.check_interval = check_interval
        self.monitoring_active = True
        self.stop_flag.clear()
        
        def monitoring_loop():
            if self.logger:
                self.logger.info("🔄 Perimeter monitoring started (Background Subtraction)")
            last_state = False
            consecutive_detections = 0
            required_consecutive = 2
            
            while self.monitoring_active and not self.stop_flag.is_set():
                try:
                    # Get current frame
                    frame = get_frame_callback()
                    if frame is None:
                        time.sleep(self.check_interval)
                        continue
                    
                    # Check obstruction using background subtraction
                    obstructed, percentage = self._check_obstruction_internal(frame)
                    
                    with self.lock:
                        self.current_obstruction_pct = percentage
                    
                    # Debounce detection
                    if obstructed:
                        consecutive_detections += 1
                    else:
                        consecutive_detections = 0
                    
                    # State change detection
                    current_state = consecutive_detections >= required_consecutive
                    
                    if current_state != last_state:
                        with self.lock:
                            self.obstruction_detected = current_state
                        
                        if current_state:
                            if self.logger:
                                self.logger.warning(f"🚨 PERIMETER BREACH: {percentage:.1f}%")
                        else:
                            if self.logger:
                                self.logger.info("✅ Perimeter clear")
                        
                        # Notify callback
                        if self.obstruction_callback:
                            try:
                                self.obstruction_callback(current_state, percentage)
                            except Exception as e:
                                if self.logger:
                                    self.logger.error(f"Callback error: {e}")
                        
                        last_state = current_state
                    
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Monitoring loop error: {e}")
                    time.sleep(self.check_interval)
            
            if self.logger:
                self.logger.info("🛑 Perimeter monitoring stopped")
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        return True
    
    def stop_continuous_monitoring(self):
        """Stop continuous monitoring"""
        if not self.monitoring_active:
            return
        
        if self.logger:
            self.logger.info("Stopping perimeter monitoring...")
        self.monitoring_active = False
        self.stop_flag.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        
        with self.lock:
            self.obstruction_detected = False
            self.current_obstruction_pct = 0.0
    
    def check_obstruction(self, current_frame) -> Tuple[bool, float]:
        """
        Single obstruction check (public API)
        """
        if not self.drawing_complete:
            return False, 0.0
        
        return self._check_obstruction_internal(current_frame)
    
    def set_obstruction_callback(self, callback):
        """Set obstruction callback"""
        self.obstruction_callback = callback
    
    def update_reference_frame(self, frame):
        """Update reference frame (alias for update_background)"""
        return self.update_background(frame)
    
    def set_threshold(self, threshold: float):
        """Set obstruction detection threshold (0-100)"""
        if 0 <= threshold <= 100:
            self.obstruction_threshold = threshold
            if self.logger:
                self.logger.info(f"Obstruction threshold set to {threshold}%")
    
    def set_check_interval(self, interval: float):
        """Set monitoring check interval in seconds"""
        if interval > 0:
            self.check_interval = interval
            if self.logger:
                self.logger.info(f"Check interval set to {interval}s")
    
    def get_status(self) -> dict:
        """Get current monitoring status"""
        with self.lock:
            return {
                'configured': self.drawing_complete,
                'monitoring': self.monitoring_active,
                'obstructed': self.obstruction_detected,
                'obstruction_pct': self.current_obstruction_pct,
                'point_count': len(self.perimeter_points),
                'threshold': self.obstruction_threshold,
                'visible': self.visible,
                'show_detection_boxes': self.show_detection_boxes,
                'method': 'background_subtraction'
            }
    
    def reset(self):
        """Reset all perimeter data"""
        self.stop_continuous_monitoring()
        
        with self.lock:
            self.reference_frame = None
            self.perimeter_points = []
            self.mask = None
            self.drawing_complete = False
            self.obstruction_detected = False
            self.current_obstruction_pct = 0.0
        
        if self.logger:
            self.logger.info("Perimeter reset")