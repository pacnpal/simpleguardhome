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
    AdGuardValidationError,
    FilterStatus,
    FilterCheckHostResponse,
    SetRulesRequest
)
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize API with proper OpenAPI info
app = FastAPI(
    title="SimpleGuardHome",
    description="AdGuard Home REST API interface",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
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

# Setup templates and static directories
templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# Mount static files from package directory
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent)), name="static")

# Mount favicon.ico at root
app.mount("/favicon.ico", StaticFiles(directory=str(Path(__file__).parent), files={"favicon.ico": "favicon.ico"}), name="favicon")

# Response models matching AdGuard spec
class ErrorResponse(BaseModel):
    """Error response model according to AdGuard spec."""
    message: str = Field(..., description="The error message")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get(
    "/control/filtering/check_host",
    response_model=FilterCheckHostResponse,
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request", "model": ErrorResponse},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def check_domain(name: str) -> FilterCheckHostResponse:
    """Check if a domain is blocked by AdGuard Home according to spec."""
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
    except AdGuardValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error checking domain {name}: {str(e)}")
        raise

@app.post(
    "/control/filtering/set_rules",
    response_model=Dict,
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request", "model": ErrorResponse},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def add_to_whitelist(request: SetRulesRequest) -> Dict:
    """Add rules using set_rules endpoint according to AdGuard spec."""
    if not request.rules:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rules are required"
        )
    
    # Extract domain from whitelist rule
    rule = request.rules[0]
    if not rule.startswith("@@||") or not rule.endswith("^"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid whitelist rule format"
        )
    
    domain = rule[4:-1]  # Remove @@|| prefix and ^ suffix
    logger.info(f"Adding domain to whitelist: {domain}")
    
    try:
        async with adguard.AdGuardClient() as client:
            success = await client.add_allowed_domain(domain)
            if success:
                return {"message": f"Domain {domain} added to whitelist"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add domain to whitelist"
                )
    except AdGuardValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding domain to whitelist: {str(e)}")
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
    """Get filtering status according to AdGuard spec."""
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
    elif isinstance(exc, AdGuardValidationError):
        status_code = status.HTTP_400_BAD_REQUEST
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