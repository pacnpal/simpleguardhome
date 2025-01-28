from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import httpx
import logging
from typing import Dict
from . import adguard
from .config import settings
from .adguard import AdGuardError, AdGuardConnectionError, AdGuardAPIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SimpleGuardHome")

# Setup templates directory
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/health")
async def health_check() -> Dict:
    """Check the health of the application and AdGuard Home connection."""
    try:
        async with adguard.AdGuardClient() as client:
            status = await client.get_filter_status()
            return {
                "status": "healthy",
                "adguard_connection": "connected",
                "filtering_enabled": status.get("enabled", False)
            }
    except AdGuardConnectionError:
        return {
            "status": "degraded",
            "adguard_connection": "failed",
            "error": "Could not connect to AdGuard Home"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.exception_handler(AdGuardError)
async def adguard_exception_handler(request: Request, exc: AdGuardError) -> JSONResponse:
    """Handle AdGuard-related exceptions."""
    if isinstance(exc, AdGuardConnectionError):
        status_code = 503  # Service Unavailable
    elif isinstance(exc, AdGuardAPIError):
        status_code = 502  # Bad Gateway
    else:
        status_code = 500  # Internal Server Error
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc.__class__.__name__,
            "detail": str(exc)
        }
    )

@app.post("/check-domain")
async def check_domain(domain: str = Form(...)) -> Dict:
    """Check if a domain is blocked by AdGuard Home."""
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")
    
    logger.info(f"Checking domain: {domain}")
    try:
        async with adguard.AdGuardClient() as client:
            result = await client.check_domain(domain)
            response = {
                "success": True,
                "domain": domain,
                "blocked": result.get("filtered", False),
                "rule": result.get("rule", ""),
                "filter_list": result.get("filter_list", "")
            }
            logger.info(f"Domain check result: {response}")
            return response
    except Exception as e:
        logger.error(f"Error checking domain {domain}: {str(e)}")
        raise

@app.post("/unblock-domain")
async def unblock_domain(domain: str = Form(...)) -> Dict:
    """Add a domain to the allowed list."""
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")
    
    logger.info(f"Unblocking domain: {domain}")
    try:
        async with adguard.AdGuardClient() as client:
            await client.add_allowed_domain(domain)
            response = {
                "success": True,
                "domain": domain,
                "message": f"Successfully unblocked {domain}"
            }
            logger.info(f"Domain unblock result: {response}")
            return response
    except Exception as e:
        logger.error(f"Error unblocking domain {domain}: {str(e)}")
        raise

def start():
    """Start the application using uvicorn."""
    import uvicorn
    uvicorn.run(
        "simpleguardhome.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    start()