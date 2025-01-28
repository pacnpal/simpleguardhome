# SimpleGuardHome

A modern web application for checking and managing domain filtering in AdGuard Home. Built with FastAPI and modern JavaScript.

## Features

- 🔍 Real-time domain filtering status checks
- 🚫 One-click domain unblocking
- 💻 Modern, responsive web interface with Tailwind CSS
- 🔄 Live feedback and error handling
- 📝 Comprehensive logging
- 🏥 Health monitoring endpoint
- ⚙️ Environment-based configuration

## Requirements

- Python 3.9 or higher
- Running AdGuard Home instance
- AdGuard Home API credentials (if authentication is enabled)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/simpleguardhome.git
cd simpleguardhome
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your AdGuard Home settings:
```env
ADGUARD_HOST=http://localhost    # AdGuard Home host URL
ADGUARD_PORT=3000               # AdGuard Home API port
ADGUARD_USERNAME=admin          # Optional: AdGuard Home username
ADGUARD_PASSWORD=password       # Optional: AdGuard Home password
```

## Running the Application

Start the application:
```bash
python -m uvicorn src.simpleguardhome.main:app --reload
```

The application will be available at `http://localhost:8000`

## API Endpoints

### Web Interface
- `GET /` - Main web interface for domain checking and unblocking

### API Endpoints
- `POST /check-domain` - Check if a domain is blocked
  - Parameters: `domain` (form data)
  - Returns: Blocking status and rule information

- `POST /unblock-domain` - Add a domain to the allowed list
  - Parameters: `domain` (form data)
  - Returns: Success/failure status

- `GET /health` - Check application and AdGuard Home connection status
  - Returns: Health status of the application and AdGuard Home connection

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure AdGuard Home is running
   - Verify the host and port in .env are correct
   - Check if AdGuard Home's API is accessible

2. **Authentication Failed**
   - Verify username and password in .env
   - Ensure AdGuard Home authentication is enabled/disabled as expected

3. **Domain Check Failed**
   - Check AdGuard Home logs for filtering issues
   - Verify domain format is correct
   - Ensure AdGuard Home filtering is enabled

### Checking System Status

1. Use the health check endpoint:
```bash
curl http://localhost:8000/health
```

2. Check application logs:
- The application uses structured logging
- Look for ERROR level messages for issues
- Connection problems are logged with detailed error information

## Development

### Project Structure

```
simpleguardhome/
├── src/
│   └── simpleguardhome/
│       ├── __init__.py
│       ├── main.py          # FastAPI application
│       ├── config.py        # Configuration management
│       ├── adguard.py       # AdGuard Home API client
│       └── templates/
│           └── index.html   # Web interface
├── requirements.txt
├── setup.py
├── .env.example
└── README.md
```

### Adding New Features

1. Backend Changes:
   - Add routes in `main.py`
   - Extend AdGuard client in `adguard.py`
   - Update configuration in `config.py`

2. Frontend Changes:
   - Modify `templates/index.html`
   - Use Tailwind CSS for styling
   - Follow existing error handling patterns

## Security Notes

- API credentials are handled via environment variables
- Connections use proper error handling and timeouts
- Input validation is performed on all endpoints
- Sensitive information is not exposed in responses

## License

MIT License - See LICENSE file for details
