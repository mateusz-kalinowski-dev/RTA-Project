import json
import time
from datetime import datetime, timezone
from kafka import KafkaConsumer
from pymongo import MongoClient
import logging
from utils import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    OUTPUT_TOPIC_POST,
    OUTPUT_TOPIC_COMMENTS,
    MONGODB_URI,
    MONGODB_DB_NAME
)

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(__name__ if __name__ != "__main__" else "consumer_mongo")
def connect_to_mongodb():
    """Connect to MongoDB"""
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    return db

def create_kafka_consumer():
    """Create a Kafka consumer with retry logic"""
    for i in range(10):  
        try:
            consumer = KafkaConsumer(
                OUTPUT_TOPIC_POST,
                OUTPUT_TOPIC_COMMENTS,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                group_id=KAFKA_CONSUMER_GROUP,
                consumer_timeout_ms=30000 
            )
            logger.info(f"Successfully connected to Kafka")
            return consumer
        except Exception as e:
            logger.error(f"Failed to connect to Kafka (attempt {i+1}/10): {e}")
            if i < 9: 
                time.sleep(5)
    
    raise Exception("Failed to connect to Kafka after multiple retries")

def process_messages():
    """Process messages with simplified logging"""
    try:
        db = connect_to_mongodb()
        posts_collection = db['analyzed_posts']
        comments_collection = db['analyzed_comments']
        consumer = create_kafka_consumer()
        
        message_count = 0
        
        logger.info("Starting consumer...")

        for message in consumer:
            data = message.value
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now(timezone.utc).isoformat()

            if message.topic == OUTPUT_TOPIC_POST:
                posts_collection.insert_one(data)
            else:
                comments_collection.insert_one(data)

            message_count += 1
            if message_count % 100 == 0:
                logger.info(f"Processed {message_count} messages so far")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise
    finally:
       consumer.commit()
       consumer.close()
    logger.info(f"Finished processing {message_count} messages")

