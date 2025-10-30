# PC Monitor - Remote Activity Monitoring System

A Python-based client-server system for remotely monitoring PC activity including keystrokes, mouse movements, window changes, and automatic screenshots. Features advanced remote administration capabilities including process management, file system operations, and clipboard monitoring.

## ⚠️ Important Disclaimers

**Legal & Ethical Use Only:**
- This software is intended for **educational purposes** and legitimate use cases only (parental monitoring, employee monitoring with consent, personal device tracking)
- You must have legal authorization to monitor any computer
- Unauthorized monitoring may violate privacy laws and workplace policies
- Always obtain explicit consent before deploying
- Review local laws regarding computer monitoring in your jurisdiction

**Security Warning:**
- Data transmitted over HTTP is **not encrypted**
- Screenshots and keystroke logs contain highly sensitive information
- Change the default API key immediately upon first run
- Use on trusted networks only
- Consider implementing VPN for remote access
- This is a learning project - not production-grade security

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
- 📁 **File Transfer** - Upload and download files (coming soon)

### Security Features
- 🔑 **API Key Authentication** - Protect server access
- 🛑 **Kill Switch** - Remotely terminate server from client
- 📝 **Auto Data Cleanup** - Configurable retention policies
- 🔐 **Request Authentication** - All endpoints require valid API key

### Multi-PC Support
- 📊 **Multi-Tab Interface** - Monitor multiple PCs simultaneously
- 💾 **Persistent Configuration** - Saved server connections
- 🔄 **Auto-Refresh** - Optional automatic status updates

## System Requirements

### Server (Target PC - Being Monitored)
- **OS**: Windows (for window tracking features)
- **Python**: 3.7+ (if running from source)
- **Network**: Local network connectivity
- **Disk**: ~50-100MB + screenshot storage
- **RAM**: ~100MB base memory usage

### Client (Monitoring PC)
- **OS**: Windows, macOS, or Linux
- **Python**: 3.7+ (if running from source)
- **Network**: Access to server on local network
- **Display**: 1400x900 minimum recommended

## Quick Start

### Option 1: Using Pre-Built Executables (Recommended)

**Step 1: Build the executables**
```bash
# Run the interactive build script
build.bat
```

Follow the prompts:
- Choose what to build (Server, Client, or Both)
- Choose console mode (No console for stealth, or with console for debugging)
- Choose optimization level
- Choose service installation (optional)

**Step 2: Deploy Server to Target PC**
1. Copy `dist/PCMonitor.exe` to target computer
2. Run `PCMonitor.exe` (first run creates configuration)
3. Check console output or `config.json` for the API key
4. Note the displayed IP address(es) for connection
5. Keep `PCMonitor.exe` running

**Step 3: Setup Client on Monitoring PC**
1. Copy `dist/PCMonitorClient.exe` to your computer
2. Run `PCMonitorClient.exe`
3. Click **Add Server**
4. Enter server name (e.g., "Laptop")
5. Enter server URL: `http://<SERVER_IP>:5000`
6. Enter the API key from Step 2
7. Click **Add**
8. Click **Start** to begin monitoring

### Option 2: Running from Source

**Install Dependencies:**
```bash
pip install flask flask-cors pynput pillow pywin32 psutil requests
```

**Start Server (Target PC):**
```bash
python server.py
```
- On first run, `config.json` is created with API key
- Note the API key displayed in console
- Server runs on port 5000 by default

**Start Client (Monitoring PC):**
```bash
python client.py
```
- Click "Add Server" to configure connection
- Enter server URL and API key
- Start monitoring

## Configuration

### Server Configuration (`config.json`)

The server auto-generates this file on first run:

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
- `motion_detection` - Only screenshot during activity (default: false)
- `data_retention_days` - Days to keep old data (default: 30)
- `pc_id` - Unique identifier for this PC
- `pc_name` - Friendly name for identification

### Client Configuration (`multi_client_config.json`)

Auto-generated on first run when you add servers:

```json
{
    "servers": [
        {
            "name": "Work Laptop",
            "url": "http://192.168.0.48:5000",
            "api_key": "YOUR_SECRET_KEY_HERE"
        },
        {
            "name": "Home PC",
            "url": "http://192.168.0.50:5000",
            "api_key": "ANOTHER_SECRET_KEY"
        }
    ]
}
```

**How to Configure:**
1. Run `PCMonitorClient.exe`
2. Click **Add Server**
3. Fill in server details
4. Click **Add**
5. Configuration is saved automatically

## Network Setup

### Finding Server IP Address

**On Windows (Target PC):**
```bash
ipconfig
```
Look for **IPv4 Address** under your active network adapter (e.g., `192.168.0.48`)

The server displays all available IP addresses on startup.

**On macOS/Linux:**
```bash
ifconfig
# or
ip addr show
```

### Firewall Configuration

**Windows Firewall (Required):**

Via Command Line (Administrator):
```bash
netsh advfirewall firewall add rule name="PC Monitor" dir=in action=allow protocol=TCP localport=5000
```

Via GUI:
1. Open **Windows Defender Firewall with Advanced Security**
2. Click **Inbound Rules → New Rule**
3. Select **Port** → Next
4. Enter port `5000` (or your custom port) → Next
5. Select **Allow the connection** → Next
6. Apply to all profiles → Next
7. Name: "PC Monitor Server" → Finish

### Testing Connection

From monitoring PC:
```bash
# Test if server is reachable
ping <SERVER_IP>

# Test if port is open (PowerShell)
Test-NetConnection -ComputerName <SERVER_IP> -Port 5000
```

## Usage Guide

### Server Operations

**Starting the Server:**
- Double-click `PCMonitor.exe`, or
- Run `python server.py`

**First-Time Setup:**
1. Server creates `config.json` with API key
2. Server displays connection information with IP addresses
3. Copy API key for client configuration
4. Note the IP address(es) shown

**Server runs continuously** - keep the window/process running while monitoring.

**Installing as Windows Service (Optional):**
```bash
# Install service
PCMonitor.exe install

# Start service
PCMonitor.exe start

# Stop service
PCMonitor.exe stop

# Remove service
PCMonitor.exe remove

# Check status
PCMonitor.exe status
```

### Client Interface Guide

#### Main Window

**Control Panel:**
- **Add Server** - Add a new PC to monitor
- **Settings** - Configure client settings

**Server Tabs:**
- Each server gets its own tab for independent monitoring
- Switch between tabs to view different PCs

#### Per-Server Controls

**Status Bar** (Bottom of each tab):
- 🟢 **Green** = Monitoring active
- 🔴 **Red** = Monitoring stopped
- Shows: PC name, event count, keystroke count

**Control Buttons:**
- **Refresh** - Manually update all data
- **Start** - Begin monitoring on server
- **Stop** - Pause monitoring on server
- **Snapshot** - Take immediate screenshot
- **⚠ KILL SERVER** - Emergency stop (terminates server process)
- **Auto-refresh** - Enable automatic updates (15 seconds)
- **Clipboard** - Access clipboard operations
- **Processes** - Manage remote processes
- **Files** - Browse remote file system
- **Command** - Execute remote commands

#### Tab 1: Overview

**Live View Panel:**
- Displays latest screenshot from target PC
- Auto-updates when monitoring is active
- Click screenshot for full-size view
- Click "Refresh Screenshot" for manual update

**Activity Log Panel:**
- Real-time event stream
- Shows mouse clicks, key presses, window changes
- Auto-scrolls to newest events
- Click "Refresh Events" to update manually

#### Tab 2: Live Keylogger

**Live Text Stream:**
- Real-time keystroke display
- Shows typed text as it happens
- Automatically formats text (removes special keys)

**Keystroke Buffer:**
- Shows detailed keystroke history
- Includes timestamp and window context
- Click "Load Buffer" to fetch from server
- Click "Export Text" to save to file

**Controls:**
- **Show All Keys** - Display all keystrokes including special keys
- **Clear** - Clear live feed display
- **Load Buffer** - Fetch keystroke history from server
- **Export Text** - Save to text file

#### Tab 3: Screenshot Gallery

- View all captured screenshots
- Double-click to view full size
- Single-click to preview in panel
- Click "Refresh Gallery" to update list
- Screenshots sorted by newest first

#### Tab 4: Search & Filter

**Search Controls:**
- **Search** - Text search in events
- **Type** - Filter by event type (key_press, mouse_click, window_change, screenshot)

**Actions:**
- **Search** - Apply filters
- **Clear** - Reset all filters

### Advanced Features

#### Clipboard Monitor

Access via **Clipboard** button in controls.

**Features:**
- View current clipboard content on remote PC
- Set clipboard content remotely
- Real-time clipboard access

**Usage:**
1. Click **Clipboard** button
2. Click **Get Clipboard** to view current content
3. Content is displayed in text area

#### Process Manager

Access via **Processes** button in controls.

**Features:**
- List all running processes
- View process details (PID, name, user, CPU, memory)
- Kill processes remotely
- Refresh process list

**Usage:**
1. Click **Processes** button
2. Process list loads automatically
3. Enter PID in the field
4. Click **Kill Process** to terminate
5. Click **Refresh** to update list

**Columns:**
- **PID** - Process ID
- **Name** - Process executable name
- **User** - Username running the process
- **CPU %** - CPU usage percentage
- **Memory (MB)** - Memory usage in megabytes

#### File System Browser

Access via **Files** button in controls.

**Features:**
- Browse remote directories
- View file information (name, type, size, modified date)
- Navigate directory structure

**Usage:**
1. Click **Files** button
2. Enter path in the path field (e.g., `C:\Users`)
3. Click **Browse** to list contents
4. View files and directories in the tree

**Columns:**
- **Name** - File or directory name
- **Type** - file or directory
- **Size** - File size in bytes
- **Modified** - Last modification timestamp

#### Remote Command Execution

Access via **Command** button in controls.

**Features:**
- Execute any Windows shell command
- View command output (STDOUT/STDERR)
- See exit codes
- Command history

**Usage:**
1. Click **Command** button
2. Enter command in the input field
3. Click **Execute**
4. View output in the text area

**Example Commands:**
```bash
dir                    # List directory contents
ipconfig              # Show network configuration
tasklist              # List running processes
systeminfo            # Display system information
whoami                # Show current user
netstat -ano          # Show network connections
```

### Remote Control Features

**System Controls:**
Available through the command execution with these commands:
- **Shutdown PC** - `shutdown /s /t 10`
- **Restart PC** - `shutdown /r /t 10`

**Launch Application:**
- Use command execution to start programs
- Example: `notepad.exe`, `calc.exe`, `C:\Path\To\App.exe`

### Screenshot Settings

Screenshots are configured in the server's `config.json`:

**Manual Configuration:**
1. Stop the server
2. Edit `config.json`
3. Set `"auto_screenshot": true` to enable
4. Set `"screenshot_interval": 300` (seconds between captures)
5. Set `"motion_detection": true` to only capture during activity
6. Restart server

**Intervals:**
- 60s = 1 minute
- 300s = 5 minutes (default)
- 600s = 10 minutes
- 3600s = 1 hour

**Motion Detection:**
- Only captures screenshots when user is active
- Detects mouse movement and keyboard activity
- Saves disk space during idle periods

## Data Storage

### Directory Structure

```
PCMonitor.exe location/
├── config.json              # Server configuration
├── callback_config.json     # Reverse connection config (if enabled)
└── monitor_data/            # Data directory (auto-created)
    ├── screenshots/         # PNG screenshot files
    │   ├── screenshot_20250129_120000.png
    │   ├── screenshot_20250129_120300.png
    │   └── ...
    └── offline_logs/        # Offline event logs
        └── offline_2025-01-29.jsonl

PCMonitorClient.exe location/
└── multi_client_config.json  # Client configuration with servers
```

### Data Files

**Screenshots:**
- Format: PNG
- Naming: `screenshot_YYYYMMDD_HHMMSS.png`
- Size: ~1-3MB each (depending on screen resolution)
- Stored in: `monitor_data/screenshots/`

**Event Logs:**
- Format: JSON Lines (.jsonl)
- One event per line
- Stored in: `monitor_data/offline_logs/`

**Auto-Cleanup:**
- Old files auto-deleted based on `data_retention_days`
- Default: 30 days
- Runs automatically during server operation
- Configurable in `config.json`

### Event Types Logged

| Event Type | Description | Details Captured |
|------------|-------------|------------------|
| `monitoring_started` | Monitoring begins | Timestamp, PC ID |
| `monitoring_stopped` | Monitoring ends | Timestamp, PC ID |
| `mouse_click` | Mouse button click | X, Y coordinates, button, window |
| `key_press` | Keyboard input | Key name, window, process |
| `window_change` | Active window changed | Window title, process name |
| `screenshot` | Screenshot captured | Filename, timestamp |
| `remote_command` | Remote command executed | Command type, parameters |
| `server_killed` | Server terminated | Source (remote/local) |
| `filesystem` | File system operation | Operation type, path |
| `process` | Process operation | Operation type, PID/name |
| `clipboard` | Clipboard operation | Operation type, content length |

## API Endpoints

### Public Endpoint (No Auth)

#### `GET /api/status`
Get server status without authentication.

**Response:**
```json
{
    "monitoring": true,
    "event_count": 1523,
    "keystroke_count": 8432,
    "screenshot_count": 45,
    "pc_id": "abc123def456",
    "pc_name": "LAPTOP-USER",
    "auto_screenshot": true,
    "offline_mode": false
}
```

### Authenticated Endpoints

All require header: `X-API-Key: YOUR_API_KEY`

#### `POST /api/start`
Start monitoring.

#### `POST /api/stop`
Stop monitoring.

#### `POST /api/kill`
Terminate server process (kill switch).

#### `GET /api/events?limit=100&type=mouse_click&search=chrome`
Get filtered events.

**Query Parameters:**
- `limit` - Max events to return (default: 100)
- `type` - Filter by event type
- `search` - Text search in event details
- `start_date` - Filter start date (YYYY-MM-DD)
- `end_date` - Filter end date (YYYY-MM-DD)

#### `GET /api/keystrokes/live`
Get recent keystrokes (non-blocking, up to 50).

#### `GET /api/keystrokes/buffer?format=text&limit=1000`
Get keystroke buffer.

**Query Parameters:**
- `format` - `text` or `json` (default: json)
- `limit` - Max keystrokes (default: 1000)

#### `POST /api/snapshot`
Take immediate screenshot.

#### `GET /api/screenshot/latest`
Get latest screenshot as base64-encoded JSON.

#### `GET /api/screenshot/history`
List all screenshots with metadata.

#### `GET /api/screenshot/<filename>`
Get specific screenshot by filename.

#### `POST /api/settings/screenshot`
Update screenshot settings.

**Request Body:**
```json
{
    "enabled": true,
    "interval": 300
}
```

#### `POST /api/command`
Execute remote command.

**Request Body:**
```json
{
    "type": "shutdown|restart|launch|shell",
    "path": "app.exe",        // for launch
    "command": "ipconfig"     // for shell
}
```

#### `GET /api/clipboard`
Get clipboard content.

**Response:**
```json
{
    "success": true,
    "content": "clipboard text",
    "timestamp": "2025-01-29T12:00:00"
}
```

#### `POST /api/clipboard`
Set clipboard content.

**Request Body:**
```json
{
    "content": "text to set"
}
```

#### `GET /api/process`
List running processes.

**Response:**
```json
{
    "success": true,
    "processes": [
        {
            "pid": 1234,
            "name": "chrome.exe",
            "username": "user",
            "cpu_percent": 5.2,
            "memory_mb": 250.5
        }
    ]
}
```

#### `POST /api/process`
Manage processes.

**Request Body:**
```json
{
    "operation": "kill|start",
    "pid": 1234,           // for kill
    "command": "notepad"   // for start
}
```

#### `GET /api/filesystem?path=C:\`
List directory contents.

**Query Parameters:**
- `path` - Directory path to list

**Response:**
```json
{
    "success": true,
    "path": "C:\\",
    "items": [
        {
            "name": "Users",
            "path": "C:\\Users",
            "type": "directory",
            "size": 0,
            "modified": "2025-01-15T10:30:00",
            "permissions": 16877
        }
    ]
}
```

#### `POST /api/filesystem`
Perform filesystem operations.

**Request Body:**
```json
{
    "operation": "mkdir|delete",
    "path": "C:\\path\\to\\directory"
}
```

#### `GET /api/export?type=events`
Export data.

**Query Parameters:**
- `type` - `events` or `keystrokes`

## Build Script Options

The `build.bat` script provides interactive options:

### Build Selection
1. **Server only** - Build PCMonitor.exe
2. **Client only** - Build PCMonitorClient.exe
3. **Both** - Build both executables

### Console Mode
1. **No console (stealth)** - Silent background operation
   - No visible window
   - No taskbar icon
   - Check `config.json` for API key
2. **With console** - Debug mode
   - Shows output window
   - Displays API key and connection info on startup
   - Useful for troubleshooting

### Optimization
1. **Normal build** - Faster build, larger file size
2. **Optimized** - Slower build, smaller file (UPX compression)

### Service Installation
1. **Do not install as service** - Run as regular application
2. **Install as Windows service** - Auto-start with Windows
   - Runs in background automatically
   - Survives reboots
   - Named "Windows Update Assistant Service" for stealth

**Build Output:**
- Creates `dist/` folder with executables
- Opens `dist` folder automatically when complete
- Displays detailed installation instructions

## Windows Service Installation

The server can be installed as a Windows service for automatic startup:

**Install Service (Administrator required):**
```bash
PCMonitor.exe install
```

**Start Service:**
```bash
PCMonitor.exe start
# Or use: net start WindowsUpdateAssistant
```

**Stop Service:**
```bash
PCMonitor.exe stop
# Or use: net stop WindowsUpdateAssistant
```

**Check Status:**
```bash
PCMonitor.exe status
```

**Remove Service:**
```bash
PCMonitor.exe remove
```

**Service Details:**
- Service Name: `WindowsUpdateAssistant`
- Display Name: "Windows Update Assistant Service"
- Description: "Provides support for Windows Update operations"
- Startup Type: Automatic

**Note:** Service commands require Administrator privileges. Right-click Command Prompt and select "Run as Administrator".

## Troubleshooting

### Server Issues

**"ImportError: No module named 'win32gui'"**
```bash
pip install pywin32
```

**Server won't start / Port in use**
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill process using port
taskkill /PID <PID> /F

# Or change port in config.json
```

**"Permission denied" errors**
- Run as Administrator
- Check antivirus isn't blocking
- Verify write permissions to folder

**High memory usage**
- Check `data_retention_days` setting
- Reduce `screenshot_interval`
- Events limited to 10,000 in memory
- Restart server if needed

**Service won't install**
- Must run as Administrator
- Install pywin32: `pip install pywin32`
- Check if service already exists: `PCMonitor.exe status`

### Client Issues

**"Cannot connect to server"**
- Verify server is running: check Task Manager
- Check IP address is correct (use server's displayed IP)
- Verify port matches (default: 5000)
- Test connection: `ping <SERVER_IP>`
- Check firewall allows port 5000
- Ensure both on same network

**"Unauthorized" error**
- Verify API keys match exactly
- No extra spaces or quotes
- Check `config.json` on server
- Re-enter API key in client

**No screenshots appearing**
- Click "Start" to begin monitoring
- Wait for screenshot interval to pass
- Click "Snapshot" for immediate capture
- Check disk space available on server
- Verify monitoring is actually started (green status)

**Client GUI not responding**
- Check network connection to server
- Disable auto-refresh temporarily
- Close and restart client
- Check server is still running

**Tab shows "Not connected"**
- Verify server URL is correct
- Check server is running and accessible
- Verify API key matches
- Check firewall settings

### Network Issues

**Can't access server from client**
1. Verify server IP: Check server startup message or run `ipconfig`
2. Test ping: `ping <SERVER_IP>` from client
3. Check firewall: Allow port 5000 inbound on server
4. Verify same network/subnet
5. Check router settings if across subnets

**Connection timeout**
- Server may be overloaded
- Network latency too high
- Firewall blocking packets
- Check server is responsive

### Build Issues

**PyInstaller not found**
```bash
pip install pyinstaller
```

**Missing modules during build**
```bash
pip install flask flask-cors pynput pillow pywin32 psutil requests
```

**Build fails with errors**
- Delete `build/` and `dist/` folders
- Delete `.spec` files
- Run `build.bat` again
- Check Python version (3.7+ required)

### Process Manager Issues

**"Access denied" when killing process**
- Some processes require admin privileges
- Server must be running as Administrator
- System processes cannot be killed

**Processes not loading**
- Verify psutil is installed on server
- Check server has Windows support enabled
- Restart server if needed

### File System Issues

**"Path not found" error**
- Verify path exists on remote system
- Use correct path format (e.g., `C:\Users`)
- Check permissions on remote system

**Can't browse certain directories**
- Some directories require admin privileges
- System directories may be protected
- Run server as Administrator if needed

## Security Considerations

### Essential Security Steps

1. **Change API Key Immediately**
   - Generate strong key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Update `config.json` on server
   - Update client configuration

2. **Network Isolation**
   - Use on trusted local networks only
   - Never expose directly to internet
   - Consider VPN for remote access
   - Use separate network segment if possible

3. **Data Protection**
   - **Unencrypted HTTP** - All data sent in clear text
   - Screenshots contain sensitive information
   - Keystroke logs may capture passwords
   - Store on encrypted drives
   - Secure physical access to both machines

4. **Access Control**
   - Protect `config.json` file permissions
   - Don't share API keys
   - Limit who can access client
   - Lock workstation when away

5. **Compliance & Consent**
   - Obtain written consent from monitored users
   - Document monitoring policy
   - Follow local privacy laws (GDPR, CCPA, etc.)
   - Keep audit trail
   - Provide notice to monitored individuals

### Kill Switch Usage

The **⚠ KILL SERVER** button provides emergency shutdown:
- Stops all monitoring immediately
- Terminates server process
- Cannot be restarted remotely
- Requires physical access to restart
- Use for emergency situations only

### Data Retention

Configure automatic cleanup:
```json
"data_retention_days": 7
```
- Automatically deletes old screenshots
- Removes old event logs
- Runs during server operation
- Helps maintain compliance
- Saves disk space

### Service Stealth Mode

When installed as a service with stealth build:
- No visible window
- No taskbar icon
- Runs silently in background
- Named as "Windows Update Assistant Service"
- Auto-starts with Windows
- Check Task Manager to verify running
- Stop with: `net stop WindowsUpdateAssistant` (as Admin)

## Known Limitations

- **Windows-only server** - Window tracking requires Windows
- **No encryption** - HTTP traffic is plain text
- **Basic authentication** - Single API key only
- **No HTTPS** - Security limitation
- **All monitors as one** - Multi-monitor screenshots captured as single image
- **No session management** - Stateless requests only
- **Process operations** - Some require Administrator privileges
- **File system access** - Limited by server process permissions

## Performance Notes

**Resource Usage:**
- **Memory**: ~100MB base + ~2-5MB per screenshot in history
- **CPU**: <5% during normal monitoring, spikes during screenshots
- **Disk**: ~1-3MB per screenshot
- **Network**: ~100-500KB per screenshot transfer

**Optimization Tips:**
- Increase screenshot interval to reduce disk usage
- Enable motion detection to skip idle screenshots
- Set lower data retention days
- Limit screenshot history size
- Close unused server tabs in client
- Disable auto-refresh when not needed

## License & Disclaimer

This software is provided **as-is** for **educational purposes only**. 

**No warranty** of any kind is provided. The authors are **not liable** for:
- Misuse of this software
- Legal violations by users
- Data loss or corruption
- Privacy violations
- Any damages resulting from use

Users are **solely responsible** for:
- Compliance with all applicable laws
- Obtaining proper consent
- Securing data appropriately
- Ethical use of monitoring capabilities

## Support & Contributing

This is an educational project created for learning purposes.

**For issues:**
1. Review troubleshooting section above
2. Check `config.json` configuration
3. Review console output/logs
4. Verify network connectivity
5. Check Windows Event Viewer (for service issues)

**Future Enhancements:**
- HTTPS/TLS encryption support
- Multi-user authentication
- Database backend (SQLite)
- Web-based client interface
- Cross-platform server support
- Real-time streaming (WebSockets)
- Mobile app client
- Multi-monitor handling
- Session recording/playback
- File transfer completion
- Registry editing
- Network monitoring
- Webcam capture

---

**Remember: Use responsibly and legally. Always obtain proper authorization before monitoring any computer system. This is a learning tool - understand the implications of surveillance technology.**