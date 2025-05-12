
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import db
import config

app = Flask(__name__)
CORS(app)

@app.route('api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})


@app.route('/api/data', methods=['GET'])
def get_results():
    """Endpoint to get the latest analyzed data"""
    # Get query parameters
    limit = request.args.get('limit', default=100, type=int)
    data_type = request.args.get('type')
    subreddit = request.args.get('subreddit')
    
    # Get results from MongoDB
    results = db.get_recent_results(limit, data_type, subreddit)
    
    return jsonify(results)

if __name__ == '__main__':
    print(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    
    # Start Flask app
    app.run(
        host=config.API_HOST, 
        port=config.API_PORT, 
        debug=config.DEBUG
    ) 