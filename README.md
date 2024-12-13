# crisis-center-api

# Finnish Crisis Center Finder API

This API helps find the nearest crisis center in Finland based on a given city location. It's designed to support crisis support services by providing quick access to nearest help centers.

## Features

- Find nearest crisis center based on city name
- Returns center name, region, contact information, and distance
- Always provides national crisis line as backup
- Handles unknown cities by finding closest center from central Finland

## API Endpoint

`GET /find-nearest`

### Parameters

- `city` (required): Name of the city in Finland

### Example Response

```json
{
    "nearest_center": "Helsingin kriisikeskus",
    "region": "Helsinki",
    "phone": "09 4135 0510",
    "distance": 2.5,
    "national_crisis_line": "09 25250111"
}
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python app.py
```

## Docker Deployment

Build and run with Docker:

```bash
docker build -t crisis-center-api .
docker run -p 5000:5000 crisis-center-api
```

## Crisis Support

If you need immediate support, call the national crisis helpline: 09 25250111 (24/7)
