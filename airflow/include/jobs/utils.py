import os

# Kafka settings
ZOOKEEPER_CLIENT_PORT= os.getenv('ZOOKEEPER_CLIENT_PORT')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_CONSUMER_GROUP = 'data_from_reddit'
KAFKA_RAW_DATA_TOPIC = 'raw_data_from_reddit' 
OUTPUT_TOPIC_POST = 'analyzed_posts'
OUTPUT_TOPIC_COMMENTS = 'analyzed_comments'

# MongoDB settings
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME') 

# Reddit API settings
REDDIT_CLIENT_ID= os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET= os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT= os.getenv('REDDIT_USER_AGENT')
SUBREDDITS_TO_MONITOR= os.getenv('SUBREDDITS_TO_MONITOR').split(',')