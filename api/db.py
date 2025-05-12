from pymongo import MongoClient
import config

# Create MongoDB client
client = MongoClient(config.MONGODB_URI)
db = client[config.MONGODB_DB_NAME]

# collections
analyzed_data = db.analyzed_data

# Create indexes
analyzed_data.create_index("timestamp")

def get_recent_results(limit=100, data_type=None, subreddit=None):
    """
    Get recent analysis results from MongoDB with optional filtering
    """
    # Build query
    query = {}
    if data_type:
        query['raw_data.type'] = data_type
    if subreddit:
        query['raw_data.subreddit'] = subreddit
        
    # Get data from MongoDB
    return list(analyzed_data.find(
        query,
        {'_id': 0}
    ).sort('timestamp', -1).limit(limit))
    
#def insert_raw_data(data):
 #   """
   # Insert raw data into MongoDB
   # """
   # return raw_data.insert_one(data) 