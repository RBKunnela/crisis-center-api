# Finnish Crisis Center Finder API

Simple API to find the nearest crisis center in Finland based on city location.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run locally:
```bash
python app.py
```

## Docker Build & Run

```bash
docker build -t crisis-center-api .
docker run -p 5000:5000 crisis-center-api
```

## API Usage

GET `/find-nearest?city=Helsinki`

Example response:
```json
{
    "nearest_center": "Helsingin kriisikeskus",
    "region": "Helsinki",
    "phone": "09 4135 0510",
    "distance": 0.0,
    "national_crisis_line": "09 25250111"
}
```