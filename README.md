# SimpleGuardHome

A simple web application for checking and managing domain filtering in AdGuard Home.

## Features

- Check if domains are blocked by your AdGuard Home instance
- One-click domain unblocking
- Modern, responsive web interface
- Secure integration with AdGuard Home API

## Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/simpleguardhome.git
cd simpleguardhome
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure your environment:
```bash
cp .env.example .env
```

Edit `.env` with your AdGuard Home instance details:
```
ADGUARD_HOST=http://localhost
ADGUARD_PORT=3000
ADGUARD_USERNAME=your_username
ADGUARD_PASSWORD=your_password
```

## Running the Application

Start the application:
```bash
python -m src.simpleguardhome.main
```

Visit `http://localhost:8000` in your web browser.

## Usage

1. Enter a domain in the input field
2. Click "Check Domain" or press Enter
3. View the domain's blocking status
4. If blocked, use the "Unblock Domain" button to whitelist it

## Development

The application is built with:
- FastAPI for the backend
- Tailwind CSS for styling
- Modern JavaScript for frontend interactivity

## License

MIT License - See LICENSE file for details
