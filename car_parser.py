import re
import logging
from typing import Any

from bs4 import BeautifulSoup

from config import BASE_URL, CAR_VIEW_PATH, REGEX_PATTERNS
from http_client import create_session, fetch_with_retry
from utils import extract_json_ld, extract_meta_description, safe_float
from field_parsers import (
    BaseFieldParser,
    FloatParser,
    IntParser,
    TableValueParser,
    ReleaseDateParser,
    DescriptionParser,
    CarModelParser,
    CityParser,
    SellerNameParser,
)
from models import Car

logger = logging.getLogger(__name__)


class CarListingParser:
    """Parses a single car listing page and extracts all available data."""
    
    FIELD_PARSERS = {
        # Basic info
        'title': BaseFieldParser(json_ld_path='name'),
        'url': BaseFieldParser(json_ld_path='url'),
        'price': BaseFieldParser(json_ld_path='offers.priceSpecification.price'),
        'make': BaseFieldParser(json_ld_path='manufacturer'),
        'model': CarModelParser(),
        
        # Technical specs from meta/JSON-LD
        'km': FloatParser(json_ld_path='mileageFromOdometer.value', regex=REGEX_PATTERNS['km']),
        'engine': IntParser(regex=REGEX_PATTERNS['engine']),
        'bhp': IntParser(regex=REGEX_PATTERNS['bhp']),
        'fueltype': BaseFieldParser(json_ld_path='fuelType', regex=REGEX_PATTERNS['fueltype']),
        'transmission': BaseFieldParser(json_ld_path='vehicleTransmission', regex=REGEX_PATTERNS['transmission']),
        'release_date': ReleaseDateParser(json_ld_path='modelDate', regex=REGEX_PATTERNS['release_date']),
        
        # Content
        'description': DescriptionParser(json_ld_path='description'),
        'images': BaseFieldParser(json_ld_path='image'),
        'is_dealer': BaseFieldParser(json_ld_path='offers.seller.@type'),
        
        # Table specifications
        'color': TableValueParser(r'^\s*Χρώμα\s*$'),
        'category': TableValueParser(r'^\s*Κατηγορία\s*$'),
        'euro_class': TableValueParser(r'^\s*Κλάση ρύπων\s*$'),
        'kteo_expiry': TableValueParser(r'^\s*ΚΤΕΟ μέχρι\s*$'),
        'views': TableValueParser(r'^\s*Εμφανίσεις αγγελίας\s*$', output_type='int'),
        'modified_at': TableValueParser(r'^\s*Τελευταία αλλαγή\s*$'),
        'road_tax': TableValueParser(r'^\s*Τέλη κυκλοφορίας\s*$', output_type='int'),
        'seats': TableValueParser(r'^\s*Θέσεις επιβατών\s*$', output_type='int'),
        'doors': TableValueParser(r'^\s*Πόρτες\s*$', output_type='int'),
        
        # Seller info
        'seller_name': SellerNameParser(),
        'city': CityParser(),
    }

    def __init__(self, car_path: str):
        self.car_path = str(car_path)
        self.car_id = self._extract_car_id()
        self.url = self._build_url()
        
        # Fetch and parse the page
        session = create_session()
        response = fetch_with_retry(session, self.url)
        response.encoding = 'utf-8'
        
        self.soup = BeautifulSoup(response.text, 'html.parser')
        self.json_data = extract_json_ld(self.soup)
        self.meta = extract_meta_description(self.soup)

    def _extract_car_id(self) -> str:
        """Extract numeric car ID from path."""
        match = re.search(r'(\d+)', self.car_path)
        return match.group(1) if match else self.car_path

    def _build_url(self) -> str:
        """Build full URL from car path."""
        if self.car_path.startswith('http'):
            return self.car_path
        
        if self.car_path.startswith('/'):
            return f'{BASE_URL}{self.car_path}'
        
        return f'{BASE_URL}{CAR_VIEW_PATH}{self.car_path}'

    def _get_field(self, field: str) -> Any:
        """Get a field value using the appropriate parser."""
        parser = self.FIELD_PARSERS.get(field)
        if parser:
            return parser.parse(self.json_data, self.meta, self.soup)
        return None

    def _is_dealer(self) -> bool:
        """Determine if seller is a dealer."""
        seller_type = self.json_data.get('offers', {}).get('seller', {}).get('@type')
        
        if seller_type in ['AutoDealer', 'Organization']:
            return True
        
        # Check for dealer indicator in HTML
        if self.soup.find(string=re.compile(r'Έμπορος')):
            return True
        
        return False

    def parse(self) -> Car:
        """Parse the page and return a Car model."""
        images = self._get_field('images') or []
        if not isinstance(images, list):
            images = [images]

        return Car(
            car_id=self.car_id,
            url=self._get_field('url') or self.url,
            title=self._get_field('title'),
            price=safe_float(self._get_field('price')),
            make=self._get_field('make'),
            model=self._get_field('model'),
            category=self._get_field('category'),
            km=self._get_field('km'),
            bhp=self._get_field('bhp'),
            engine=self._get_field('engine'),
            fueltype=self._get_field('fueltype'),
            transmission=self._get_field('transmission'),
            color=self._get_field('color'),
            release_date=self._get_field('release_date'),
            euro_class=self._get_field('euro_class'),
            road_tax=self._get_field('road_tax'),
            kteo_expiry=self._get_field('kteo_expiry'),
            views=self._get_field('views'),
            modified_at=self._get_field('modified_at'),
            city=self._get_field('city'),
            seller_name=self._get_field('seller_name'),
            is_dealer=self._is_dealer(),
            images=images,
            description=self._get_field('description'),
            seats=self._get_field('seats'),
            doors=self._get_field('doors'),
        )


def parse_car_page(path_or_id: str) -> Car:
    """Parse a car listing page and return a Car model.
    
    Args:
        path_or_id: Car ID, path, or full URL
        
    Returns:
        Car model with all parsed data
    """
    return CarListingParser(path_or_id).parse()

