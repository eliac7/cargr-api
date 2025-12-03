import re
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from utils import safe_int, safe_float


class BaseFieldParser:
    """Base parser that extracts values from JSON-LD or meta description via regex."""
    
    def __init__(self, json_ld_path: str = None, regex: str = None):
        self.json_path = json_ld_path
        self.regex = regex

    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Any:
        # Try JSON-LD path first
        if self.json_path:
            val = json_data
            for key in self.json_path.split('.'):
                if isinstance(val, dict):
                    val = val.get(key)
                else:
                    val = None
                    break
            if val is not None:
                return val
        
        # Fall back to regex on meta description
        if self.regex:
            match = re.search(self.regex, meta)
            if match:
                return match.group(1)
            
        return None


class FloatParser(BaseFieldParser):
    """Parser that returns a float value."""
    
    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Optional[float]:
        val = super().parse(json_data, meta, soup)
        return safe_float(val)


class IntParser(BaseFieldParser):
    """Parser that returns an integer value."""
    
    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Optional[int]:
        val = super().parse(json_data, meta, soup)
        return safe_int(val)


class TableValueParser(BaseFieldParser):
    """Parses values from the Tailwind CSS Grid specification table."""
    
    def __init__(self, label_pattern: str, output_type: str = 'str'):
        super().__init__()
        self.label_pattern = label_pattern
        self.output_type = output_type

    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Any:
        try:
            # Find the label element (e.g., "Χρώμα")
            label_el = soup.find(string=re.compile(self.label_pattern))
            if not label_el:
                return None
                
            # Find the parent grid row
            row = label_el.find_parent(class_='tw-grid')
            if not row:
                return None
                
            children = row.find_all(recursive=False)
            if len(children) < 2:
                return None
                
            val_div = children[-1]
            text = val_div.get_text(separator=' ', strip=True)
            
            # Remove the label if accidentally included
            clean_label = self.label_pattern.replace('^', '').replace('$', '').replace('\\s*', '')
            text = re.sub(f'^{clean_label}', '', text, flags=re.IGNORECASE).strip()

            if self.output_type == 'int':
                match = re.search(r'(\d+)', text)
                return safe_int(match.group(1)) if match else None
            
            return text
            
        except Exception:
            return None


class ReleaseDateParser(BaseFieldParser):
    """Parses release date from MM/YYYY format."""
    
    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Optional[str]:
        # Try regex first (captures month and year separately)
        if self.regex:
            match = re.search(self.regex, meta)
            if match:
                return f"{match.group(1)}/{match.group(2)}"
        
        # Fall back to JSON-LD
        return super().parse(json_data, meta, soup)


class DescriptionParser(BaseFieldParser):
    """Extracts description from JSON-LD or HTML fallback."""
    
    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Optional[str]:
        # 1. Try JSON-LD
        val = super().parse(json_data, meta, soup)
        if val:
            return val
        
        # 2. HTML Fallback
        desc_div = soup.find('div', class_='description')
        if desc_div:
            return desc_div.get_text(separator='\n', strip=True)
        
        return None


class CarModelParser(BaseFieldParser):
    """Extracts car model from JSON-LD or infers from title."""
    
    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Optional[str]:
        # 1. Direct JSON-LD model field
        if json_data.get('model'):
            return json_data['model']
            
        # 2. Infer from title by removing make and year
        try:
            title = json_data.get('name') or ''
            if not title and soup.find('title'):
                title = soup.find('title').text
                
            make = json_data.get('manufacturer') or json_data.get('brand', {}).get('name')
            
            if title and make:
                # Remove make (case insensitive)
                clean_title = re.sub(make, '', title, flags=re.IGNORECASE).strip()
                # Remove year (4 digits like 2020 or 1999)
                clean_title = re.sub(r'\b(19|20)\d{2}\b', '', clean_title).strip()
                # Remove common extra words
                clean_title = re.sub(
                    r'\b(Professional|Edition|Pack|Sport)\b', 
                    '', 
                    clean_title, 
                    flags=re.IGNORECASE
                ).strip()
                
                if clean_title:
                    return clean_title.split()[0]
        except Exception:
            pass
        
        return None


class CityParser(BaseFieldParser):
    """Parses city/region from seller info section."""
    
    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Optional[str]:
        # 1. HTML: Look for location pin in seller info
        try:
            seller_div = soup.find('div', class_='main-seller-info')
            if seller_div:
                pin = seller_div.find('svg', class_='ci-location-pin')
                if pin:
                    location_span = pin.find_next('span')
                    if location_span:
                        return location_span.get_text(strip=True)
        except Exception:
            pass

        # 2. JSON-LD: areaServed field
        try:
            geo = json_data.get('offers', {}).get('seller', {}).get('areaServed', {})
            if geo and 'name' in geo:
                return geo['name']
        except Exception:
            pass
            
        return None


class SellerNameParser(BaseFieldParser):
    """Extracts seller name from JSON-LD or HTML."""
    
    def parse(self, json_data: Dict, meta: str, soup: BeautifulSoup) -> Optional[str]:
        # 1. JSON-LD
        name = json_data.get('offers', {}).get('seller', {}).get('name')
        if name:
            return name
        
        # 2. HTML: Dealer link in seller info
        try:
            seller_div = soup.find('div', class_='main-seller-info')
            if seller_div:
                link = seller_div.find('a', class_=re.compile(r'tw-text-lg'))
                if link:
                    return link.get_text(strip=True)
        except Exception:
            pass
        
        return None

