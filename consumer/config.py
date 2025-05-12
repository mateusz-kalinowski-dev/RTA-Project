import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB settings
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_OUTPUT_TOPIC = 'analyzed_data'
KAFKA_CONSUMER_GROUP = 'data_from_reddit' 