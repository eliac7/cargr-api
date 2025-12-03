BASE_URL = 'https://www.car.gr'
CAR_VIEW_PATH = '/classifieds/cars/view/'

REGEX_PATTERNS = {
    'km': r'Χιλιόμετρα:\s*([\d\.]+)',
    'engine': r'Κυβικά:\s*([\d\.]+)\s*cc',
    'bhp': r'Ιπποδύναμη:\s*(\d+)\s*hp',
    'release_date': r'Χρονολογία:\s*(\d{1,2})\s*/\s*(\d{4})',
    'fueltype': r'Καύσιμο:\s*([^\s]+)',
    'transmission': r'Σασμάν:\s*([^\s]+)',
    'results_count': r'(\d+)\s+αγγελίες',
    'car_path': r'/(?:classifieds/|used-)[^/]+/(?:view/)?(\d+)',
    'car_id': r'^(\d+)',
    'price': r'€',
}

IMAGE_DOMAIN = 'static.car.gr'
IMAGE_SUFFIX = '_z.jpg'

# Timing delays (in seconds)
TIMING = {
    'session_init_delay': (1, 2),
    'search_page_delay': (2, 3),
    'car_page_delay': (1, 3),
    'error_delay': (5, 8),
    'retry_base_delay': 2,
    'rate_limit_delay_range': (5, 10),
}

REQUEST_SETTINGS = {
    'timeout': 60,
    'max_retries': 3,
    'session_timeout': 30,
}

