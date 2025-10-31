# PC Monitor - Remote Activity Monitoring System (FIXED)

**Educational/Demonstration Project for AV/Security Research**

A Python-based client-server system for remotely monitoring PC activity including keystrokes, mouse movements, window changes, and automatic screenshots. Features advanced remote administration capabilities and evasion technique demonstrations.

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
- Anti-debugging and anti-VM checks are for EDUCATIONAL demonstration only
- They detect but do NOT block execution (demo mode)
- Real malware would behave differently - this project continues regardless
- Designed to show AV researchers what techniques exist

---

## Features

### Core Monitoring
- 🖱️ **Mouse Activity Tracking** - Captures clicks with coordinates and window context
- ⌨️ **Live Keylogging** - Real-time keystroke capture with window tracking
- 🪟 **Window Tracking** - Records active window changes and process names
- 📸 **Automatic Screenshots** - Configurable interval-based capture with motion detection
- 📊 **Activity Log** - Comprehensive event logging with timestamps

### Client Dashboard
- 🌐 **Remote GUI Client** - Full-featured desktop application
- 📺 **Live Screenshot View** - Real-time screenshot display
- ⌨️ **Live Keystroke Feed** - Stream keystrokes as they're typed
- 🔍 **Search & Filter** - Advanced event filtering and search
- 📤 **Data Export** - Export events and keystrokes to JSON
- 🎮 **Remote Control** - Execute commands, launch apps, shutdown/restart

### Advanced Features
- 🗂️ **File System Browser** - Browse remote directories and files
- 📋 **Clipboard Monitor** - View and set remote clipboard content
- ⚙️ **Process Manager** - List, kill, and start processes remotely
- 💻 **Remote Command Execution** - Execute shell commands with output capture
- 🔄 **Reverse Connection** - Server auto-registers with client

### Educational Evasion Demonstrations
- 🔐 **Mutex (Single Instance)** - Prevents multiple instances
- 🐛 **Anti-Debugging Detection** - Detects debuggers (continues anyway)
- 🖥️ **Anti-VM Detection** - Detects virtualization (continues anyway)
- 🔒 **String Obfuscation Ready** - Base64/XOR encoding available
- 📦 **Modular Architecture** - Clean separation of concerns

### Security Features
- 🔑 **API Key Authentication** - Protect server access
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
    "callback_url": "http://YOUR_CLIENT_IP:8080",
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
├── server.py                    # ✅ Fixed entry point
├── client.py                    # ✅ Fixed entry point
├── install_service.py           # Windows service installer
├── build.bat                    # Nuitka build script
├── requirements.txt             # Dependencies
│
├── server_modules/              # ✅ All fixed
│   ├── __init__.py
│   ├── config.py               # ✅ Proper exports
│   ├── monitoring.py           # ✅ Complete implementation
│   ├── screenshots.py          # ✅ Complete implementation
│   ├── api_routes.py           # ✅ Flask app initialized
│   ├── remote_commands.py      # Command execution
│   ├── reverse_connection.py   # ✅ Complete implementation
│   └── utils.py                # Helper functions
│
├── client_modules/              # ✅ All working
│   ├── __init__.py
│   ├── gui.py                  # Main GUI
│   ├── api_client.py           # API wrapper
│   ├── server_tab.py           # Server tab UI
│   ├── callback_listener.py    # Reverse connection listener
│   ├── dialogs.py              # Dialog windows
│   └── config.py               # Config management
│
├── evasion_modules/             # ✅ All complete
│   ├── __init__.py
│   ├── mutex.py                # ✅ Single instance check
│   ├── anti_debug.py           # ✅ Complete implementation
│   ├── anti_vm.py              # ✅ Complete implementation
│   └── obfuscation.py          # String encoding
│
└── persistence_modules/
    ├── __init__.py
    ├── registry.py             # Registry auto-start
    └── service.py              # Service placeholder
```

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

**What makes this educational:**
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

This software is provided **as-is** for **educational and security research purposes only**. 

**No warranty** of any kind. Authors are **not liable** for misuse, legal violations, data loss, or any damages.

Users are **solely responsible** for:
- Compliance with all applicable laws
- Obtaining proper consent
- Securing data appropriately
- Ethical use

---

## Support & Contributing

This is an educational project for security research and AV testing.

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