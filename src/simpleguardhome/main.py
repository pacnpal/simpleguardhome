import logging
from pathlib import Path
from typing import Dict

import httpx  # noqa: F401
from fastapi import (  # type: ignore  # noqa: F401
    FastAPI,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.templating import Jinja2Templates  # type: ignore
from pydantic import BaseModel, Field

from . import adguard
from .adguard import (
    AdGuardAPIError,
    AdGuardConnectionError,
    AdGuardError,
    AdGuardValidationError,
    FilterCheckHostResponse,
    FilterStatus,
    SetRulesRequest,
)
from .config import settings  # noqa: F401

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

# Serve favicon.ico directly
from fastapi.responses import FileResponse
favicon_path = Path(__file__).parent / "favicon.ico"

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon."""
    return FileResponse(favicon_path)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

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
        ) from e
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
        ) from e
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


@app.get(
    "/control/filtering/unblock_host",
    response_model=Dict,
    responses={
        200: {"description": "OK"},
        400: {"description": "Bad Request", "model": ErrorResponse},
        503: {"description": "AdGuard Home service unavailable", "model": ErrorResponse}
    },
    tags=["filtering"]
)
async def unblock_host(name: str) -> Dict:
    """Unblock a domain by adding it to the whitelist if it's blocked."""
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain name is required"
        )

    logger.info(f"Checking domain status: {name}")
    try:
        async with adguard.AdGuardClient() as client:
            # First check if domain is blocked
            check_result = await client.check_domain(name)
            
            # If domain isn't blocked, no need to check whitelist or do anything else
            if check_result.reason != "FilteredBlackList":
                return {"message": f"Domain {name} is not blocked (Status: {check_result.reason})"}
            
            # Domain is blocked, check if it's already in whitelist
            status_rules = await client.get_filter_status()
            whitelist_rule = f"@@||{name}^"
            if status_rules.user_rules and whitelist_rule in status_rules.user_rules:
                return {"message": f"Domain {name} is already unblocked"}
            
            # Domain is blocked and not in whitelist, proceed with unblocking
            success = await client.add_allowed_domain(name)
            if success:
                return {"message": f"Domain {name} has been unblocked"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to unblock domain"
                )
    except AdGuardValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Error unblocking domain: {str(e)}")
        raise


@app.exception_handler(AdGuardError)
async def adguard_exception_handler(_request: Request, exc: AdGuardError) -> JSONResponse:
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
    import uvicorn  # type: ignore
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Disable reload in Docker
    )


if __name__ == "__main__":
    start()
