from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import httpx
import logging
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdGuardError(Exception):
    """Base exception for AdGuard Home API errors."""
    pass

class AdGuardConnectionError(AdGuardError):
    """Raised when connection to AdGuard Home fails."""
    pass

class AdGuardAPIError(AdGuardError):
    """Raised when AdGuard Home API returns an error."""
    pass

# Response models matching AdGuard Home API spec
class Filter(BaseModel):
    """Filter subscription info according to AdGuard spec."""
    enabled: bool
    id: int = Field(..., description="Filter ID", example=1234)
    name: str = Field(..., example="AdGuard Simplified Domain Names filter")
    rules_count: int = Field(..., description="Number of rules in filter", example=5912)
    url: str = Field(..., example="https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt")
    last_updated: Optional[str] = Field(None, example="2018-10-30T12:18:57+03:00")

class FilterStatus(BaseModel):
    """Filtering settings according to AdGuard spec."""
    enabled: bool = Field(..., description="Whether filtering is enabled")
    interval: Optional[int] = Field(None, description="Update interval in hours")
    filters: List[Filter] = Field(default_factory=list)
    whitelist_filters: List[Filter] = Field(default_factory=list)
    user_rules: List[str] = Field(default_factory=list)

class DnsAnswer(BaseModel):
    """DNS answer section according to AdGuard spec."""
    ttl: int = Field(..., description="Time to live")
    type: str = Field(..., description="Record type", example="A")
    value: str = Field(..., description="Record value", example="217.69.139.201")

class DomainCheckResult(BaseModel):
    """Response model for check_host endpoint according to AdGuard spec."""
    reason: str = Field(
        ...,
        description="Request filtering status",
        enum=[
            "NotFilteredNotFound",
            "NotFilteredWhiteList",
            "NotFilteredError",
            "FilteredBlackList",
            "FilteredSafeBrowsing",
            "FilteredParental",
            "FilteredInvalid",
            "FilteredSafeSearch",
            "FilteredBlockedService",
            "Rewrite",
            "RewriteEtcHosts",
            "RewriteRule"
        ]
    )
    filter_id: Optional[int] = Field(None, description="ID of the filter list containing the rule")
    rule: Optional[str] = Field(None, description="Applied filtering rule")
    service_name: Optional[str] = Field(None, description="Blocked service name if applicable")
    cname: Optional[str] = Field(None, description="CNAME value if rewritten")
    ip_addrs: Optional[List[str]] = Field(None, description="IP addresses if rewritten")

class AdGuardClient:
    """Client for interacting with AdGuard Home API according to OpenAPI spec."""
    
    def __init__(self):
        """Initialize the AdGuard Home API client."""
        self.base_url = f"{settings.adguard_base_url}/control"
        self.client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self._session_cookie = None
        self._auth = None
        if settings.ADGUARD_USERNAME and settings.ADGUARD_PASSWORD:
            self._auth = {
                "name": settings.ADGUARD_USERNAME,
                "password": settings.ADGUARD_PASSWORD
            }
        logger.info(f"Initialized AdGuard Home client with base URL: {self.base_url}")

    async def login(self) -> bool:
        """Authenticate with AdGuard Home and get session cookie.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            AdGuardConnectionError: If connection to AdGuard Home fails
            AdGuardAPIError: If authentication fails
        """
        if not self._auth:
            logger.warning("No credentials configured, skipping authentication")
            return False

        url = f"{self.base_url}/login"
        
        try:
            logger.info("Authenticating with AdGuard Home")
            response = await self.client.post(url, json=self._auth)
            response.raise_for_status()
            
            cookies = response.cookies
            if 'agh_session' in cookies:
                self._session_cookie = cookies['agh_session']
                logger.info("Successfully authenticated with AdGuard Home")
                return True
            else:
                logger.error("No session cookie received after login")
                raise AdGuardAPIError("Authentication failed: No session cookie received")
                
        except httpx.ConnectError as e:
            logger.error(f"Connection error during login: {str(e)}")
            raise AdGuardConnectionError(f"Failed to connect to AdGuard Home: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during login: {str(e)}")
            raise AdGuardAPIError(f"Authentication failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            raise AdGuardError(f"Authentication error: {str(e)}")

    async def _ensure_authenticated(self):
        """Ensure we have a valid session cookie."""
        if not self._session_cookie:
            await self.login()
    
    async def check_domain(self, domain: str) -> DomainCheckResult:
        """Check if a domain is blocked by AdGuard Home.
        
        Args:
            domain: The domain to check
            
        Returns:
            DomainCheckResult according to AdGuard spec
            
        Raises:
            AdGuardConnectionError: If connection to AdGuard Home fails
            AdGuardAPIError: If AdGuard Home API returns an error
        """
        await self._ensure_authenticated()
        url = f"{self.base_url}/filtering/check_host"
        params = {"name": domain}
        headers = {}
        
        if self._session_cookie:
            headers['Cookie'] = f'agh_session={self._session_cookie}'
        
        try:
            logger.info(f"Checking domain: {domain}")
            response = await self.client.get(url, params=params, headers=headers)
            
            if response.status_code == 401:
                logger.info("Session expired, attempting reauth")
                await self.login()
                if self._session_cookie:
                    headers['Cookie'] = f'agh_session={self._session_cookie}'
                response = await self.client.get(url, params=params, headers=headers)
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Domain check result for {domain}: {result}")
            return DomainCheckResult(**result)
            
        except httpx.ConnectError as e:
            logger.error(f"Connection error while checking domain {domain}: {str(e)}")
            raise AdGuardConnectionError(f"Failed to connect to AdGuard Home: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while checking domain {domain}: {str(e)}")
            raise AdGuardAPIError(f"AdGuard Home API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while checking domain {domain}: {str(e)}")
            raise AdGuardError(f"Unexpected error: {str(e)}")
    
    async def get_filter_status(self) -> FilterStatus:
        """Get the current filtering status.
        
        Returns:
            FilterStatus according to AdGuard spec
            
        Raises:
            AdGuardConnectionError: If connection to AdGuard Home fails
            AdGuardAPIError: If AdGuard Home API returns an error
        """
        await self._ensure_authenticated()
        url = f"{self.base_url}/filtering/status"
        headers = {}
        
        if self._session_cookie:
            headers['Cookie'] = f'agh_session={self._session_cookie}'
        
        try:
            logger.info("Getting filter status")
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 401:
                logger.info("Session expired, attempting reauth")
                await self.login()
                if self._session_cookie:
                    headers['Cookie'] = f'agh_session={self._session_cookie}'
                response = await self.client.get(url, headers=headers)
            
            response.raise_for_status()
            result = response.json()
            logger.info("Successfully retrieved filter status")
            return FilterStatus(**result)
            
        except httpx.ConnectError as e:
            logger.error(f"Connection error while getting filter status: {str(e)}")
            raise AdGuardConnectionError(f"Failed to connect to AdGuard Home: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting filter status: {str(e)}")
            raise AdGuardAPIError(f"AdGuard Home API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while getting filter status: {str(e)}")
            raise AdGuardError(f"Unexpected error: {str(e)}")
    
    async def add_allowed_domain(self, domain: str) -> bool:
        """Add a domain to the allowed list according to AdGuard spec.
        
        Args:
            domain: The domain to allow
            
        Returns:
            bool: True if successful
            
        Raises:
            AdGuardConnectionError: If connection to AdGuard Home fails
            AdGuardAPIError: If AdGuard Home API returns an error
        """
        await self._ensure_authenticated()
        url = f"{self.base_url}/filtering/whitelist/add"
        data = {"name": domain}
        headers = {}
        
        if self._session_cookie:
            headers['Cookie'] = f'agh_session={self._session_cookie}'
        
        try:
            logger.info(f"Adding domain to whitelist: {domain}")
            response = await self.client.post(url, json=data, headers=headers)
            
            if response.status_code == 401:
                logger.info("Session expired, attempting reauth")
                await self.login()
                if self._session_cookie:
                    headers['Cookie'] = f'agh_session={self._session_cookie}'
                response = await self.client.post(url, json=data, headers=headers)
            
            response.raise_for_status()
            logger.info(f"Successfully added {domain} to whitelist")
            return True
            
        except httpx.ConnectError as e:
            logger.error(f"Connection error while whitelisting domain {domain}: {str(e)}")
            raise AdGuardConnectionError(f"Failed to connect to AdGuard Home: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while whitelisting domain {domain}: {str(e)}")
            raise AdGuardAPIError(f"AdGuard Home API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while whitelisting domain {domain}: {str(e)}")
            raise AdGuardError(f"Unexpected error: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("Closed AdGuard Home client")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()