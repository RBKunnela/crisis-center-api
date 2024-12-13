from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import math
import logging

app = Flask(__name__)
CORS(app)

# HTML template for the root endpoint
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
    "national_crisis_line": "09 25250111"
}
    </pre>

    <h2>Emergency Contact</h2>
    <p>National Crisis Helpline: 09 25250111 (24/7)</p>
</body>
</html>
'''

# Your existing crisis centers and city coordinates data here...
CRISIS_CENTERS = [
    {
        "region": "Helsinki",
        "name": "Helsingin kriisikeskus",
        "phone": "09 4135 0510",
        "latitude": 60.1699,
        "longitude": 24.9384
    },
    # ... rest of your centers ...
]

CITY_COORDINATES = {
    "Helsinki": (60.1699, 24.9384),
    # ... rest of your cities ...
}

# Add root endpoint
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Crisis Center API is operational",
        "endpoints": {
            "find_nearest": "/find-nearest?city=<city_name>",
            "health": "/health"
        }
    })

# Your existing haversine_distance function here...

@app.route('/centers', methods=['GET'])
def list_centers():
    """Return a list of all crisis centers."""
    return jsonify({
        "centers": CRISIS_CENTERS,
        "total": len(CRISIS_CENTERS)
    })

@app.route('/centers/search', methods=['GET'])
def search_centers():
    """Search crisis centers by region."""
    region = request.args.get('region', '').capitalize()
    if not region:
        return jsonify({"error": "Region parameter is required"}), 400
        
    matching_centers = [
        center for center in CRISIS_CENTERS 
        if region in center['region']
    ]
    
    return jsonify({
        "centers": matching_centers,
        "count": len(matching_centers)
    })
    
@app.route('/centers/<region>', methods=['GET'])
def center_details(region):
    """Get detailed information about a specific center."""
    center = next(
        (c for c in CRISIS_CENTERS if c['region'].lower() == region.lower()),
        None
    )
    
    if not center:
        return jsonify({"error": "Center not found"}), 404
        
    return jsonify(center)

# Your existing find-nearest endpoint
@app.route('/find-nearest', methods=['GET'])
def find_nearest_center():
    city = request.args.get('city', '')
    if not city:
        return jsonify({
            "error": "City parameter is required"
        }), 400
    
    # Normalize city name
    city = city.capitalize()
    
    # Get city coordinates
    if city in CITY_COORDINATES:
        user_lat, user_lon = CITY_COORDINATES[city]
    else:
        # Default to center of Finland if city not found
        user_lat, user_lon = 62.2426, 25.7475
        
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
        "national_crisis_line": "09 25250111"
    })

# Add a health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "1.0.0"
    })

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Add startup logging
logger.info("Starting Crisis Center API application...")
logger.info("Configuring routes...")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)