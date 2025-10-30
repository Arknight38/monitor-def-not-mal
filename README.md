# PC Monitor - Remote Activity Monitoring System v2.0

A Python-based client-server system for remotely monitoring PC activity including mouse movements, keyboard inputs, window changes, and periodic screenshots with advanced security and configuration features.

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

## 🆕 What's New in v2.0

- ✅ **Rate Limiting** - Prevents API abuse (100 requests/minute)
- ✅ **Replay Attack Prevention** - Timestamp validation on requests
- ✅ **Configurable Monitoring** - Choose what to monitor
- ✅ **Data Retention Policies** - Auto-cleanup of old data
- ✅ **Keyword Notifications** - Alert on specific keywords
- ✅ **Log Export** - Export logs as JSON with date filtering
- ✅ **Improved Error Handling** - Better retry logic and error messages
- ✅ **Memory Management** - Prevents memory leaks from unlimited events
- ✅ **Logging System** - Detailed logging to monitor.log file

## Features

### Core Features
- 🖱️ **Mouse Activity Tracking** - Captures clicks and movements
- ⌨️ **Keyboard Monitoring** - Logs key presses
- 🪟 **Window Tracking** - Records active window changes
- 📸 **Periodic Screenshots** - Automatic screenshots during activity
- 🌐 **Remote Dashboard** - Real-time monitoring from any device

### Security Features
- 🔐 **API Key Authentication** - Basic security layer
- 🛡️ **Rate Limiting** - Protection against abuse
- ⏱️ **Replay Attack Prevention** - Timestamp validation
- 📝 **Activity Logging** - Detailed logging system

### Configuration Features
- ⚙️ **Selective Monitoring** - Enable/disable specific event types
- 🗑️ **Auto Data Cleanup** - Configurable retention periods
- 🔔 **Keyword Alerts** - Get notified on specific keywords
- 📊 **Log Export** - Export filtered logs to JSON

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
    "auto_start": true,
    "data_retention_days": 7,
    "monitoring": {
        "mouse_moves": true,
        "mouse_clicks": true,
        "keyboard": true,
        "windows": true,
        "screenshots": true
    },
    "notifications": {
        "enabled": false,
        "keywords": ["password", "confidential"],
        "log_file": "alerts.log"
    },
    "security": {
        "use_https": false,
        "request_timeout_seconds": 30
    }
}
```

**Main Options:**
- `api_key` - Secret key for API authentication (**change this!**)
- `port` - Server port (default: 5000)
- `screenshot_interval` - Seconds between screenshots (default: 15)
- `auto_start` - Start monitoring automatically on launch (default: true)
- `data_retention_days` - Days to keep logs/screenshots before auto-deletion (default: 7)

**Monitoring Options:**
- `mouse_moves` - Track mouse movements (throttled to every 5 seconds)
- `mouse_clicks` - Track mouse clicks
- `keyboard` - Track keyboard input
- `windows` - Track active window changes
- `screenshots` - Take periodic screenshots

**Notification Options:**
- `enabled` - Enable keyword notifications
- `keywords` - List of keywords to trigger alerts
- `log_file` - File to save alerts (default: alerts.log)

**Security Options:**
- `use_https` - HTTPS support (not implemented yet)
- `request_timeout_seconds` - Request timeout

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
- Security warnings
- Connection instructions

**Keep the server window open while monitoring.**

### Starting the Client

```bash
python client.py
```

### Client Interface

**Menu Bar:**
- **Settings** → Change Server, Configure Monitoring
- **Tools** → Export Logs, View Statistics
- **Help** → About

**Status Bar:**
- 🟢 Green = Monitoring active
- 🔴 Red = Monitoring stopped
- Shows event count and security warnings

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

### Configuring Monitoring

1. Open client → **Settings** → **Configure Monitoring**
2. Check/uncheck what you want to monitor:
   - Mouse Movements
   - Mouse Clicks
   - Keyboard Input
   - Window Changes
   - Screenshots
3. Set screenshot interval (5-300 seconds)
4. Click **Save Configuration**

### Exporting Logs

1. Open client → **Tools** → **Export Logs**
2. Optionally enter date range (YYYY-MM-DD format)
3. Click **Export to JSON File**
4. Choose save location
5. Logs are exported with all event details

### Keyword Notifications

To enable keyword alerts:

1. Edit `config.json` on server
2. Set `notifications.enabled` to `true`
3. Add keywords to `notifications.keywords` array
4. Restart server
5. Alerts will be logged to `alerts.log` in data directory

Example:
```json
"notifications": {
    "enabled": true,
    "keywords": ["password", "banking", "confidential", "secret"],
    "log_file": "alerts.log"
}
```

## API Endpoints

### Public Endpoints

#### `GET /api/status`
Get server status (no authentication required)

**Response:**
```json
{
    "monitoring": true,
    "event_count": 1523,
    "last_activity": 1698765432.123,
    "security_warning": "⚠️  HTTP connection is not encrypted!"
}
```

### Authenticated Endpoints

All require headers:
- `X-API-Key`: Your API key
- `X-Request-Time`: Current Unix timestamp (optional but recommended)

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

#### `GET /api/config`
Get current monitoring configuration

#### `POST /api/config`
Update monitoring configuration

**Request body:**
```json
{
    "monitoring": {
        "mouse_clicks": true,
        "keyboard": false
    },
    "screenshot_interval": 30
}
```

#### `GET /api/export?start=YYYY-MM-DD&end=YYYY-MM-DD`
Export logs for date range

#### `POST /api/shutdown`
Shutdown server

### Example API Usage

```python
import requests
import time

headers = {
    'X-API-Key': 'YOUR_SECRET_KEY',
    'X-Request-Time': str(time.time())
}
server = 'http://192.168.1.100:5000'

# Start monitoring
requests.post(f'{server}/api/start', headers=headers)

# Get events
events = requests.get(f'{server}/api/events?limit=50', headers=headers).json()

# Configure monitoring
config = {
    "monitoring": {
        "screenshots": False,
        "keyboard": True
    }
}
requests.post(f'{server}/api/config', json=config, headers=headers)

# Export logs
params = {'start': '2025-01-01', 'end': '2025-01-31'}
logs = requests.get(f'{server}/api/export', params=params, headers=headers).json()
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
├── events_20250102.json
└── alerts.log
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

### Alert Log Format

Each line in `alerts.log`:
```json
{"timestamp": "2025-01-01T12:00:00.123456", "keyword": "password", "event": {...}}
```

## Troubleshooting

### Common Errors

**"ImportError: No module named 'win32gui'"**
- Solution: `pip install pywin32`
- Window monitoring will be disabled on non-Windows systems

**"Rate limit exceeded"**
- Wait 1 minute before retrying
- Reduce refresh frequency

**"Unauthorized. Check your API key"**
- Verify API key matches in both config files
- Check for typos or extra spaces

**"Request timestamp outside valid window"**
- Check system clocks are synchronized
- Allow 30-second window for time differences

### Server won't start
- Check if port is already in use
- Verify firewall allows the port
- Ensure config.json is valid JSON
- Check Python/library installations
- Review `monitor.log` for errors

### Client can't connect
- Verify server is running
- Check IP address is correct
- Ensure port matches server config
- Verify API key matches exactly
- Test network connectivity: `ping [server-ip]`
- Check firewall on both machines

### No screenshots appearing
- Verify monitoring is started
- Check activity is occurring (idle = no screenshots)
- Check `monitoring.screenshots` is true in config
- Review screenshot_interval setting
- Ensure sufficient disk space
- Check PIL/Pillow installation

### High memory usage
- Check `data_retention_days` setting
- Reduce screenshot_interval
- Events are limited to 1000 in memory
- Restart server periodically for very long sessions

### Permission errors on Windows
- Run as administrator if needed
- Check antivirus isn't blocking
- Verify write permissions to data directory

## Security Best Practices

### Essential Steps

1. **Change Default API Key Immediately**
   - Use strong, random key (32+ characters)
   - Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Store securely

2. **Network Security**
   - Use on isolated/trusted networks only
   - Consider VPN for remote access
   - Never expose directly to internet
   - Use separate network segment if possible

3. **Access Control**
   - Limit physical access to server machine
   - Don't leave client credentials exposed
   - Use Windows user account restrictions
   - Lock workstation when away

4. **Data Protection**
   - Enable data retention policy (e.g., 7 days)
   - Encrypt storage drive if possible
   - Secure config file permissions
   - Regularly review and delete unnecessary data

5. **Monitoring Best Practices**
   - Disable unnecessary monitoring features
   - Use keyword alerts for sensitive terms
   - Review logs regularly
   - Keep server software updated

6. **Compliance**
   - Document consent from monitored users
   - Follow data retention policies
   - Review GDPR/local privacy laws
   - Maintain audit trail

### Rate Limiting

The server implements rate limiting to prevent abuse:
- **100 requests per minute** per client IP
- Excess requests return HTTP 429
- Window resets every 60 seconds
- Configurable in code if needed

### Replay Attack Prevention

Requests can include `X-Request-Time` header:
- Unix timestamp of request
- Server validates timestamp within 30-second window
- Prevents replaying captured requests
- Optional but recommended for sensitive operations

## Known Limitations

- Windows-only server (due to win32gui)
- No HTTPS encryption (HTTP only)
- Screenshots stored unencrypted
- Basic API key authentication only
- No multi-user support
- Screenshots capture all monitors as one image
- Rate limiting per IP (not per API key)
- No session management

## Performance Considerations

- **Memory**: ~50-100MB base + screenshots in memory
- **CPU**: Low (<5%) during normal monitoring
- **Disk**: ~1-5MB per screenshot, log files minimal
- **Network**: ~100-500KB per screenshot transfer
- **Events**: Limited to 1000 in memory to prevent leaks

## Future Enhancements

- [ ] HTTPS/SSL support with self-signed certificates
- [ ] Screenshot encryption at rest
- [ ] Database backend (SQLite) instead of JSON files
- [ ] Web-based client interface
- [ ] Mobile app client
- [ ] Multi-monitor screenshot handling
- [ ] Session recording/playback
- [ ] Email notifications for alerts
- [ ] User authentication system (multi-user)
- [ ] Cross-platform support (macOS, Linux)
- [ ] OAuth2 authentication
- [ ] Webhook integrations
- [ ] Real-time streaming instead of polling

## Development

### Building from Source

Requirements:
```bash
pip install flask flask-cors pynput pillow pywin32 pyinstaller requests
```

### Project Structure

```
pc-monitor/
├── server.py              # Server application
├── client.py              # Client GUI application
├── build.bat              # Build script for executable
├── config.json            # Server configuration
├── client_config.json     # Client configuration
├── monitor.log            # Server log file
├── README.md              # This file
└── monitor_data/          # Data directory (generated)
    ├── screenshots/       # Screenshot storage
    ├── events_*.json      # Event logs
    └── alerts.log         # Keyword alerts
```

### Running Tests

Currently no automated tests. Manual testing recommended:
1. Start server with various configurations
2. Connect client and test each feature
3. Test rate limiting (make rapid requests)
4. Verify event logging
5. Test screenshot capture
6. Verify data cleanup
7. Test export functionality
8. Check keyword notifications

### Contributing

Suggested improvements:
- Add unit tests and integration tests
- Implement HTTPS support
- Add database backend option
- Improve cross-platform support
- Add more authentication methods
- Implement encryption for sensitive data
- Add comprehensive error recovery

## FAQ

**Q: Can I monitor multiple PCs?**
A: Yes, run server on each PC with different ports or IPs. Client can switch between servers via Settings menu.

**Q: How much disk space is needed?**
A: Depends on usage. With default 15s screenshot interval and 7-day retention:
- ~240 screenshots/hour
- ~1-2MB per screenshot
- ~288MB per day
- ~2GB for 7 days

**Q: Can I use this remotely over internet?**
A: Not recommended without VPN. HTTP is unencrypted and insecure over public networks.

**Q: Does it work on Mac/Linux?**
A: Client works on all platforms. Server requires Windows for window tracking. Partial functionality available on other OS.

**Q: How do I reset the API key?**
A: Edit config.json on server, update client_config.json on client, restart both.

**Q: Can the monitored user detect this?**
A: Yes - server window runs visibly. This is intentional for ethical monitoring with consent.

**Q: What happens if server crashes?**
A: Monitoring stops. All data on disk is preserved. Restart server to resume.

**Q: Can I access from my phone?**
A: Not directly. A web-based interface would be needed (future enhancement).

## License

This code is provided as-is for educational and legitimate monitoring purposes only. No warranty or liability is provided. Users are responsible for compliance with all applicable laws and regulations.

## Support

For issues or questions:
1. Review troubleshooting section
2. Check configuration files
3. Review `monitor.log` for detailed errors
4. Verify network connectivity
5. Check Windows Event Viewer for system errors

## Changelog

**Version 2.0** (Current)
- Added rate limiting (100 req/min)
- Added replay attack prevention
- Added configurable monitoring options
- Added data retention and auto-cleanup
- Added keyword notification system
- Added log export functionality
- Added retry logic and better error handling
- Added memory leak prevention
- Added comprehensive logging system
- Added configuration management via API
- Improved security warnings
- Enhanced client interface with new features

**Version 1.0**
- Initial release
- Basic monitoring features
- Client-server architecture
- Screenshot capture
- Event logging

---

**Remember: Use responsibly and legally. Always obtain proper authorization before monitoring any computer system.**