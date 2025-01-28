from typing import Dict, List, Optional
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

class AdGuardClient:
    """Client for interacting with AdGuard Home API."""
    
    def __init__(self):
        """Initialize the AdGuard Home API client."""
        self.base_url = settings.adguard_base_url
        self.client = httpx.AsyncClient(timeout=10.0)  # 10 second timeout
        self._auth = None
        if settings.ADGUARD_USERNAME and settings.ADGUARD_PASSWORD:
            self._auth = (settings.ADGUARD_USERNAME, settings.ADGUARD_PASSWORD)
        logger.info(f"Initialized AdGuard Home client with base URL: {self.base_url}")
    
    async def check_domain(self, domain: str) -> Dict:
        """Check if a domain is blocked by AdGuard Home.
        
        Args:
            domain: The domain to check
            
        Returns:
            Dict containing the filtering status
            
        Raises:
            AdGuardConnectionError: If connection to AdGuard Home fails
            AdGuardAPIError: If AdGuard Home API returns an error
        """
        url = f"{self.base_url}/filtering/check_host"
        params = {"name": domain}
        
        try:
            logger.info(f"Checking domain: {domain}")
            response = await self.client.get(url, params=params, auth=self._auth)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Domain check result for {domain}: {result}")
            return result
            
        except httpx.ConnectError as e:
            logger.error(f"Connection error while checking domain {domain}: {str(e)}")
            raise AdGuardConnectionError(f"Failed to connect to AdGuard Home: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while checking domain {domain}: {str(e)}")
            raise AdGuardAPIError(f"AdGuard Home API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while checking domain {domain}: {str(e)}")
            raise AdGuardError(f"Unexpected error: {str(e)}")
    
    async def get_filter_status(self) -> Dict:
        """Get the current filtering status.
        
        Returns:
            Dict containing the filtering status
            
        Raises:
            AdGuardConnectionError: If connection to AdGuard Home fails
            AdGuardAPIError: If AdGuard Home API returns an error
        """
        url = f"{self.base_url}/filtering/status"
        
        try:
            logger.info("Getting filter status")
            response = await self.client.get(url, auth=self._auth)
            response.raise_for_status()
            result = response.json()
            logger.info("Successfully retrieved filter status")
            return result
            
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
        """Add a domain to the allowed list.
        
        Args:
            domain: The domain to allow
            
        Returns:
            bool: True if successful
            
        Raises:
            AdGuardConnectionError: If connection to AdGuard Home fails
            AdGuardAPIError: If AdGuard Home API returns an error
        """
        url = f"{self.base_url}/filtering/whitelist/add"
        data = {"name": domain}
        
        try:
            logger.info(f"Adding domain to whitelist: {domain}")
            response = await self.client.post(url, json=data, auth=self._auth)
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