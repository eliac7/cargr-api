from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CarSummary(BaseModel):
    """Car model with data available on search results page."""
    car_id: str
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    year: Optional[int] = None
    km: Optional[float] = None
    fueltype: Optional[str] = None
    transmission: Optional[str] = None
    location: Optional[str] = None
    thumbnail: Optional[str] = None
    is_dealer: bool = False

    class Config:
        from_attributes = True


class Car(BaseModel):
    car_id: str
    title: Optional[str] = None
    price: Optional[float] = None
    
    # Categorization
    make: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    
    # Specs
    release_date: Optional[str] = None
    engine: Optional[int] = None
    km: Optional[float] = None
    bhp: Optional[int] = None
    color: Optional[str] = None
    fueltype: Optional[str] = None
    transmission: Optional[str] = None
    doors: Optional[int] = None
    seats: Optional[int] = None
    
    # Regulatory & Costs
    euro_class: Optional[str] = None  # e.g., Euro 5
    road_tax: Optional[int] = None    # e.g., 110
    kteo_expiry: Optional[str] = None # MOT expiry
    
    # Location
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[int] = None
    
    # Seller & Meta
    is_dealer: bool = False
    seller_name: Optional[str] = None
    description: Optional[str] = None
    views: Optional[int] = None
    modified_at: Optional[str] = None
    
    images: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list) # e.g., ['ABS', 'A/C']
    
    url: str
    scraped_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        from_attributes = True