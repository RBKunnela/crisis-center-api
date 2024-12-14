# Finnish Crisis Center Finder API

Simple API to find the nearest crisis center in Finland based on city location, providing comprehensive support and emergency information.

## Features
- Find nearest crisis centers by city
- Retrieve travel times (driving and public transit)
- Get alternative center options
- Multilingual support (Finnish, Swedish, English)
- Emergency contact information

## Setup

### Prerequisites
- Python 3.8+
- Google Maps API Key (set as environment variable)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/crisis-center-api.git
cd crisis-center-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set Google Maps API Key:
```bash
export GOOGLE_MAPS_API_KEY='your_api_key_here'
```

4. Run locally:
```bash
python app.py
```

## Docker Build & Run

```bash
# Build Docker image
docker build -t crisis-center-api .

# Run Docker container
docker run -p 5000:5000 \
    -e GOOGLE_MAPS_API_KEY='your_api_key_here' \
    crisis-center-api
```

## API Endpoints

### 1. Find Nearest Crisis Center
- **Endpoint:** `/find-nearest`
- **Method:** GET
- **Query Parameter:** `city` (required)

#### Example Request
```bash
curl "https://api.aiagentchatbot.com/find-nearest?city=Helsinki"
```

#### Example Response
```json
{
    "nearest_center": {
        "name": "Helsingin kriisikeskus",
        "region": "Helsinki",
        "phone": "09 4135 0510",
        "distance": {
            "straight_line_km": 0.01,
            "driving": {
                "duration": "5 mins", 
                "distance": "2.1 km"
            }
        }
    },
    "emergency_contacts": {
        "national_crisis_line": "09 25250111",
        "emergency_number": "112"
    }
}
```

### 2. Health Check
- **Endpoint:** `/health`
- **Method:** GET
- Returns service status and version information

## Error Handling
- 400: Missing city parameter
- 503: Service temporarily unavailable
- 500: Unexpected server error

## Emergency Contacts
- **National Crisis Line:** 09 25250111
- **Emergency Number:** 112

## Supported Languages
- Finnish
- Swedish
- English

## Deployment
- Hosted at: https://api.aiagentchatbot.com
- Supports CORS
- Logging enabled for monitoring and debugging

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
[Insert your license here]