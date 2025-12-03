import time
import random
import logging
from typing import Any

from stealth_requests import StealthSession

from config import BASE_URL, TIMING, REQUEST_SETTINGS

logger = logging.getLogger(__name__)


def create_session() -> StealthSession:
    """Create a new stealth session with initial warmup request."""
    session = StealthSession()
    try:
        session.get(BASE_URL, timeout=REQUEST_SETTINGS['session_timeout'])
        time.sleep(random.uniform(*TIMING['session_init_delay']))
    except Exception:
        pass
    return session


def fetch_with_retry(session: StealthSession, url: str) -> Any:
    """Fetch URL with automatic retry and rate limit handling."""
    for attempt in range(REQUEST_SETTINGS['max_retries']):
        try:
            if attempt > 0:
                delay = TIMING['retry_base_delay'] * (2 ** (attempt - 1))
                time.sleep(delay)
            
            response = session.get(
                url, 
                timeout=REQUEST_SETTINGS['timeout'], 
                allow_redirects=True
            )
            
            if response.status_code == 429:
                time.sleep(random.uniform(*TIMING['rate_limit_delay_range']))
                continue
                
            response.raise_for_status()
            return response
            
        except Exception as e:
            if attempt == REQUEST_SETTINGS['max_retries'] - 1:
                raise
            time.sleep(1)
    
    raise Exception(f"Failed to fetch {url} after {REQUEST_SETTINGS['max_retries']} attempts")

