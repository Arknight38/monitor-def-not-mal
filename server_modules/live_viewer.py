"""
Live PC Viewer Module
Real-time screen streaming with encryption and compression
"""
import base64
import threading
import time
import queue
from datetime import datetime
from typing import Dict, List, Optional
import io
import zlib
from PIL import Image, ImageGrab
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets

class LiveViewer:
    """Handle live screen viewing with encryption and streaming"""
    
    def __init__(self):
        self.streaming = False
        self.stream_thread = None
        self.frame_queue = queue.Queue(maxsize=10)
        self.connected_clients = set()
        self.encryption_key = None
        self.cipher_suite = None
        self.stream_quality = 70  # JPEG quality (1-100)
        self.stream_fps = 10  # Frames per second
        self.compression_level = 6  # zlib compression level
        self.screen_size = None
        self.last_frame_time = 0
        self.total_frames_captured = 0
        self.total_bytes_sent = 0
        
        # Initialize encryption
        self._initialize_encryption()
    
    def _initialize_encryption(self):
        """Initialize encryption for secure streaming"""
        try:
            # Generate a random key for this session
            self.encryption_key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.encryption_key)
            return True
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            return False
    
    def get_encryption_key(self) -> str:
        """Get the base64 encoded encryption key for clients"""
        if self.encryption_key:
            return base64.b64encode(self.encryption_key).decode('utf-8')
        return None
    
    def _capture_screen(self) -> Optional[bytes]:
        """Capture and compress screen with encryption"""
        try:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            # Store screen size
            if not self.screen_size:
                self.screen_size = screenshot.size
            
            # Convert to JPEG with compression
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='JPEG', quality=self.stream_quality, optimize=True)
            img_data = img_buffer.getvalue()
            
            # Apply zlib compression
            compressed_data = zlib.compress(img_data, self.compression_level)
            
            # Encrypt the compressed data
            if self.cipher_suite:
                encrypted_data = self.cipher_suite.encrypt(compressed_data)
                return encrypted_data
            else:
                return compressed_data
                
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def _streaming_loop(self):
        """Main streaming loop"""
        frame_interval = 1.0 / self.stream_fps
        
        while self.streaming:
            try:
                start_time = time.time()
                
                # Capture frame
                frame_data = self._capture_screen()
                
                if frame_data:
                    # Create frame info
                    frame_info = {
                        'timestamp': datetime.now().isoformat(),
                        'frame_number': self.total_frames_captured,
                        'data_size': len(frame_data),
                        'encrypted': self.cipher_suite is not None,
                        'compressed': True,
                        'quality': self.stream_quality,
                        'screen_size': self.screen_size
                    }
                    
                    # Encode frame data as base64 for JSON transport
                    frame_info['data'] = base64.b64encode(frame_data).decode('utf-8')
                    
                    # Add to queue (non-blocking, drop old frames if queue is full)
                    try:
                        self.frame_queue.put_nowait(frame_info)
                    except queue.Full:
                        # Remove oldest frame and add new one
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame_info)
                        except queue.Empty:
                            pass
                    
                    self.total_frames_captured += 1
                    self.total_bytes_sent += len(frame_data)
                    self.last_frame_time = time.time()
                
                # Maintain frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"Error in streaming loop: {e}")
                time.sleep(1)  # Prevent tight error loop
    
    def start_streaming(self, quality: int = 70, fps: int = 10) -> Dict:
        """Start live screen streaming"""
        if self.streaming:
            return {
                "success": False,
                "error": "Streaming already active"
            }
        
        # Validate parameters
        self.stream_quality = max(1, min(100, quality))
        self.stream_fps = max(1, min(30, fps))
        
        # Reset counters
        self.total_frames_captured = 0
        self.total_bytes_sent = 0
        
        # Start streaming
        self.streaming = True
        self.stream_thread = threading.Thread(target=self._streaming_loop, daemon=True)
        self.stream_thread.start()
        
        return {
            "success": True,
            "message": "Live streaming started",
            "quality": self.stream_quality,
            "fps": self.stream_fps,
            "encrypted": self.cipher_suite is not None,
            "encryption_key": self.get_encryption_key()
        }
    
    def stop_streaming(self) -> Dict:
        """Stop live screen streaming"""
        if not self.streaming:
            return {
                "success": False,
                "error": "Streaming not active"
            }
        
        self.streaming = False
        
        if self.stream_thread:
            self.stream_thread.join(timeout=2)
        
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        return {
            "success": True,
            "message": "Live streaming stopped",
            "total_frames": self.total_frames_captured,
            "total_bytes": self.total_bytes_sent
        }
    
    def get_latest_frame(self) -> Dict:
        """Get the latest frame from the stream"""
        if not self.streaming:
            return {
                "success": False,
                "error": "Streaming not active"
            }
        
        try:
            # Get the most recent frame (non-blocking)
            frame_info = self.frame_queue.get_nowait()
            return {
                "success": True,
                "frame": frame_info
            }
        except queue.Empty:
            return {
                "success": False,
                "error": "No frames available"
            }
    
    def get_stream_status(self) -> Dict:
        """Get current streaming status and statistics"""
        return {
            "success": True,
            "streaming": self.streaming,
            "quality": self.stream_quality,
            "fps": self.stream_fps,
            "screen_size": self.screen_size,
            "total_frames": self.total_frames_captured,
            "total_bytes": self.total_bytes_sent,
            "frames_in_queue": self.frame_queue.qsize(),
            "last_frame_time": self.last_frame_time,
            "encrypted": self.cipher_suite is not None,
            "compression_level": self.compression_level,
            "connected_clients": len(self.connected_clients)
        }
    
    def update_stream_settings(self, quality: int = None, fps: int = None, compression: int = None) -> Dict:
        """Update streaming settings on the fly"""
        updated_settings = {}
        
        if quality is not None:
            self.stream_quality = max(1, min(100, quality))
            updated_settings['quality'] = self.stream_quality
        
        if fps is not None:
            self.stream_fps = max(1, min(30, fps))
            updated_settings['fps'] = self.stream_fps
        
        if compression is not None:
            self.compression_level = max(0, min(9, compression))
            updated_settings['compression'] = self.compression_level
        
        return {
            "success": True,
            "message": "Settings updated",
            "updated_settings": updated_settings,
            "current_settings": {
                "quality": self.stream_quality,
                "fps": self.stream_fps,
                "compression": self.compression_level
            }
        }
    
    def add_client(self, client_id: str) -> Dict:
        """Add a client to the streaming session"""
        self.connected_clients.add(client_id)
        return {
            "success": True,
            "message": f"Client {client_id} added to stream",
            "total_clients": len(self.connected_clients),
            "encryption_key": self.get_encryption_key()
        }
    
    def remove_client(self, client_id: str) -> Dict:
        """Remove a client from the streaming session"""
        self.connected_clients.discard(client_id)
        return {
            "success": True,
            "message": f"Client {client_id} removed from stream",
            "total_clients": len(self.connected_clients)
        }
    
    def get_frame_history(self, count: int = 5) -> Dict:
        """Get multiple recent frames"""
        if not self.streaming:
            return {
                "success": False,
                "error": "Streaming not active"
            }
        
        frames = []
        temp_frames = []
        
        # Collect available frames
        while not self.frame_queue.empty() and len(temp_frames) < count:
            try:
                frame = self.frame_queue.get_nowait()
                temp_frames.append(frame)
            except queue.Empty:
                break
        
        # Put frames back in queue (most recent first)
        for frame in reversed(temp_frames):
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                break
        
        # Return frames (oldest first)
        frames = list(reversed(temp_frames))
        
        return {
            "success": True,
            "frames": frames,
            "count": len(frames)
        }

# Global live viewer instance
live_viewer = LiveViewer()