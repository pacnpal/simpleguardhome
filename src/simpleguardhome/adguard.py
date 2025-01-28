from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field
import httpx
import logging
import re
import json
from pathlib import Path
from datetime import datetime
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for rule validation and backup
DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
RULES_BACKUP_DIR = Path("rules_backup")
RULES_BACKUP_DIR.mkdir(exist_ok=True)

class AdGuardError(Exception):
    """Base exception for AdGuard Home API errors."""
    pass

class AdGuardConnectionError(AdGuardError):
    """Raised when connection to AdGuard Home fails."""
    pass

class AdGuardAPIError(AdGuardError):
    """Raised when AdGuard Home API returns an error."""
    pass

class AdGuardValidationError(AdGuardError):
    """Raised when input validation fails."""
    pass

class ResultRule(BaseModel):
    """Rule detail according to AdGuard spec."""
    filter_list_id: Optional[int] = Field(None, description="Filter list ID")
    text: Optional[str] = Field(None, description="Rule text")

class FilterCheckHostResponse(BaseModel):
    """Response model for check_host endpoint according to AdGuard spec."""
    reason: str = Field(..., description="Request filtering status")
    filter_id: Optional[int] = Field(None, deprecated=True)
    rule: Optional[str] = Field(None, deprecated=True)
    rules: Optional[List[ResultRule]] = Field(None, description="Applied rules")
    service_name: Optional[str] = Field(None, description="Blocked service name")
    cname: Optional[str] = Field(None, description="CNAME value if rewritten")
    ip_addrs: Optional[List[str]] = Field(None, description="IP addresses if rewritten")

class Filter(BaseModel):
    """Filter subscription info according to AdGuard spec."""
    enabled: bool
    id: int = Field(..., description="Filter ID")
    name: str = Field(..., description="Filter name")
    rules_count: int = Field(..., description="Number of rules")
    url: str = Field(..., description="Filter URL")
    last_updated: Optional[str] = None

class FilterStatus(BaseModel):
    """Filtering settings according to AdGuard spec."""
    enabled: bool
    interval: Optional[int] = None
    filters: List[Filter] = Field(default_factory=list)
    whitelist_filters: List[Filter] = Field(default_factory=list)
    user_rules: List[str] = Field(default_factory=list)

class SetRulesRequest(BaseModel):
    """Request model for set_rules endpoint according to AdGuard spec."""
    rules: List[str] = Field(..., description="List of filtering rules")

def validate_domain(domain: str) -> bool:
    """Validate domain name format."""
    if not domain or len(domain) > 255:
        return False
    return bool(DOMAIN_PATTERN.match(domain))

def sanitize_rule(rule: str) -> str:
    """Sanitize and validate rule format."""
    # Remove any whitespace and normalize
    rule = rule.strip()
    # Basic XSS/injection prevention
    rule = rule.replace('<', '').replace('>', '').replace('"', '').replace("'", '')
    return rule

def save_rules_backup(rules: List[str], action: str = "update") -> Path:
    """Save rules to backup file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = RULES_BACKUP_DIR / f"rules_{action}_{timestamp}.json"
    with open(backup_file, 'w') as f:
        json.dump({"rules": rules, "timestamp": timestamp}, f, indent=2)
    logger.info(f"Saved rules backup to {backup_file}")
    return backup_file

def load_rules_backup(backup_file: Path) -> List[str]:
    """Load rules from backup file."""
    try:
        with open(backup_file) as f:
            data = json.load(f)
            return data.get("rules", [])
    except Exception as e:
        logger.error(f"Error loading rules backup: {str(e)}")
        return []

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
        """Authenticate with AdGuard Home and get session cookie."""
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
    
    async def check_domain(self, domain: str) -> FilterCheckHostResponse:
        """Check if a domain is blocked by AdGuard Home according to spec."""
        # Validate domain format
        if not validate_domain(domain):
            raise AdGuardValidationError(f"Invalid domain format: {domain}")

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
            return FilterCheckHostResponse(**result)
            
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
        """Get the current filtering status according to spec."""
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
        """Add a domain to the allowed list using AdGuard filtering API."""
        # Validate domain format
        if not validate_domain(domain):
            raise AdGuardValidationError(f"Invalid domain format: {domain}")

        await self._ensure_authenticated()
        
        try:
            # First get current user rules
            status = await self.get_filter_status()
            current_rules = status.user_rules if status else []
            
            # Create sanitized whitelist rule
            new_rule = sanitize_rule(f"@@||{domain}^")
            
            # Save backup of current rules
            old_backup = save_rules_backup(current_rules, "before")
            
            # Add rule if not already present
            if new_rule not in current_rules:
                current_rules.append(new_rule)
                
            # Save backup of new rules before updating
            new_backup = save_rules_backup(current_rules, "after")
            
            # Update rules
            url = f"{self.base_url}/filtering/set_rules"
            data = {"rules": current_rules}
            headers = {}
            
            if self._session_cookie:
                headers['Cookie'] = f'agh_session={self._session_cookie}'
            
            logger.info(f"Updating rules list with whitelisted domain: {domain}")
            response = await self.client.post(url, json=data, headers=headers)
            
            if response.status_code == 401:
                logger.info("Session expired, attempting reauth")
                await self.login()
                if self._session_cookie:
                    headers['Cookie'] = f'agh_session={self._session_cookie}'
                response = await self.client.post(url, json=data, headers=headers)
            
            response.raise_for_status()
            logger.info(f"Successfully updated rules list with whitelisted domain: {domain}")
            return True
            
        except (httpx.ConnectError, httpx.HTTPError) as e:
            # On error, try to restore from backup
            logger.error(f"Error updating rules, attempting to restore from backup: {str(e)}")
            if old_backup.exists():
                try:
                    old_rules = load_rules_backup(old_backup)
                    if old_rules:
                        await self.client.post(url, json={"rules": old_rules}, headers=headers)
                        logger.info("Successfully restored rules from backup")
                except Exception as restore_error:
                    logger.error(f"Failed to restore from backup: {str(restore_error)}")
            raise
            
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