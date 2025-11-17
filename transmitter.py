# transmitter.py - SIMPLIFIED WITH DIFFERENT FREQUENCIES
import serial
import time
import threading
from serial.tools import list_ports

class BluetoothTransmitter:
    def __init__(self, baud=9600):
        self.baud = baud
        self.ser = None
        self.connected = False
        self.obstruction_pulsing = False
        self.stop_pulse = threading.Event()
        
    def list_ports(self):
        """Get available ports"""
        try:
            ports = [port.device for port in list_ports.comports()]
            print(f"Available ports: {ports}")
            return ports
        except:
            return ["COM3", "COM4", "COM5", "COM6", "COM7"]
    
    def connect(self, port: str) -> bool:
        """Connect to Arduino"""
        try:
            # Close existing
            if self.ser:
                self.ser.close()
            
            print(f"Connecting to {port}...")
            self.ser = serial.Serial(port, self.baud, timeout=1)
            time.sleep(2)  # Wait for Arduino
            
            # Test connection
            self.ser.write(b'\n')
            time.sleep(0.5)
            
            self.connected = True
            print(f"✅ Connected to {port}")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect"""
        try:
            self.stop_obstruction_pulse()
            if self.ser:
                self._send_command('0')  # Turn off everything
                self.ser.close()
        except:
            pass
        finally:
            self.connected = False
    
    def _send_command(self, command: str) -> bool:
        """Send command to Arduino"""
        if not self.connected or not self.ser:
            return False
            
        try:
            self.ser.write(f"{command}\n".encode())
            print(f"Sent: {command}")
            return True
        except:
            self.connected = False
            return False
    
    def send_drowning_alert(self):
        """Drowning alert - HIGH frequency (continuous)"""
        if self.connected:
            self.stop_obstruction_pulse()
            return self._send_command('1')  # High frequency
    
    def send_obstruction_alert(self):
        """Obstruction alert - LOW frequency (pulsing)"""
        if self.connected:
            self.stop_obstruction_pulse()
            return self._send_command('2')  # Low frequency
    
    def send_clear_alert(self):
        """Clear all alerts"""
        if self.connected:
            self.stop_obstruction_pulse()
            return self._send_command('0')
    
    def start_obstruction_pulse(self):
        """Start obstruction pulsing with low frequency"""
        if not self.connected or self.obstruction_pulsing:
            return False
            
        self.obstruction_pulsing = True
        self.stop_pulse.clear()
        
        def pulse_loop():
            while self.obstruction_pulsing and not self.stop_pulse.is_set():
                self._send_command('2')  # Low frequency on
                time.sleep(1.0)
                if self.stop_pulse.is_set():
                    break
                self._send_command('0')  # Off
                time.sleep(1.0)
        
        threading.Thread(target=pulse_loop, daemon=True).start()
        return True
    
    def stop_obstruction_pulse(self):
        """Stop obstruction pulsing"""
        if self.obstruction_pulsing:
            self.obstruction_pulsing = False
            self.stop_pulse.set()
            self._send_command('0')
    
    def send(self, command: str) -> bool:
        """Legacy support"""
        return self._send_command(command)