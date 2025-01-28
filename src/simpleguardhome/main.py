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

# Initialize FastAPI app
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

# Request/Response Models
class DomainRequest(BaseModel):
    name: str

class ErrorResponse(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get(
    "/control/filtering/check_host",
    response_model=DomainCheckResult,
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request", "model": ErrorResponse},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def check_domain(name: str) -> Dict:
    """Check if a domain is blocked by AdGuard Home using AdGuard spec."""
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain name is required"
        )
    
    logger.info(f"Checking domain: {name}")
    try:
        async with adguard.AdGuardClient() as client:
            result = await client.check_domain(name)
            logger.info(f"Domain check result: {result}")
            return result
    except Exception as e:
        logger.error(f"Error checking domain {name}: {str(e)}")
        raise

@app.post(
    "/control/filtering/whitelist/add",
    response_model=Dict,
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request", "model": ErrorResponse},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def add_to_whitelist(request: DomainRequest) -> Dict:
    """Add a domain to the allowed list using AdGuard spec."""
    if not request.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain name is required"
        )
    
    logger.info(f"Adding domain to whitelist: {request.name}")
    try:
        async with adguard.AdGuardClient() as client:
            success = await client.add_allowed_domain(request.name)
            if success:
                return {"message": f"Successfully whitelisted {request.name}"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to whitelist domain"
                )
    except Exception as e:
        logger.error(f"Error whitelisting domain {request.name}: {str(e)}")
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
    """Get the current filtering status using AdGuard spec."""
    try:
        async with adguard.AdGuardClient() as client:
            return await client.get_filter_status()
    except Exception as e:
        logger.error(f"Error getting filter status: {str(e)}")
        raise

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