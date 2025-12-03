from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CarSummary(BaseModel):
    """Car model with data available on search results page."""
    car_id: str = Field(..., description="Unique identifier for the car listing")
    url: str = Field(..., description="URL to the car listing on car.gr")
    title: Optional[str] = Field(None, description="Listing title")
    price: Optional[float] = Field(None, description="Price in Euros")
    year: Optional[int] = Field(None, description="Registration year")
    km: Optional[float] = Field(None, description="Odometer reading in kilometers")
    fueltype: Optional[str] = Field(None, description="Fuel type (e.g., 'Petrol', 'Diesel')")
    transmission: Optional[str] = Field(None, description="Transmission type (e.g., 'Manual', 'Automatic')")
    location: Optional[str] = Field(None, description="Location of the car")
    thumbnail: Optional[str] = Field(None, description="URL to the thumbnail image")
    is_dealer: bool = Field(False, description="Whether the seller is a dealer")

    class Config:
        from_attributes = True


class Car(BaseModel):
    car_id: str = Field(..., description="Unique identifier for the car listing")
    title: Optional[str] = Field(None, description="Listing title")
    price: Optional[float] = Field(None, description="Price in Euros")
    
    # Categorization
    make: Optional[str] = Field(None, description="Car manufacturer")
    model: Optional[str] = Field(None, description="Car model")
    category: Optional[str] = Field(None, description="Car category (e.g., 'Sedan', 'SUV')")
    
    # Specs
    release_date: Optional[str] = Field(None, description="Registration date (MM/YYYY)")
    engine: Optional[int] = Field(None, description="Engine displacement in cc")
    km: Optional[float] = Field(None, description="Odometer reading in kilometers")
    bhp: Optional[int] = Field(None, description="Engine power in BHP")
    color: Optional[str] = Field(None, description="Exterior color")
    fueltype: Optional[str] = Field(None, description="Fuel type")
    transmission: Optional[str] = Field(None, description="Transmission type")
    doors: Optional[int] = Field(None, description="Number of doors")
    seats: Optional[int] = Field(None, description="Number of seats")
    
    # Regulatory & Costs
    euro_class: Optional[str] = Field(None, description="Euro emissions standard (e.g., 'Euro 6')")
    road_tax: Optional[int] = Field(None, description="Annual road tax in Euros")
    kteo_expiry: Optional[str] = Field(None, description="MOT/KTEO expiry date")
    
    # Location
    city: Optional[str] = Field(None, description="City where the car is located")
    region: Optional[str] = Field(None, description="Region where the car is located")
    postal_code: Optional[int] = Field(None, description="Postal code")
    
    # Seller & Meta
    is_dealer: bool = Field(False, description="Whether the seller is a dealer")
    seller_name: Optional[str] = Field(None, description="Name of the seller")
    description: Optional[str] = Field(None, description="Full description text of the listing")
    views: Optional[int] = Field(None, description="Number of views the listing has received")
    modified_at: Optional[str] = Field(None, description="Last modification timestamp")
    
    images: List[str] = Field(default_factory=list, description="List of image URLs")
    features: List[str] = Field(default_factory=list, description="List of features (e.g., 'ABS', 'Navigation')")
    
    url: str = Field(..., description="URL to the car listing")
    scraped_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Timestamp when the data was scraped")

    class Config:
        from_attributes = True


class CarSearchFilters(BaseModel):
    """
    Filter parameters for searching cars.
    Note: Use /api/filters to get valid values for ID-based fields like 'make', 'model', etc.
    """
    make: Optional[str] = Field(None, description="Car manufacturer ID (e.g., '18' for BMW)")
    model: Optional[str] = Field(None, description="Car model ID")
    
    price_from: Optional[int] = Field(None, description="Minimum price in Euros")
    price_to: Optional[int] = Field(None, description="Maximum price in Euros")
    
    registration_from: Optional[int] = Field(None, description="Minimum registration year (e.g. 2018)")
    registration_to: Optional[int] = Field(None, description="Maximum registration year")
    
    mileage_from: Optional[int] = Field(None, description="Minimum kilometers")
    mileage_to: Optional[int] = Field(None, description="Maximum kilometers")
    
    engine_size_from: Optional[int] = Field(None, description="Minimum engine size (cc)")
    engine_size_to: Optional[int] = Field(None, description="Maximum engine size (cc)")
    
    fuel_type: Optional[str] = Field(None, description="Fuel type ID")
    gearbox_type: Optional[str] = Field(None, description="Transmission type ID")
    drive_type: Optional[str] = Field(None, description="Drive type ID (e.g. '4x4')")
    
    exterior_color: Optional[str] = Field(None, description="Exterior color ID")
    seats: Optional[str] = Field(None, description="Number of seats")
    doors: Optional[str] = Field(None, description="Number of doors")
    
    sort: Optional[str] = Field("price", description="Sort order (e.g., 'price', 'cr', 'date')")