import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_RAW_DATA_TOPIC = 'raw_data_from_reddit'

# Reddit API settings
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
SUBREDDITS_TO_MONITOR = os.getenv('SUBREDDITS_TO_MONITOR').split(',')

