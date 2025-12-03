# Car.gr API

Unofficial FastAPI-based API for scraping and accessing car listings from [car.gr](https://www.car.gr), the largest Greek car marketplace.

---

## Features

- 🔍 **Search API**: Search using native car.gr filters
- 📋 **Car Details**: Get detailed specifications, pricing, and seller info
- 🚗 **Comprehensive Data**: Engine specs, Euro class, KTEO, and more
- 🛡️ **Stealth Requests**: Retries and stealth techniques to reduce blocking
- ⚡ **FastAPI**: High-performance API with auto-generated Swagger docs

---

## Installation

### Prerequisites

- Python **3.13+**
- **uv** (recommended) or **pip**

---

### Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd cargr-api
```

2. **Install dependencies**

Using **uv** (recommended):

```bash
uv pip install -e .
```

Using **pip**:

```bash
pip install -e .
```

---

## Docker

Build and run the containerized application:

```bash
# Build image
docker build -t cargr-api .

# Run container
docker run -p 8000:8000 cargr-api
```

The API will be available at:

```
http://localhost:8000
```

---

## Usage

### Running the Server

```bash
uvicorn main:app --reload
```

or, if you run the `main.py` directly (if provided):

```bash
python main.py
```

---

### API Documentation

Once running, access:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## MCP Server Integration

This API includes a Model Context Protocol (MCP) server, allowing AI assistants (like Claude Desktop, Cursor, etc.) to directly search for cars and retrieve details using natural language.

### Connecting via SSE (Recommended)

To use this API with an MCP client, add the following configuration to your client's settings (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cargr-mcp": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

Once connected, the AI will have access to the following tools:
- `search_car_listings`: Search for cars using filters (requires fetching filter IDs first).
- `get_car_details_by_id`: Get full details for a specific car listing.
- `get_available_filters`: Retrieve valid IDs for makes, models, and other categorical fields.

### Important Note for AI Usage

When using the `search` tool, the AI must **first** use `get_available_filters` to look up the correct IDs for parameters like `make`, `model`, `fuel_type`, etc. Guessing IDs will likely result in empty or incorrect results.

---

## API Endpoints

### 1. Get Car Details

Retrieve full details for a specific classified listing.

```http
GET /api/car/{car_id}
```

**Example:**

```bash
curl http://127.0.0.1:8000/api/car/48949544
```

**Response:**

```json
{
  "car_id": "48949544",
  "title": "Fiat 2020 Fiorino Professional",
  "price": 10200.0,
  "make": "Fiat",
  "model": "Fiorino",
  "km": 97000.0,
  "engine": 1300,
  "bhp": 95,
  "fueltype": "Diesel",
  "transmission": "Manual",
  "euro_class": "Euro 6",
  "city": "Άγιος Δημήτριος, Ν. Αττικής",
  "postal_code": "17341",
  "is_dealer": true,
  "seller_name": "Tolias Edition",
  "url": "https://www.car.gr/classifieds/vans/view/48949544",
  "images": ["https://.../1.jpg", "https://.../2.jpg"],
  "features": ["air conditioning", "abs"],
  "views": 120,
  "modified_at": "2025-11-10T12:34:56Z",
  "scraped_at": "2025-12-03T15:00:00Z"
}
```

---

### 2. Search Cars

Search for listings. This endpoint accepts query parameters that map to car.gr's search filters.

```http
GET /api/search?{query_params}
```

**Example:**

```bash
curl "http://127.0.0.1:8000/api/search?make=13302&fuel_type=2&price-to=12000"
```

**Common Parameters (examples):**

| Parameter           | Description     | Example                    |
| ------------------- | --------------- | -------------------------- |
| `make`              | Manufacturer ID | `13301` (Toyota)           |
| `model`             | Model ID        | `14911` (Aygo)             |
| `price-from`        | Min price (€)   | `5000`                     |
| `price-to`          | Max price (€)   | `15000`                    |
| `registration-from` | Min year        | `2018`                     |
| `fuel_type`         | Fuel ID         | `1` (Petrol), `2` (Diesel) |
| `gearbox_type`      | Transmission    | `manual`, `automatic`      |
| `city`              | City name or id | `Athens` or id             |
| `page`              | Page number     | `1`                        |

**Response:**

Returns an array of `Car` objects matching the query, along with pagination metadata.

---

## Data Model

The API returns a comprehensive `Car` object with fields such as:

- **Identification**
  - `car_id`, `title`, `url`
- **Categorization**
  - `make`, `model`, `category`
- **Specifications**
  - `release_date`, `engine` (cc), `km`, `bhp`, `color`, `fueltype`, `transmission`, `doors`, `seats`
- **Regulatory**
  - `euro_class`, `road_tax`, `kteo_expiry` (MOT)
- **Location**
  - `city`, `region`, `postal_code`
- **Seller**
  - `is_dealer` (bool), `seller_name`, `description`, `views`, `modified_at`
- **Media**
  - `images` (array of image URLs)
- **Features**
  - `features` (array of strings)
- **Metadata**
  - `scraped_at` (ISO 8601 timestamp)

---

## Architecture

- **`main.py`**: FastAPI application with route handlers
- **`models.py`**: Pydantic models for request/response validation
- **`parser.py`**: Web scraping logic using BeautifulSoup and stealth requests
- **`services/`**: Modular scraping, caching, and rate-limiting helpers
- **`docker/`**: Dockerfile and helper scripts

### Parsing strategies

1. JSON-LD structured data (primary, when available)
2. HTML parsing with BeautifulSoup and targeted selectors
3. Regex fallbacks for specific embedded values
4. Tailwind grid/table parsing for complex layouts

---

## Rate Limiting & Ethics

This project includes defensive measures to avoid overloading car.gr:

- Randomized delays between requests
- Exponential backoff and retry logic
- Rate-limit detection and respectful pausing
- Optional caching layer to reduce repeated requests

**Please use responsibly**, respect car.gr's `robots.txt`, and read their Terms of Service before scraping. Avoid high-frequency scraping or commercial use without permission.

---

## Dependencies

Key Python packages used:

- `fastapi`
- `uvicorn`
- `beautifulsoup4`
- `stealth-requests` (or similar stealth HTTP client)
- `pydantic`
- `requests`
- optional: `httpx`, `tenacity`, `cachetools`

Install via the provided `setup.py`/`pyproject.toml` or the editable install command above.

---

## Examples

Search for a Toyota petrol under €20,000:

```bash
curl "http://127.0.0.1:8000/api/search?make=13301&price-to=20000&fuel_type=1"
```

Get details for a specific listing:

```bash
curl http://127.0.0.1:8000/api/car/48949544
```

---

## License & Disclaimer

This project is provided **for educational purposes only**. By using this software you agree to:

- Respect car.gr's `robots.txt` and Terms of Service
- Not use this tool for abusive, high-frequency, or commercial scraping without explicit permission
- Understand that the authors are not responsible for misuse or any legal consequences that may arise

No warranty, use at your own risk.

---

## Contributing

Contributions, bug reports, and pull requests are welcome. Please open issues for feature requests or problems, and follow the project's code style and testing guidelines.

---

## Contact

For questions or help, open an issue on the GitHub repository.
