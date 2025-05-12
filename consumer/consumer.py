import json
import time
from datetime import datetime, timezone
from kafka import KafkaConsumer
from pymongo import MongoClient
import config

def connect_to_mongodb():
    """Connect to MongoDB"""
    client = MongoClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    return db.analyzed_data

def create_kafka_consumer():
    """Create a Kafka consumer with retry logic"""
    for i in range(10):  # Retry 10 times
        try:
            consumer = KafkaConsumer(
                config.KAFKA_OUTPUT_TOPIC,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                group_id=config.KAFKA_CONSUMER_GROUP
            )
            print(f"Successfully connected to Kafka")
            return consumer
        except Exception as e:
            print(f"Failed to connect to Kafka (attempt {i+1}/10): {e}")
            if i < 9:  
                time.sleep(5)
    
    raise Exception("Failed to connect to Kafka after multiple retries")

def process_messages():
    """Process messages from Kafka and store in MongoDB"""
    # Connect to MongoDB
    collection = connect_to_mongodb()
    
    # Create Kafka consumer
    consumer = create_kafka_consumer()
    
    print("Consumer started. Waiting for messages...")
    
    # Process messages
    for message in consumer:
        try:
            data = message.value
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            print(f"Received message: {data.get('raw_data', {}).get('id', 'unknown')}")

            
            # Store in MongoDB
            collection.insert_one(data)
            print(f"Saved to MongoDB: {data.get('raw_data', {}).get('id', 'unknown')}")
            
        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == "__main__":
    while True:
        try:
            process_messages()
        except Exception as e:
            print(f"Error in consumer: {e}")
            print("Reconnecting in 10 seconds...")
            time.sleep(10) 