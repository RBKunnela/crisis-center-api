# Required imports
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import googlemaps
from typing import Tuple, Optional
import math
import logging
import os

# Configure logging to help debug any issues
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Google Maps client with API key from environment variable
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
if not GOOGLE_MAPS_API_KEY:
    logger.warning("Google Maps API key not found in environment variables")

try:
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    logger.info("Successfully initialized Google Maps client")
except Exception as e:
    logger.error(f"Failed to initialize Google Maps client: {str(e)}")
    gmaps = None

# Create Flask app instance
app = Flask(__name__)
CORS(app)

# Log startup
logger.info("Starting Crisis Center API application...")
logger.info("Configuring routes...")

# HTML template for the root endpoint - provides API documentation
HOME_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Crisis Center Finder API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }
        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Crisis Center Finder API</h1>
    <p>Welcome to the Finnish Crisis Center Finder API. This service helps locate the nearest crisis center based on your city location.</p>
    
    <h2>Available Endpoints:</h2>
    <h3>1. Find Nearest Center</h3>
    <p><code>GET /find-nearest</code></p>
    <p><strong>Parameters:</strong></p>
    <ul>
        <li><code>city</code> (required): Name of the city in Finland</li>
    </ul>
    
    <h3>Example Request:</h3>
    <pre>GET /find-nearest?city=Helsinki</pre>
    
    <h3>Example Response:</h3>
    <pre>
{
    "nearest_center": "Helsingin kriisikeskus",
    "region": "Helsinki",
    "phone": "09 4135 0510",
    "distance": 0.0,
    "national_crisis_line": "09 25250111",
    "coordinates_source": "google_maps"
}
    </pre>

    <h2>Emergency Contact</h2>
    <p>National Crisis Helpline: 09 25250111 (24/7)</p>
</body>
</html>
'''

# Database of crisis centers with their coordinates
CRISIS_CENTERS = [
    {
        "region": "Helsinki",
        "name": "Helsingin kriisikeskus",
        "phone": "09 4135 0510",
        "latitude": 60.1699,
        "longitude": 24.9384
    },
    {
        "region": "Jyväskylä",
        "name": "Jyväskylän kriisikeskus Mobile",
        "phone": "044 7888 470",
        "latitude": 62.2426,
        "longitude": 25.7475
    },
    {
        "region": "Kuopio",
        "name": "Kuopion kriisikeskus",
        "phone": "017 262 7733",
        "latitude": 62.8924,
        "longitude": 27.6782
    },
    {
        "region": "Oulu",
        "name": "Oulun kriisikeskus",
        "phone": "044 3690 500",
        "latitude": 65.0121,
        "longitude": 25.4651
    },
    {
        "region": "Rovaniemi",
        "name": "Rovaniemen kriisikeskus",
        "phone": "040 553 7508",
        "latitude": 66.5039,
        "longitude": 25.7294
    }
]

def get_city_coordinates(city: str) -> Optional[Tuple[float, float]]:
    """
    Get the coordinates of a city using Google Maps Geocoding API.
    Returns tuple of (latitude, longitude) if found, None if not found or not in Finland.
    """
    if not gmaps:
        logger.warning("Google Maps client not initialized, cannot get coordinates")
        return None

    try:
        # Add 'Finland' to ensure we get Finnish cities
        search_query = f"{city}, Finland"
        result = gmaps.geocode(search_query)
        
        if not result:
            logger.warning(f"No results found for {city}")
            return None
            
        location = result[0]['geometry']['location']
        
        # Verify the result is in Finland
        address_components = result[0]['address_components']
        country = next((comp['short_name'] for comp in address_components 
                       if 'country' in comp['types']), None)
                       
        if country != 'FI':
            logger.warning(f"Result for {city} was not in Finland")
            return None
            
        return (location['lat'], location['lng'])
        
    except Exception as e:
        logger.error(f"Error getting coordinates for {city}: {str(e)}")
        return None

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth."""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

@app.route('/')
def home():
    """Serve the API documentation page."""
    logger.info("Root endpoint accessed")
    return render_template_string(HOME_PAGE)

@app.route('/find-nearest', methods=['GET'])
def find_nearest_center():
    """Find the nearest crisis center to a given city."""
    city = request.args.get('city', '')
    if not city:
        return jsonify({
            "error": "City parameter is required"
        }), 400
    
    # Try to get coordinates from Google Maps
    coordinates = None
    if gmaps:
        try:
            coordinates = get_city_coordinates(city)
            if coordinates:
                logger.info(f"Successfully geocoded {city}")
        except Exception as e:
            logger.error(f"Geocoding failed for {city}: {str(e)}")
    
    if coordinates:
        user_lat, user_lon = coordinates
    else:
        # Fall back to center of Finland if geocoding fails
        user_lat, user_lon = 62.2426, 25.7475
        logger.warning(f"Using fallback coordinates for {city}")
    
    # Find nearest crisis center
    nearest_center = min(
        CRISIS_CENTERS,
        key=lambda center: haversine_distance(
            user_lat, user_lon,
            center['latitude'], center['longitude']
        )
    )
    
    # Calculate distance
    distance = haversine_distance(
        user_lat, user_lon,
        nearest_center['latitude'], nearest_center['longitude']
    )
    
    return jsonify({
        "nearest_center": nearest_center['name'],
        "region": nearest_center['region'],
        "phone": nearest_center['phone'],
        "distance": round(distance, 2),
        "national_crisis_line": "09 25250111",
        "coordinates_source": "google_maps" if coordinates else "fallback"
    })

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "google_maps_available": gmaps is not None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)