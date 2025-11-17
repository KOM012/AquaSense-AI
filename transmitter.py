# transmitter.py - ULTRA SIMPLE VERSION
import serial
import serial.tools.list_ports
import time
from typing import Optional

class BluetoothTransmitter:
    def __init__(self):
        self.ser: Optional[serial.Serial] = None
        self.connected = False
        
    def list_ports(self):
        """List available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def connect(self, port: str, baudrate: int = 9600) -> bool:
        """Connect to specified serial port"""
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            self.connected = True
            print(f"✅ Connected to {port} at {baudrate} baud")
            time.sleep(2)  # Wait for Arduino to reset
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        if self.connected and self.ser:
            try:
                self.ser.close()
            except:
                pass
            self.connected = False
            print("✅ Disconnected from Bluetooth")
    
    def send_command(self, command: int):
        """Send simple command to Arduino"""
        if not self.connected or not self.ser:
            print("❌ Not connected to Bluetooth")
            return False
            
        try:
            command_str = f"{command}\n"
            self.ser.write(command_str.encode())
            self.ser.flush()
            print(f"📡 Sent: {command}")
            return True
        except Exception as e:
            print(f"❌ Failed to send: {e}")
            self.connected = False
            return False
    
    def send_drowning_alert(self):
        """Send drowning alert"""
        return self.send_command(1)
    
    def send_obstruction_alert(self):
        """Send obstruction alert"""
        return self.send_command(2)
    
    def send_clear_alert(self):
        """Send clear alert"""
        return self.send_command(0)

# Test
if __name__ == "__main__":
    bt = BluetoothTransmitter()
    ports = bt.list_ports()
    print("Ports:", ports)
    
    if ports and bt.connect(ports[0]):
        print("Testing...")
        bt.send_drowning_alert()
        time.sleep(3)
        bt.send_clear_alert()
        time.sleep(1)
        bt.send_obstruction_alert()
        time.sleep(3)
        bt.send_clear_alert()
        bt.disconnect()