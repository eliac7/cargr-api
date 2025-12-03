import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup, Tag
from stealth_requests import StealthSession

from config import BASE_URL

logger = logging.getLogger(__name__)

@dataclass
class FilterOption:
    label: str
    value: str
    count: Optional[int] = None

@dataclass
class FilterDefinition:
    query_param: str
    label: str
    type: str  # 'select', 'checkbox', 'range', 'button_group'
    options: List[FilterOption]

class FilterDiscoveryParser:
    """Parses the Car.gr search page to dynamically extract available filters."""

    def __init__(self, search_url: str = f"{BASE_URL}/classifieds/cars/"):
        self.url = search_url
        self.session = StealthSession()
        self.html = self._fetch_page()
        self.soup = BeautifulSoup(self.html, 'html.parser')

    def _fetch_page(self) -> str:
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch search page for filters: {e}")
            return ""

    def _extract_count(self, text: str) -> Optional[int]:
        """Extracts count from 'Label (1.234)'."""
        match = re.search(r'\((\d+[\.\d]*)\)', text)
        if match:
            return int(match.group(1).replace('.', ''))
        return None

    def _clean_label(self, text: str) -> str:
        """Removes count suffix from label."""
        return re.sub(r'\s*\(\d+[\.\d]*\)$', '', text).strip()

    def _parse_options_from_select(self, select: Tag) -> List[FilterOption]:
        """Extracts clean options from a select tag."""
        options = []
        for option in select.find_all('option'):
            value = option.get('value')
            raw_text = option.get_text(strip=True)
            
            # Skip placeholders
            if not value or not raw_text or raw_text in ["Όλα", "Από", "Έως", "-", "Μάρκα", "Μοντέλο"]:
                continue

            options.append(FilterOption(
                label=self._clean_label(raw_text),
                value=value,
                count=self._extract_count(raw_text)
            ))
        return options

    def _identify_filter_type(self, options: List[FilterOption]) -> Optional[str]:
        """
        Identifies what kind of filter a list of options represents based on unique keywords.
        """
        labels = [o.label.lower() for o in options]
        values = [o.value for o in options]
        
        if any('βενζίνη' in l for l in labels) and any('πετρέλαιο' in l for l in labels):
            return 'fuel_type'
        
        if any('euro 6' in l for l in labels) and any('euro 5' in l for l in labels):
            return 'euroclass'
            
        if 'ασημί' in labels and 'μαύρο' in labels and 'κόκκινο' in labels:
            return 'exterior_color'
            
        if 'μεταλλικό' in labels and 'ματ' in labels:
            return 'exterior_color_type'

        if 'μπεζ' in labels and 'γκρι' in labels and 'δίχρωμο' in labels:
            return 'interior_color'
        
        if 'alcantara' in labels and 'βελούδο' in labels:
            return 'interior_type'

        if 'με φωτογραφίες' in labels:
            return 'media_types'

        if any('πάνω από 1 χρόνο' in l for l in labels):
            return 'kteo'

        if 'μονή' in labels and 'ζυγή' in labels:
            return 'number_plate_ending'
            
        if 'audi' in labels and 'bmw' in labels:
            return 'make'
            
        if '2/3' in labels and '4/5' in labels:
            return 'doors'

        if '2' in values and '4' in values and '5' in values and len(values) > 5:
            return 'seats'

        return None

    def _parse_button_group(self, container_id: str) -> List[FilterOption]:
        """Parses filters that use button groups instead of selects."""
        options = []
        container = self.soup.find(id=container_id)
        if not container:
            return []
            
        value_map = {
            'Χειροκίνητο': 'manual',
            'Αυτόματο': 'automatic',
            'Ημιαυτόματο': 'semi_automatic',
            'Προσθιοκίνητο (FWD)': 'fwd',
            'Πισωκίνητο (RWD)': 'rwd',
            'Τετρακίνητο (4x4)': '4x4',
            'Έμπορος': 'dealer',
            'Ιδιώτης': 'private',
            'Όλα': '',
            'Με ζημιά': 't',  # True
            'Χωρίς ζημιά': 'f' # False
        }

        for btn in container.find_all('button'):
            text = btn.get_text(strip=True)
            value = btn.get('value') or value_map.get(text)
            
            if text and value and value != "":
                options.append(FilterOption(label=text, value=value))
                
        return options

    def _parse_features(self) -> List[FilterOption]:
        """Parses feature checkboxes."""
        options = []
        checkboxes = self.soup.find_all('div', class_='c-checkbox-wrapper')
        
        seen = set()
        for box in checkboxes:
            inp = box.find('input')
            lbl = box.find('label')
            
            if inp and lbl:
                val = inp.get('value') or inp.get('name')
                text = lbl.get_text(strip=True)
                
                if val and val.isdigit() and len(val) >= 3 and val not in seen:
                    options.append(FilterOption(label=text, value=val))
                    seen.add(val)
                    
        return sorted(options, key=lambda x: x.label)

    def get_filters(self) -> Dict[str, FilterDefinition]:
        filters = {}

        for select in self.soup.find_all('select'):
            opts = self._parse_options_from_select(select)
            if not opts:
                continue
                
            filter_type = self._identify_filter_type(opts)
            if filter_type and filter_type not in filters:
                labels = {
                    'make': 'Μάρκα',
                    'fuel_type': 'Καύσιμο',
                    'euroclass': 'Κλάση Ρύπων',
                    'exterior_color': 'Χρώμα Εξωτερικό',
                    'exterior_color_type': 'Τύπος Χρώματος',
                    'interior_color': 'Χρώμα Εσωτερικό',
                    'interior_type': 'Σαλόνι',
                    'media_types': 'Πολυμέσα',
                    'kteo': 'ΚΤΕΟ',
                    'number_plate_ending': 'Πινακίδα',
                    'doors': 'Πόρτες',
                    'seats': 'Θέσεις'
                }
                
                filters[filter_type] = FilterDefinition(
                    query_param=filter_type,
                    label=labels.get(filter_type, filter_type),
                    type='select',
                    options=opts
                )

        button_configs = [
            ('gearbox_type', 'Σασμάν'),
            ('drive_type', 'Κίνηση'),
            ('seller_type', 'Τύπος Πωλητή'),
            ('crashed', 'Ζημιά'),
            ('audit_options', 'Τεχνικοί Έλεγχοι')
        ]
        
        for div_id, label in button_configs:
            opts = self._parse_button_group(div_id)
            if opts:
                filters[div_id] = FilterDefinition(
                    query_param=div_id,
                    label=label,
                    type='button_group',
                    options=opts
                )

        features = self._parse_features()
        if features:
            filters['feature'] = FilterDefinition(
                query_param='feature',
                label='Ιδιαιτερότητες / Έξτρα',
                type='checkbox',
                options=features
            )

        ranges = [
            ('price', 'Τιμή (€)'),
            ('registration', 'Χρονολογία'),
            ('mileage', 'Χιλιόμετρα'),
            ('engine_size', 'Κυβικά (cc)'),
            ('engine_power', 'Ιπποδύναμη (bhp)'),
        ]
        for key, label in ranges:
            filters[key] = FilterDefinition(
                query_param=f"{key}-from / {key}-to",
                label=label,
                type='range',
                options=[]
            )

        return filters

def get_available_filters() -> Dict[str, Any]:
    parser = FilterDiscoveryParser()
    return {k: asdict(v) for k, v in parser.get_filters().items()}

if __name__ == "__main__":
    import json
    print(json.dumps(get_available_filters(), indent=2, ensure_ascii=False))