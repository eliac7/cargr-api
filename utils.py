import json
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup


def extract_json_ld(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract structured data from JSON-LD script tags."""
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                # Valid types for vehicles in car.gr JSON-LD
                if data.get('@type') in ['Car', 'Vehicle', 'Product'] or 'offers' in data:
                    return data
        except (json.JSONDecodeError, TypeError):
            continue
    return {}


def extract_meta_description(soup: BeautifulSoup) -> str:
    """Extract description from meta tags."""
    meta = (
        soup.find('meta', {'property': 'og:description'}) or 
        soup.find('meta', {'name': 'description'})
    )
    return meta['content'] if meta else ""


def safe_int(val: Any) -> Optional[int]:
    """Safely convert value to integer."""
    try:
        if isinstance(val, str):
            val = val.replace('.', '').replace(',', '')
        return int(val)
    except (ValueError, TypeError):
        return None


def safe_float(val: Any) -> Optional[float]:
    """Safely convert value to float."""
    try:
        if isinstance(val, str):
            val = val.replace('.', '').replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return None

