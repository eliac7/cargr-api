import re
import logging
from typing import Generator, Optional

from bs4 import BeautifulSoup, Tag

from config import BASE_URL, REGEX_PATTERNS
from http_client import create_session, fetch_with_retry
from models import CarSummary

logger = logging.getLogger(__name__)


class SearchResultsParser:
    """Parses a car.gr search results page and extracts car summaries directly."""
    
    def __init__(self, url: str):
        self.url = url
        self.session = create_session()
        self.response = fetch_with_retry(self.session, url)
        self.soup = BeautifulSoup(self.response.text, 'html.parser')

    def _extract_car_id(self, href: str) -> Optional[str]:
        """Extract car ID from href."""
        match = re.search(r'/(?:classifieds/cars/view/|used-cars/)(\d+)', href)
        return match.group(1) if match else None

    def _extract_price(self, card: Tag) -> Optional[float]:
        """Extract price from card."""
        # Look for price pattern in text
        price_match = re.search(r'([\d.]+)\s*€', card.get_text())
        if price_match:
            try:
                return float(price_match.group(1).replace('.', '').replace(',', '.'))
            except ValueError:
                pass
        return None

    def _extract_year(self, title: str) -> Optional[int]:
        """Extract year from title."""
        match = re.search(r'\b(19|20)\d{2}\b', title)
        if match:
            try:
                return int(match.group(0))
            except ValueError:
                pass
        return None

    def _extract_km(self, card: Tag) -> Optional[float]:
        """Extract kilometers from card."""
        # Look for km pattern
        km_text = card.find(string=re.compile(r'[\d.]+\s*Km', re.IGNORECASE))
        if km_text:
            match = re.search(r'([\d.]+)\s*Km', km_text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace('.', ''))
                except ValueError:
                    pass
        return None

    def _extract_fuel_type(self, card: Tag) -> Optional[str]:
        """Extract fuel type from card."""
        fuel_types = ['Petrol', 'Diesel', 'Electric', 'Hybrid', 'LPG', 'CNG', 
                      'Βενζίνη', 'Πετρέλαιο', 'Ηλεκτρικό', 'Υβριδικό']
        text = card.get_text()
        for fuel in fuel_types:
            if fuel.lower() in text.lower():
                return fuel
        return None

    def _extract_transmission(self, card: Tag) -> Optional[str]:
        """Extract transmission from card."""
        text = card.get_text().lower()
        if 'automatic' in text or 'αυτόματο' in text:
            return 'Automatic'
        elif 'manual' in text or 'χειροκίνητο' in text:
            return 'Manual'
        return None

    def _extract_location(self, card: Tag) -> Optional[str]:
        """Extract location from card."""
        # Location usually appears as uppercase city name followed by postal code
        text = card.get_text()
        match = re.search(r'([A-Z]{3,}(?:\s+[A-Z]+)*)\s+\d{5}', text)
        if match:
            return match.group(1).title()
        return None

    def _extract_thumbnail(self, card: Tag) -> Optional[str]:
        """Extract thumbnail URL from card."""
        img = card.find('img')
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src and not src.startswith('data:'):
                if src.startswith('//'):
                    return f'https:{src}'
                elif src.startswith('/'):
                    return f'{BASE_URL}{src}'
                return src
        return None

    def _extract_title(self, card: Tag) -> Optional[str]:
        """Extract car title from card."""
        # Try to find img alt text first
        img = card.find('img')
        if img and img.get('alt'):
            return img.get('alt')
        
        # Fallback to link text
        link = card.find('a', href=True)
        if link:
            # Get text content, clean it up
            text = link.get_text(separator=' ', strip=True)
            # Remove common noise patterns
            text = re.sub(r'^\d+\s*/\s*\d+\s*', '', text)  # Remove "1 / 27" prefix
            text = re.sub(r'Promoted|In tallment|Installment', '', text, flags=re.IGNORECASE)
            # Take first meaningful part (make + model + year usually)
            parts = text.split()
            if len(parts) > 3:
                # Look for year pattern and include up to it
                for i, part in enumerate(parts):
                    if re.match(r'^(19|20)\d{2}$', part):
                        return ' '.join(parts[:i+1])
            return ' '.join(parts[:5]) if parts else None
        return None

    def _is_dealer(self, card: Tag) -> bool:
        """Check if listing is from a dealer."""
        text = card.get_text().lower()
        return 'dealer' in text or 'έμπορος' in text or 'επαγγελματίας' in text

    def parse(self) -> Generator[CarSummary, None, None]:
        """Parse search results and yield CarSummary objects."""
        
        for anchor in self.soup.find_all('a', href=True):
            href = anchor['href']
            
            car_id = self._extract_car_id(href)
            if not car_id:
                continue

            card = anchor
            for _ in range(5):
                parent = card.parent
                if parent and parent.name in ['li', 'article', 'div']:
                    if parent.find('img'):
                        card = parent
                        break
                card = parent if parent else card
            
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = f'{BASE_URL}{href}'
            else:
                url = f'{BASE_URL}/{href}'
            
            title = self._extract_title(card)
            
            try:
                yield CarSummary(
                    car_id=car_id,
                    url=url,
                    title=title,
                    price=self._extract_price(card),
                    year=self._extract_year(title) if title else None,
                    km=self._extract_km(card),
                    fueltype=self._extract_fuel_type(card),
                    transmission=self._extract_transmission(card),
                    location=self._extract_location(card),
                    thumbnail=self._extract_thumbnail(card),
                    is_dealer=self._is_dealer(card),
                )
            except Exception as e:
                logger.error(f"Error parsing car {car_id}: {e}")
                continue

    def get_car_paths(self) -> Generator[str, None, None]:
        """Yield unique car listing paths from the search results (legacy method)."""
        seen = set()
        
        for anchor in self.soup.find_all('a', href=True):
            href = anchor['href']
            match = re.search(REGEX_PATTERNS['car_path'], href)
            
            if match:
                full_path = match.group(0)
                if full_path not in seen:
                    seen.add(full_path)
                    yield full_path


def parse_search_results(url: str) -> Generator[CarSummary, None, None]:
    """Parse a search results page and yield CarSummary models for each listing.
    
    Args:
        url: Full search URL (e.g., https://www.car.gr/classifieds/cars/?...)
        
    Yields:
        CarSummary models for each successfully parsed listing
    """
    seen_ids = set()
    for car in SearchResultsParser(url).parse():
        if car.car_id not in seen_ids:
            seen_ids.add(car.car_id)
            yield car
