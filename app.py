from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import googlemaps
from typing import List, Dict, Tuple, Optional
import math
import logging
import os
import requests
from datetime import datetime, date

# Configure logging for better debugging and monitoring
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Placeholder functions for validation
def is_valid_finnish_phone(phone: str) -> bool:
    """Basic phone number validation for Finnish numbers."""
    # Remove spaces and hyphens
    cleaned_phone = phone.replace(' ', '').replace('-', '')
    
    # Check if it contains only digits and has a reasonable length
    return len(cleaned_phone) >= 9 and cleaned_phone.isdigit()

def is_within_finland(lat: float, lon: float) -> bool:
    """Check if coordinates are within Finland's approximate boundaries."""
    return (59.0 <= lat <= 70.0) and (20.0 <= lon <= 32.0)

def get_day_range(start_day: str, end_day: str) -> List[str]:
    """Generate a list of days between start and end."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    start_index = days.index(start_day)
    end_index = days.index(end_day)
    
    if start_index <= end_index:
        return days[start_index:end_index+1]
    else:
        return days[start_index:] + days[:end_index+1]

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

# Create Flask app instance and enable CORS
app = Flask(__name__)
CORS(app)

# Log startup information
logger.info("Starting Enhanced Crisis Center API application...")
logger.info("Configuring routes and services...")

# HTML template for the API documentation page
HOME_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Crisis Center Finder API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }
        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Enhanced Crisis Center Finder API</h1>
    <p>Welcome to the Finnish Crisis Center Finder API. This service helps locate the nearest crisis centers with travel information and alternatives.</p>
    
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
    "request_info": {
        "city": "Helsinki",
        "coordinates_source": "google_maps",
        "timestamp": "2024-12-14 15:30:00"
    },
    "nearest_center": {
        "name": "Helsingin kriisikeskus",
        "region": "Helsinki",
        "phone": "09 4135 0510",
        "distance": {
            "straight_line_km": 0.01,
            "driving": {
                "duration": "5 mins",
                "distance": "2.1 km"
            },
            "public_transit": {
                "duration": "15 mins",
                "distance": "2.3 km"
            }
        }
    },
    "alternative_centers": [...],
    "emergency_contacts": {
        "national_crisis_line": "09 25250111",
        "emergency_number": "112"
    }
}
    </pre>

    <h2>Emergency Contacts</h2>
    <p>National Crisis Helpline: 09 25250111 (24/7)</p>
    <p>Emergency Number: 112</p>
</body>
</html>
'''

def verify_crisis_center_data(center_id: str, new_data: dict) -> bool:
    """
    Verify and update crisis center information.
    Returns True if verification was successful.
    """
    required_fields = {'name', 'phone', 'latitude', 'longitude', 'region'}
    
    # Check that all required fields are present
    if not all(field in new_data for field in required_fields):
        logger.error(f"Missing required fields for center {center_id}")
        return False
    
    # Verify phone number format
    if not is_valid_finnish_phone(new_data['phone']):
        logger.error(f"Invalid phone number format for center {center_id}")
        return False
    
    # Verify coordinates are within Finland
    if not is_within_finland(new_data['latitude'], new_data['longitude']):
        logger.error(f"Coordinates outside Finland for center {center_id}")
        return False
    
    # Add verification timestamp
    new_data['last_verified'] = date.today().isoformat()
    
    return True

def parse_service_hours(hours_str: str) -> Dict[str, str]:
    """Convert service hours string into structured format."""
    try:
        if hours_str == "24/7":
            return {day: "00:00-24:00" for day in 
                   ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
        
        schedule = {}
        parts = hours_str.split(", ")
        for part in parts:
            days, times = part.split(" ", 1)
            if "-" in days:
                start_day, end_day = days.split("-")
                day_range = get_day_range(start_day, end_day)
                for day in day_range:
                    schedule[day] = times
            else:
                schedule[days] = times
        return schedule
    except Exception as e:
        logger.error(f"Error parsing service hours: {str(e)}")
        return {"error": "Hours format not recognized"}

# Comprehensive database of crisis centers
CRISIS_CENTERS = [
    {
        "region": "Helsinki",
        "name": "Helsingin kriisikeskus",
        "phone": "09 4135 0510",
        "latitude": 60.1699,
        "longitude": 24.9384,
        "hours": "Mon-Fri 9:00-16:00",
        "languages": ["Finnish", "Swedish", "English"]
    },
    {
        "region": "Jyväskylä",
        "name": "Jyväskylän kriisikeskus Mobile",
        "phone": "044 7888 470",
        "latitude": 62.2426,
        "longitude": 25.7475,
        "hours": "24/7",
        "languages": ["Finnish", "English"]
    },
    {
        "region": "Kuopio",
        "name": "Kuopion kriisikeskus",
        "phone": "017 262 7733",
        "latitude": 62.8924,
        "longitude": 27.6782,
        "hours": "Mon-Fri 8:00-16:00",
        "languages": ["Finnish"]
    },
    {
        "region": "Oulu",
        "name": "Oulun kriisikeskus",
        "phone": "044 3690 500",
        "latitude": 65.0121,
        "longitude": 25.4651,
        "hours": "24/7",
        "languages": ["Finnish", "English"]
    },
    {
        "region": "Rovaniemi",
        "name": "Rovaniemen kriisikeskus",
        "phone": "040 553 7508",
        "latitude": 66.5039,
        "longitude": 25.7294,
        "hours": "Mon-Fri 9:00-17:00",
        "languages": ["Finnish", "English"]
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

def estimate_travel_time(origin_lat: float, origin_lon: float, 
                        dest_lat: float, dest_lon: float) -> Dict[str, any]:
    """Enhanced travel time estimation with comprehensive error handling."""
    try:
        origins = f"{origin_lat},{origin_lon}"
        destinations = f"{dest_lat},{dest_lon}"
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json"
        
        travel_info = {
            'driving': {'duration': 'Unknown', 'distance': 'Unknown'},
            'transit': {'duration': 'Unknown', 'distance': 'Unknown'}
        }

        # Try driving route first
        try:
            params = {
                'origins': origins,
                'destinations': destinations,
                'mode': 'driving',
                'language': 'fi',
                'key': GOOGLE_MAPS_API_KEY
            }
            driving_response = requests.get(url, params=params, timeout=5).json()
            
            if driving_response.get('status') == 'OK':
                elements = driving_response['rows'][0]['elements'][0]
                if elements.get('status') == 'OK':
                    travel_info['driving'] = {
                        'duration': elements['duration']['text'],
                        'distance': elements['distance']['text']
                    }
        except Exception as e:
            logger.error(f"Driving route estimation failed: {str(e)}")

        # Try transit route next
        try:
            params['mode'] = 'transit'
            transit_response = requests.get(url, params=params, timeout=5).json()
            
            if transit_response.get('status') == 'OK':
                elements = transit_response['rows'][0]['elements'][0]
                if elements.get('status') == 'OK':
                    travel_info['transit'] = {
                        'duration': elements['duration']['text'],
                        'distance': elements['distance']['text']
                    }
        except Exception as e:
            logger.error(f"Transit route estimation failed: {str(e)}")

        # Add additional context about availability
        travel_info['availability'] = {
            'driving_available': travel_info['driving']['duration'] != 'Unknown',
            'transit_available': travel_info['transit']['duration'] != 'Unknown'
        }
        
        return travel_info

    except Exception as e:
        logger.error(f"Travel time estimation completely failed: {str(e)}")
        return {
            'driving': {'duration': 'Service unavailable', 'distance': 'Service unavailable'},
            'transit': {'duration': 'Service unavailable', 'distance': 'Service unavailable'},
            'availability': {'driving_available': False, 'transit_available': False}
        }
        
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth."""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def find_alternative_centers(lat: float, lon: float, 
                           primary_center: Dict) -> List[Dict]:
    """Find the next 2 closest crisis centers as alternatives."""
    return sorted(
        [center for center in CRISIS_CENTERS if center != primary_center],
        key=lambda c: haversine_distance(lat, lon, c['latitude'], c['longitude'])
    )[:2]

class CrisisCenterError(Exception):
    """Base exception class for crisis center operations."""
    pass

class GeocodeError(CrisisCenterError):
    """Raised when geocoding operations fail."""
    pass

class TravelTimeError(CrisisCenterError):
    """Raised when travel time estimation fails."""
    pass

def handle_api_error(func):
    """Decorator for handling API errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GeocodeError as e:
            logger.error(f"Geocoding error: {str(e)}")
            return jsonify({
                "error": "Location service temporarily unavailable",
                "fallback": "Using approximate location",
                "emergency_contacts": {
                    "national_crisis_line": "09 25250111",
                    "emergency_number": "112"
                }
            }), 503
        except TravelTimeError as e:
            logger.error(f"Travel time estimation error: {str(e)}")
            return jsonify({
                "error": "Travel time estimation unavailable",
                "fallback": "Using straight-line distance only",
                "emergency_contacts": {
                    "national_crisis_line": "09 25250111",
                    "emergency_number": "112"
                }
            }), 503
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                "error": "Service temporarily unavailable",
                "emergency_contacts": {
                    "national_crisis_line": "09 25250111",
                    "emergency_number": "112"
                }
            }), 500
    return wrapper

def validate_finnish_city(city: str) -> bool:
    """
    Validate if the input is a potentially valid Finnish city.
    
    Args:
        city (str): City name to validate
    
    Returns:
        bool: True if city seems valid, False otherwise
    """
    # List of known Finnish cities and regions
    FINNISH_CITIES = {
        'helsinki', 'espoo', 'tampere', 'vantaa', 'oulu', 
        'turku', 'jyväskylä', 'lahti', 'kuopio', 'pori', 
        'helsinki', 'rovaniemi', 'joensuu', 'vaasa'
    }
    
    # Basic validation checks
    if not city:
        return False
    
    # Remove whitespace and convert to lowercase
    normalized_city = city.strip().lower()
    
    # Check against known cities
    if normalized_city in FINNISH_CITIES:
        return True
    
    # Additional checks
    if len(normalized_city) < 2:  # Too short
        return False
    
    if normalized_city.isdigit():  # Purely numeric
        return False
    
    # Optional: Add more sophisticated checks like regex for valid city name patterns
    return True

@app.route('/')
def home():
    """Serve the API documentation page."""
    logger.info("Root endpoint accessed")
    return render_template_string(HOME_PAGE)

@app.route('/find-nearest', methods=['GET'])
def find_nearest_center():
    city = request.args.get('city', '').strip()
    
    if not validate_finnish_city(city):
        return jsonify({
            "error": "Invalid city input. Please provide a valid Finnish city.",
            "emergency_contacts": {
                "national_crisis_line": "09 25250111",
                "emergency_number": "112"
            }
        }), 400
    
    # Fetch updated crisis center list
    global CRISIS_CENTERS
    CRISIS_CENTERS = fetch_crisis_centers()

    coordinates = get_city_coordinates(city) if gmaps else None
    if coordinates:
        user_lat, user_lon = coordinates
    else:
        user_lat, user_lon = 62.2426, 25.7475  # Fallback location
        logger.warning(f"Using fallback coordinates for {city}")
    
    nearest_center = min(
        CRISIS_CENTERS,
        key=lambda center: haversine_distance(
            user_lat, user_lon,
            center['latitude'], center['longitude']
        )
    )
    
    distance = haversine_distance(
        user_lat, user_lon,
        nearest_center['latitude'], nearest_center['longitude']
    )
    
    travel_info = estimate_travel_time(
        user_lat, user_lon,
        nearest_center['latitude'], nearest_center['longitude']
    )
    
    alternatives = find_alternative_centers(user_lat, user_lon, nearest_center)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify({
        "request_info": {
            "city": city,
            "coordinates_source": "google_maps" if coordinates else "fallback",
            "timestamp": current_time
        },
        "nearest_center": {
            "name": nearest_center['name'],
            "region": nearest_center['region'],
            "phone": nearest_center['phone'],
            "hours": nearest_center['hours'],
            "languages": nearest_center['languages'],
            "distance": {
                "straight_line_km": round(distance, 2),
                "driving": travel_info['driving'],
                "public_transit": travel_info['transit']
            }
        },
        "alternative_centers": [
            {
                "name": center['name'],
                "region": center['region'],
                "phone": center['phone'],
                "hours": center['hours'],
                "languages": center['languages'],
                "distance_km": round(haversine_distance(
                    user_lat, user_lon,
                    center['latitude'], center['longitude']
                ), 2)
            } for center in alternatives
        ],
        "emergency_contacts": {
            "national_crisis_line": "09 25250111",
            "emergency_number": "112"
        }
    })

@app.route('/health')
def health_check():
    """Enhanced health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "google_maps_available": gmaps is not None,
        "services": {
            "geocoding": "active",
            "distance_matrix": "active",
            "crisis_centers": len(CRISIS_CENTERS)
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)