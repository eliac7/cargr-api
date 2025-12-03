from typing import List
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from parser import parse_car_page, parse_search_results
from models import Car, CarSummary

SEARCH_BASE_URL = 'https://www.car.gr/classifieds/cars/'


app = FastAPI(
    title="Car.gr API",
    description="Unofficial API for car.gr",
    version="1.0.0",
)

@app.get("/api/car/{car_id}", response_model=Car)
def get_car(car_id: str):
    """Get full details for a specific car listing."""
    try:
        car = parse_car_page(car_id)
        return car
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Car not found or parsing error: {str(e)}")

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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)