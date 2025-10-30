# PC Monitor - Remote Activity Monitoring System

A Python-based client-server system for remotely monitoring PC activity including keystrokes, mouse movements, window changes, and automatic screenshots. Designed for educational purposes to learn remote monitoring techniques.

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

### Security Features
- 🔑 **API Key Authentication** - Protect server access
- 🛑 **Kill Switch** - Remotely terminate server from client
- 📁 **Auto Data Cleanup** - Configurable retention policies
- 🔒 **Request Authentication** - All endpoints require valid API key

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

**Step 2: Deploy Server to Target PC**
1. Copy `dist/PCMonitor.exe` to target computer
2. Run `PCMonitor.exe` (first run creates configuration)
3. Check `SERVER_INFO.txt` or `config.json` for the API key
4. Find the server's IP address using `ipconfig` in Command Prompt
5. Keep `PCMonitor.exe` running

**Step 3: Setup Client on Monitoring PC**
1. Copy `dist/PCMonitorClient.exe` to your computer
2. Run `PCMonitorClient.exe`
3. Go to **Settings → Change Server**
4. Enter server URL: `http://<SERVER_IP>:5000`
5. Enter the API key from Step 2
6. Click **Save & Connect**
7. Click **Start** to begin monitoring

### Option 2: Running from Source

**Install Dependencies:**
```bash
pip install flask flask-cors pynput pillow pywin32 requests
```

**Start Server (Target PC):**
```bash
python server.py
```
- On first run, `config.json` and `SERVER_INFO.txt` are created
- Note the API key displayed in console/files
- Server runs on port 5000 by default

**Start Client (Monitoring PC):**
```bash
python client.py
```
- Edit `client_config.json` with server URL and API key
- Or use Settings menu in the GUI

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

### Client Configuration (`client_config.json`)

Auto-generated on first run, or configure via GUI:

```json
{
    "server_url": "http://192.168.0.48:5000",
    "api_key": "YOUR_SECRET_KEY_HERE"
}
```

**How to Configure:**
1. Run `PCMonitorClient.exe`
2. Go to **Settings → Change Server**
3. Enter server URL and API key
4. Click **Save & Connect**

## Network Setup

### Finding Server IP Address

**On Windows (Target PC):**
```bash
ipconfig
```
Look for **IPv4 Address** under your active network adapter (e.g., `192.168.0.48`)

**On macOS/Linux:**
```bash
ifconfig
# or
ip addr show
```

### Firewall Configuration

**Windows Firewall (Required):**

Via GUI:
1. Open **Windows Defender Firewall with Advanced Security**
2. Click **Inbound Rules → New Rule**
3. Select **Port** → Next
4. Enter port `5000` (or your custom port) → Next
5. Select **Allow the connection** → Next
6. Apply to all profiles → Next
7. Name: "PC Monitor Server" → Finish

Via Command Line (Administrator):
```bash
netsh advfirewall firewall add rule name="PC Monitor" dir=in action=allow protocol=TCP localport=5000
```

### Testing Connection

From monitoring PC:
```bash
# Test if server is reachable
ping <SERVER_IP>

# Test if port is open (using telnet or powershell)
Test-NetConnection -ComputerName <SERVER_IP> -Port 5000
```

## Usage Guide

### Server Operations

**Starting the Server:**
- Double-click `PCMonitor.exe`, or
- Run `python server.py`

**First-Time Setup:**
1. Server creates `config.json` with API key
2. Server creates `SERVER_INFO.txt` with connection details
3. Copy API key for client configuration
4. Note your IP address (use `ipconfig`)

**Server runs continuously** - keep the window/process running while monitoring.

### Client Interface Guide

#### Main Window

**Status Bar** (Top):
- 🟢 **Green** = Monitoring active
- 🔴 **Red** = Monitoring stopped
- Shows: PC name, event count, keystroke count

**Control Buttons:**
- **Refresh** - Manually update status
- **Start** - Begin monitoring on server
- **Stop** - Pause monitoring on server
- **Snapshot** - Take immediate screenshot
- **⚠ KILL SERVER** - Emergency stop (terminates server process)
- **Auto-refresh** - Enable automatic updates (15 seconds)

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
- Updates every 500ms when tab is active

**Keystroke Buffer:**
- Shows detailed keystroke history
- Includes timestamp and window context
- Click "Load Buffer" to fetch from server
- Click "Export Text" to save to file

**Controls:**
- **Show All Keys** - Display all keystrokes including special keys
- **Clear** - Clear live feed display
- **Export Text** - Save to text file

#### Tab 3: Screenshot Gallery

- View all captured screenshots
- Double-click to view full size
- Select to preview in panel
- Click "Refresh Gallery" to update list
- Screenshots sorted by newest first

#### Tab 4: Search & Filter

**Search Controls:**
- **Search** - Text search in events
- **Event Type** - Filter by: mouse_click, key_press, window_change, screenshot
- **Date Range** - Filter by start/end date (YYYY-MM-DD format)

**Actions:**
- **Search** - Apply filters
- **Clear** - Reset all filters
- **Export Results** - Save filtered results to file

### Menu Bar Features

**Settings Menu:**
- **Change Server** - Update server URL and API key
- **Screenshot Settings** - Configure automatic screenshots
  - Enable/disable auto-screenshots
  - Set interval (60-3600 seconds)

**Tools Menu:**
- **Export Events** - Export all events to JSON
- **Export Keystrokes** - Export keystroke log to JSON
- **Remote Control** - Execute remote commands
  - Shutdown/Restart PC
  - Launch applications
  - Execute shell commands

**Help Menu:**
- **About** - Software information

### Remote Control Features

**System Controls:**
- **Shutdown PC** - Initiates shutdown (10 second delay)
- **Restart PC** - Initiates restart (10 second delay)

**Launch Application:**
- Enter application path or name
- Examples: `notepad.exe`, `C:\Program Files\...`

**Execute Shell Command:**
- Run any Windows command
- View output (STDOUT/STDERR)
- See return code
- Examples: `dir`, `ipconfig`, `tasklist`

### Screenshot Settings

Configure automatic screenshot behavior:

1. Go to **Settings → Screenshot Settings**
2. **Enable Automatic Screenshots** - Check to enable
3. **Interval** - Set seconds between captures
   - 60s = 1 minute
   - 300s = 5 minutes (default)
   - 600s = 10 minutes
4. Click **Save Settings**

**Motion Detection:**
- Edit `config.json` manually
- Set `"motion_detection": true`
- Only captures screenshots during user activity
- Saves disk space during idle periods

## Data Storage

### Directory Structure

```
PCMonitor.exe location/
├── config.json              # Server configuration
├── SERVER_INFO.txt          # Connection information
└── monitor_data/            # Data directory (auto-created)
    ├── screenshots/         # PNG screenshot files
    │   ├── screenshot_20250129_120000.png
    │   ├── screenshot_20250129_120300.png
    │   └── ...
    └── offline_logs/        # Offline event logs
        └── offline_2025-01-29.jsonl

PCMonitorClient.exe location/
└── client_config.json       # Client configuration
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
- Runs automatically
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
   - Check `SERVER_INFO.txt` or `config.json` for API key
2. **With console** - Debug mode
   - Shows output window
   - Displays API key on first run
   - Useful for troubleshooting

### Optimization
1. **Normal build** - Faster build, larger file size
2. **Optimized** - Slower build, smaller file (UPX compression)

**Build Output:**
- Creates `dist/` folder with executables
- Creates `SERVER_INFO.txt` with setup instructions
- Opens `dist` folder automatically when complete

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

### Client Issues

**"Cannot connect to server"**
- Verify server is running: check Task Manager
- Check IP address is correct
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
- Verify `auto_screenshot` is enabled in settings
- Check screenshot interval setting
- Ensure activity is occurring
- Check disk space available

**Client GUI not responding**
- Check network connection to server
- Disable auto-refresh temporarily
- Close and restart client
- Check server is still running

### Network Issues

**Can't access server from client**
1. Verify server IP: `ipconfig` on server
2. Test ping: `ping <SERVER_IP>` from client
3. Check firewall: Allow port 5000 inbound
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
pip install flask flask-cors pynput pillow pywin32 requests
```

**Build fails with errors**
- Delete `build/` and `dist/` folders
- Delete `.spec` files
- Run `build.bat` again
- Check Python version (3.7+ required)

## Security Considerations

### Essential Security Steps

1. **Change API Key Immediately**
   - Generate strong key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Update `config.json` on server
   - Update `client_config.json` or GUI settings on client

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

## Known Limitations

- **Windows-only server** - Window tracking requires Windows
- **No encryption** - HTTP traffic is plain text
- **Basic authentication** - Single API key only
- **No HTTPS** - Security limitation
- **Single-user** - One server, multiple clients not tested
- **All monitors as one** - Multi-monitor screenshots captured as single image
- **No session management** - Stateless requests only
- **In-memory storage** - Events lost if server crashes (before written to log)

## Performance Notes

**Resource Usage:**
- **Memory**: ~100MB base + ~2-5MB per screenshot in history
- **CPU**: <5% during normal monitoring
- **Disk**: ~1-3MB per screenshot
- **Network**: ~100-500KB per screenshot transfer

**Optimization Tips:**
- Increase screenshot interval to reduce disk usage
- Enable motion detection to skip idle screenshots
- Set lower data retention days
- Limit screenshot history size in code if needed

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
5. Check Windows Event Viewer

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

---

**Remember: Use responsibly and legally. Always obtain proper authorization before monitoring any computer system. This is a learning tool - understand the implications of surveillance technology.**
