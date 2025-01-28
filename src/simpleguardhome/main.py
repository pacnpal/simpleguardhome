from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import httpx
import logging
from typing import Dict
from . import adguard
from .config import settings
from .adguard import (
    AdGuardError,
    AdGuardConnectionError,
    AdGuardAPIError,
    DomainCheckResult,
    FilterStatus
)
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
app = FastAPI(
    title="SimpleGuardHome",
    description="AdGuard Home REST API interface",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware with security headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Setup templates directory
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Response models matching AdGuard spec
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    adguard_connection: str
    filtering_enabled: bool = False
    error: str = None

class DomainResponse(BaseModel):
    """Domain check response model matching AdGuard spec."""
    success: bool
    domain: str
    filtered: bool = False
    reason: str = None
    rule: str = None
    filter_list_id: int = None
    service_name: str = None
    cname: str = None
    ip_addrs: list[str] = None
    message: str = None

class ErrorResponse(BaseModel):
    """Error response model matching AdGuard spec."""
    message: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get(
    "/control/status",
    response_model=HealthResponse,
    responses={
        200: {"description": "OK"},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    tags=["health"]
)
async def health_check() -> Dict:
    """Check the health of the application and AdGuard Home connection."""
    try:
        async with adguard.AdGuardClient() as client:
            status = await client.get_filter_status()
            return {
                "status": "healthy",
                "adguard_connection": "connected",
                "filtering_enabled": status.enabled if status else False
            }
    except AdGuardConnectionError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "adguard_connection": "failed",
                "error": "Could not connect to AdGuard Home"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": "An internal error has occurred. Please try again later."
            }
        )

@app.exception_handler(AdGuardError)
async def adguard_exception_handler(request: Request, exc: AdGuardError) -> JSONResponse:
    """Handle AdGuard-related exceptions according to spec."""
    if isinstance(exc, AdGuardConnectionError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, AdGuardAPIError):
        status_code = status.HTTP_502_BAD_GATEWAY
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content={"message": str(exc)}
    )

@app.post(
    "/control/filtering/check_host",
    response_model=DomainResponse,
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request", "model": ErrorResponse},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def check_domain(domain: str = Form(...)) -> Dict:
    """Check if a domain is blocked by AdGuard Home."""
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain is required"
        )
    
    logger.info(f"Checking domain: {domain}")
    try:
        async with adguard.AdGuardClient() as client:
            result = await client.check_domain(domain)
            response = {
                "success": True,
                "domain": domain,
                "filtered": result.reason.startswith("Filtered"),
                "reason": result.reason,
                "rule": result.rule,
                "filter_list_id": result.filter_id,
                "service_name": result.service_name,
                "cname": result.cname,
                "ip_addrs": result.ip_addrs
            }
            logger.info(f"Domain check result: {response}")
            return response
    except Exception as e:
        logger.error(f"Error checking domain {domain}: {str(e)}")
        raise

@app.post(
    "/control/filtering/whitelist/add",
    response_model=DomainResponse,
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request", "model": ErrorResponse},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def unblock_domain(domain: str = Form(...)) -> Dict:
    """Add a domain to the allowed list."""
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain is required"
        )
    
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

@app.get(
    "/control/filtering/status",
    response_model=FilterStatus,
    responses={
        200: {"description": "OK"},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def get_filtering_status() -> FilterStatus:
    """Get the current filtering status."""
    try:
        async with adguard.AdGuardClient() as client:
            return await client.get_filter_status()
    except Exception as e:
        logger.error(f"Error getting filter status: {str(e)}")
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