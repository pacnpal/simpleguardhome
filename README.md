# SimpleGuardHome

A modern web application for checking and managing domain filtering in AdGuard Home. Built with FastAPI and modern JavaScript, following the official AdGuard Home OpenAPI specification.

## Features

- 🔍 Real-time domain filtering status checks
- 🚫 One-click domain unblocking
- 💻 Modern, responsive web interface with Tailwind CSS
- 🔄 Live feedback and error handling
- 📝 Comprehensive logging
- 🏥 Health monitoring endpoint
- ⚙️ Environment-based configuration
- 📚 Full OpenAPI/Swagger documentation
- ✅ Implements official AdGuard Home API spec

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

## API Documentation

The API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI Schema: `http://localhost:8000/api/openapi.json`

### API Endpoints

All endpoints follow the official AdGuard Home API specification:

#### Web Interface
- `GET /` - Main web interface for domain checking and unblocking

#### Filtering Endpoints
- `POST /control/filtering/check_host` - Check if a domain is blocked
  - Parameters: `name` (query parameter)
  - Returns: Detailed filtering status and rules

- `POST /control/filtering/whitelist/add` - Add a domain to the allowed list
  - Parameters: `name` (JSON body)
  - Returns: Success status

- `GET /control/filtering/status` - Get current filtering configuration
  - Returns: Complete filtering status including rules and filters

#### System Status
- `GET /control/status` - Check application and AdGuard Home connection status
  - Returns: Health status with filtering state

## Response Models

The application uses Pydantic models that match the AdGuard Home API specification:

### FilterStatus
```python
{
    "enabled": bool,
    "filters": [
        {
            "enabled": bool,
            "id": int,
            "name": str,
            "rules_count": int,
            "url": str
        }
    ],
    "user_rules": List[str],
    "whitelist_filters": List[Filter]
}
```

### DomainCheckResult
```python
{
    "reason": str,  # Filtering status (e.g., "FilteredBlackList")
    "rule": str,    # Applied filtering rule
    "filter_id": int,  # ID of the filter containing the rule
    "service_name": str,  # For blocked services
    "cname": str,   # For CNAME rewrites
    "ip_addrs": List[str]  # For A/AAAA rewrites
}
```

## Error Handling

The application implements proper error handling according to the AdGuard Home API spec:

- 400 Bad Request - Invalid input
- 401 Unauthorized - Authentication required
- 403 Forbidden - Authentication failed
- 502 Bad Gateway - AdGuard Home API error
- 503 Service Unavailable - AdGuard Home unreachable

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
   - Follow AdGuard Home OpenAPI spec

2. Frontend Changes:
   - Modify `templates/index.html`
   - Use Tailwind CSS for styling
   - Follow existing error handling patterns

## Security Notes

- API credentials are handled via environment variables
- Connections use proper error handling and timeouts
- Input validation is performed on all endpoints
- CORS protection with proper headers
- Rate limiting on sensitive endpoints
- Session-based authentication with AdGuard Home
- Sensitive information is not exposed in responses

## License

MIT License - See LICENSE file for details
