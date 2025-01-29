<p align="center">
  <img src="static/simpleguardhome.png" alt="SimpleGuardHome Logo" width="200">
</p>

<h1 align="center">SimpleGuardHome</h1>

<p align="center">
  <a href="https://github.com/pacnpal/simpleguardhome/releases"><img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version 0.1.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
</p>

A modern web application for checking and managing domain filtering in AdGuard Home. Built with FastAPI and modern JavaScript, following the official AdGuard Home OpenAPI specification.

## Quick Start

```bash
# Using Docker
docker run -d -p 8000:8000 -e ADGUARD_HOST=http://localhost -e ADGUARD_PORT=3000 pacnpal/simpleguardhome:latest

# Or using Python
pip install simpleguardhome
python -m uvicorn simpleguardhome.main:app --port 8000
```

Then visit `http://localhost:8000` to start managing your AdGuard Home filtering.

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
- 🐳 Docker support

## Requirements

### System Requirements
- Python 3.9 or higher (for local installation)
- Running AdGuard Home instance
- AdGuard Home API credentials
- Docker (optional, for containerized deployment)

### Python Dependencies
- FastAPI - Web framework for building APIs
- Uvicorn - ASGI server implementation
- Python-dotenv - Environment variable management
- HTTPX - Modern HTTP client
- Pydantic - Data validation using Python type annotations
- Jinja2 - Template engine for the web interface

## Docker Installation

The easiest way to get started is using Docker:

1. Pull the Docker image:
```bash
docker pull pacnpal/simpleguardhome:latest
```

2. Create a `.env` file with your AdGuard Home settings:
```env
ADGUARD_HOST=http://localhost    # AdGuard Home host URL
ADGUARD_PORT=3000               # AdGuard Home API port
ADGUARD_USERNAME=admin          # Required: AdGuard Home username
ADGUARD_PASSWORD=password       # Required: AdGuard Home password
```

3. Run the container:
```bash
docker run -d \
  --name simpleguardhome \
  -p 8000:8000 \
  --env-file .env \
  pacnpal/simpleguardhome:latest
```

The application will be available at `http://localhost:8000`

### Docker Compose

Alternatively, you can use Docker Compose. Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  simpleguardhome:
    image: pacnpal/simpleguardhome:latest
    container_name: simpleguardhome
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

## Local Installation

1. Clone this repository:
```bash
git clone https://github.com/pacnpal/simpleguardhome.git
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
ADGUARD_USERNAME=admin          # Required: AdGuard Home username
ADGUARD_PASSWORD=password       # Required: AdGuard Home password
```

## Running the Application

### Local Development
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
├── static/
│   └── simpleguardhome.png  # Project logo
├── requirements.txt
├── setup.py
├── .env.example
├── Dockerfile
├── docker-compose.yml
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