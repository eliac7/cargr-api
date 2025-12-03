import logging
from contextlib import asynccontextmanager
from typing import List
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request

from cache import get_filter_cache, init_filter_cache
from config import CACHE_SETTINGS
from filter_parser import get_available_filters
from models import Car, CarSummary
from parser import parse_car_page, parse_search_results

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

SEARCH_BASE_URL = 'https://www.car.gr/classifieds/cars/'


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Car.gr API...")
    
    cache = init_filter_cache(fetcher=get_available_filters)
    
    # Warm cache on startup
    if CACHE_SETTINGS.get('warm_on_startup', True):
        logger.info("Warming filter cache on startup...")
        if cache.warm():
            logger.info("Filter cache warmed successfully")
        else:
            logger.warning("Failed to warm cache - first request will be slower")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Car.gr API...")


app = FastAPI(
    title="Car.gr API",
    description="Unofficial API for car.gr",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/car/{car_id}", response_model=Car)
def get_car(car_id: str):
    """Get full details for a specific car listing."""
    try:
        car = parse_car_page(car_id)
        return car
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Car not found or parsing error: {str(e)}"
        )


@app.get("/api/search", response_model=List[CarSummary])
def search(request: Request):
    """Search for cars. Returns summary data (use /api/car/{id} for full details)."""
    params = dict(request.query_params)
    search_url = f"{SEARCH_BASE_URL}?{urlencode(params)}"
    
    try:
        results = list(parse_search_results(search_url))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return results


@app.get("/api/filters")
def get_filters(refresh: bool = False):
    try:
        cache = get_filter_cache()
        return cache.get(force_refresh=refresh)
    except RuntimeError:
        logger.error("Filter cache not initialized")
        raise HTTPException(
            status_code=503,
            detail="Service not ready - cache not initialized"
        )
    except Exception as e:
        logger.error(f"Failed to get filters: {e}")
        raise HTTPException(
            status_code=503,
            detail="Could not fetch filters from source"
        )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
