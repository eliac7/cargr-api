import logging
from threading import RLock
from typing import Any, Callable, Dict, Optional

from cachetools import TTLCache

from config import CACHE_SETTINGS

logger = logging.getLogger(__name__)

_FILTER_CACHE_KEY = "filters"


class FilterCacheService:
    def __init__(
        self,
        fetcher: Callable[[], Dict[str, Any]],
        ttl: int = CACHE_SETTINGS['filter_ttl'],
        maxsize: int = CACHE_SETTINGS['filter_maxsize'],
    ):
        self._fetcher = fetcher
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = RLock()
        self._stale_data: Optional[Dict[str, Any]] = None
    
    def get(self, force_refresh: bool = False) -> Dict[str, Any]:
        with self._lock:
            if not force_refresh and _FILTER_CACHE_KEY in self._cache:
                logger.debug("Cache hit for filters")
                return self._cache[_FILTER_CACHE_KEY]
            
            logger.info("Cache miss for filters, fetching fresh data...")
            return self._fetch_and_cache()
    
    def _fetch_and_cache(self) -> Dict[str, Any]:
        try:
            fresh_data = self._fetcher()
            
            self._cache[_FILTER_CACHE_KEY] = fresh_data
            self._stale_data = fresh_data
            
            logger.info("Successfully cached fresh filter data")
            return fresh_data
            
        except Exception as e:
            logger.error(f"Failed to fetch filter data: {e}")
            
            if self._stale_data is not None:
                logger.warning("Returning stale filter data due to fetch failure")
                return self._stale_data
            
            raise
    
    def warm(self) -> bool:
        try:
            self.get(force_refresh=True)
            logger.info("Cache warmed successfully on startup")
            return True
        except Exception as e:
            logger.error(f"Failed to warm cache on startup: {e}")
            return False
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    @property
    def is_cached(self) -> bool:
        with self._lock:
            return _FILTER_CACHE_KEY in self._cache
    
    @property
    def has_stale_fallback(self) -> bool:
        return self._stale_data is not None


_filter_cache_instance: Optional[FilterCacheService] = None


def init_filter_cache(fetcher: Callable[[], Dict[str, Any]]) -> FilterCacheService:
    global _filter_cache_instance
    _filter_cache_instance = FilterCacheService(fetcher=fetcher)
    return _filter_cache_instance


def get_filter_cache() -> FilterCacheService:
    if _filter_cache_instance is None:
        raise RuntimeError(
            "Filter cache not initialized. Call init_filter_cache() first."
        )
    return _filter_cache_instance

