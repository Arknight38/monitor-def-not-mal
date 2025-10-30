# PC Monitor - Remote Activity Monitoring System

A Python-based client-server system for remotely monitoring PC activity including mouse movements, keyboard inputs, window changes, and periodic screenshots.

## ⚠️ Important Disclaimers

**Legal & Ethical Use Only:**
- This software is intended for legitimate use cases only (parental monitoring, employee monitoring with consent, personal device tracking)
- You must have legal authorization to monitor any computer
- Unauthorized monitoring may violate privacy laws and workplace policies
- Always obtain explicit consent before deploying
- Review local laws regarding computer monitoring in your jurisdiction

**Security Warning:**
- Data transmitted over HTTP is **not encrypted**
- Screenshots and activity logs contain sensitive information
- Change the default API key immediately
- Use on trusted networks only
- Consider implementing VPN for remote access

## Features

- 🖱️ **Mouse Activity Tracking** - Captures clicks and movements
- ⌨️ **Keyboard Monitoring** - Logs key presses
- 🪟 **Window Tracking** - Records active window changes
- 📸 **Periodic Screenshots** - Automatic screenshots during activity
- 🌐 **Remote Dashboard** - Real-time monitoring from any device
- 🔐 **API Key Authentication** - Basic security layer
- 📊 **Activity Logging** - JSON-based event storage
- ⚡ **Auto-start Option** - Begin monitoring on launch

## System Requirements

### Server (Target PC)
- Windows OS (for win32gui window tracking)
- Python 3.7+ OR standalone executable
- Network connectivity
- Required Python packages (if not using exe):
  - Flask
  - flask-cors
  - pynput
  - Pillow
  - pywin32

### Client (Monitoring Device)
- Python 3.7+
- Network access to server
- Required packages:
  - tkinter (usually included with Python)
  - requests
  - Pillow

## Installation

### Option 1: Using Standalone Executable (Recommended)

1. **Build the server executable:**
   ```bash
   # On the development machine
   python -m pip install pyinstaller
   build.bat
   ```

2. **Deploy to target PC:**
   - Copy `dist/PCMonitor.exe` to target computer
   - Run once to generate `config.json`
   - Edit `config.json` with your settings
   - Run `PCMonitor.exe` again

### Option 2: Running from Source

1. **Clone or download the repository**

2. **Install dependencies:**
   ```bash
   pip install flask flask-cors pynput pillow pywin32 requests
   ```

3. **Server Setup (Target PC):**
   ```bash
   python server.py
   ```
   - Edit `config.json` after first run
   - Restart server

4. **Client Setup (Monitoring Device):**
   ```bash
   python client.py
   ```
   - Edit `client_config.json` with server details

## Configuration

### Server Configuration (`config.json`)

```json
{
    "api_key": "YOUR_SECRET_KEY_HERE",
    "port": 5000,
    "screenshot_interval": 15,
    "auto_start": true
}
```

**Options:**
- `api_key` - Secret key for API authentication (**change this!**)
- `port` - Server port (default: 5000)
- `screenshot_interval` - Seconds between screenshots (default: 15)
- `auto_start` - Start monitoring automatically on launch (default: true)

### Client Configuration (`client_config.json`)

```json
{
    "server_url": "http://192.168.1.100:5000",
    "api_key": "YOUR_SECRET_KEY_HERE"
}
```

**Options:**
- `server_url` - Full URL to server (include http:// and port)
- `api_key` - Must match server's API key

## Network Setup

### Finding Your Server IP Address

On the target PC (Windows):
```bash
ipconfig
```
Look for "IPv4 Address" under your active network adapter.

### Firewall Configuration

You need to allow incoming connections on the server port:

**Windows Firewall:**
1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Select "Inbound Rules"
4. Click "New Rule..."
5. Choose "Port" → Next
6. Enter your port (default: 5000) → Next
7. Allow the connection → Next
8. Apply to all profiles → Next
9. Name it "PC Monitor Server" → Finish

**Or via Command Line (Run as Administrator):**
```bash
netsh advfirewall firewall add rule name="PC Monitor" dir=in action=allow protocol=TCP localport=5000
```

## Usage

### Starting the Server

**Using Executable:**
```bash
PCMonitor.exe
```

**Using Python:**
```bash
python server.py
```

The server will display:
- Local IP address
- Port number
- API key
- Connection instructions

**Keep the server window open while monitoring.**

### Starting the Client

```bash
python client.py
```

Or use the GUI to:
- View server status
- Start/Stop monitoring
- View live screenshots
- Browse activity log
- Take manual snapshots

### Client Interface

**Status Bar:**
- 🟢 Green = Monitoring active
- 🔴 Red = Monitoring stopped
- Shows event count

**Controls:**
- **Refresh** - Update status manually
- **Start Monitoring** - Begin activity tracking
- **Stop Monitoring** - Pause tracking
- **Take Snapshot Now** - Force immediate screenshot
- **Auto-refresh** - Enable/disable 10-second updates

**Live View Panel:**
- Displays latest screenshot
- Updates automatically
- Click "Refresh Screenshot" for manual update

**Activity Log Panel:**
- Real-time event stream
- Shows timestamps, event types, details
- Auto-scrolls to latest events

## API Endpoints

### Public Endpoints

#### `GET /api/status`
Get server status (no authentication required)

**Response:**
```json
{
    "monitoring": true,
    "event_count": 1523,
    "last_activity": 1698765432.123
}
```

### Authenticated Endpoints

All require `X-API-Key` header matching server's API key.

#### `POST /api/start`
Start monitoring

#### `POST /api/stop`
Stop monitoring

#### `GET /api/events?limit=100`
Get recent events

#### `GET /api/screenshots`
List all screenshots with metadata

#### `GET /api/screenshot/latest`
Get latest screenshot as base64

#### `GET /api/screenshot/<filename>`
Download specific screenshot file

#### `POST /api/snapshot`
Take immediate screenshot

#### `POST /api/shutdown`
Shutdown server

### Example API Usage

```python
import requests

headers = {'X-API-Key': 'YOUR_SECRET_KEY'}
server = 'http://192.168.1.100:5000'

# Start monitoring
requests.post(f'{server}/api/start', headers=headers)

# Get events
events = requests.get(f'{server}/api/events?limit=50', headers=headers).json()

# Take snapshot
requests.post(f'{server}/api/snapshot', headers=headers)
```

## Data Storage

### Directory Structure

```
monitor_data/
├── screenshots/
│   ├── screenshot_20250101_120000.png
│   ├── screenshot_20250101_120015.png
│   └── ...
├── events_20250101.json
└── events_20250102.json
```

### Event Log Format

Each line in `events_YYYYMMDD.json`:
```json
{"timestamp": "2025-01-01T12:00:00.123456", "type": "mouse_click", "details": {"x": 100, "y": 200, "button": "Button.left"}}
```

**Event Types:**
- `monitoring_started` / `monitoring_stopped`
- `mouse_move` - Throttled (every 5 seconds)
- `mouse_click` - With coordinates and button
- `key_press` - With key name
- `window_change` - With window title
- `screenshot` - When screenshot taken

## Troubleshooting

### Server won't start
- Check if port is already in use
- Verify firewall allows the port
- Ensure config.json is valid JSON
- Check Python/library installations

### Client can't connect
- Verify server is running
- Check IP address is correct
- Ensure port matches server config
- Verify API key matches
- Test network connectivity: `ping [server-ip]`
- Check firewall on both machines

### No screenshots appearing
- Verify monitoring is started
- Check activity is occurring (idle = no screenshots)
- Review screenshot_interval setting
- Ensure sufficient disk space
- Check PIL/Pillow installation

### High memory usage
- Server stores all events in memory
- Restart server periodically for long sessions
- Reduce screenshot_interval
- Consider implementing log rotation

### Permission errors on Windows
- Run as administrator if needed
- Check antivirus isn't blocking
- Verify write permissions to data directory

## Security Best Practices

1. **Change Default API Key Immediately**
   - Use strong, random key (32+ characters)
   - Store securely

2. **Network Security**
   - Use on isolated/trusted networks
   - Consider VPN for remote access
   - Never expose directly to internet without HTTPS

3. **Access Control**
   - Limit physical access to server machine
   - Don't leave client credentials exposed
   - Use Windows user account restrictions

4. **Data Protection**
   - Regularly delete old screenshots/logs
   - Encrypt storage drive if possible
   - Secure client_config.json file permissions

5. **Compliance**
   - Document consent from monitored users
   - Follow data retention policies
   - Review GDPR/local privacy laws

## Known Limitations

- Windows-only server (due to win32gui)
- No HTTPS encryption
- Screenshots stored unencrypted
- Unlimited memory usage for events
- No built-in data retention/cleanup
- Basic authentication only
- No multi-user support
- Screenshots capture all monitors as one image

## Future Enhancements

- [ ] HTTPS/SSL support
- [ ] Screenshot encryption
- [ ] Configurable event filters
- [ ] Data retention policies
- [ ] Web-based client interface
- [ ] Mobile app client
- [ ] Multi-monitor screenshot handling
- [ ] Session recording/playback
- [ ] Alert notifications
- [ ] User authentication system
- [ ] Cross-platform support (macOS, Linux)

## Development

### Building from Source

Requirements in development:
```bash
pip install flask flask-cors pynput pillow pywin32 pyinstaller requests
```

### Running Tests

Currently no automated tests. Manual testing recommended:
1. Start server
2. Connect client
3. Test each button/feature
4. Verify event logging
5. Check screenshot capture

### Contributing

This is a reference implementation. Modifications suggested:
- Add proper error handling
- Implement logging framework
- Add unit tests
- Security hardening
- Cross-platform support

## License

This code is provided as-is for educational and legitimate monitoring purposes only. No warranty or liability is provided. Users are responsible for compliance with all applicable laws.

## Support

For issues or questions:
- Review troubleshooting section
- Check configuration files
- Verify network connectivity
- Review Windows Event Viewer for errors

## Changelog

**Version 1.0**
- Initial release
- Basic monitoring features
- Client-server architecture
- Screenshot capture
- Event logging

---

**Remember: Use responsibly and legally. Always obtain proper authorization before monitoring any computer system.**