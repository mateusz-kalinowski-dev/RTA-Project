import time
import json
import sys
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
import config
from transformers import pipeline
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

model_name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = DistilBertTokenizer.from_pretrained(model_name)
model = DistilBertForSequenceClassification.from_pretrained(model_name)

def create_kafka_consumer():
    """Create a Kafka consumer with retry logic"""
    for i in range(10):  # Retry 10 times
        try:
            consumer = KafkaConsumer(
                config.KAFKA_RAW_DATA_TOPIC,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,   
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                group_id=config.KAFKA_CONSUMER_GROUP
            )
            print(f"Successfully connected to Kafka consumer")
            return consumer
        except Exception as e:
            print(f"Failed to connect to Kafka consumer (attempt {i+1}/10): {e}")
            if i < 9:  # Don't sleep on the last attempt
                time.sleep(5)
    
    # If we get here, we failed to connect after all retries
    raise Exception("Failed to connect to Kafka consumer after multiple retries")

def create_kafka_producer():
    """Create a Kafka producer with retry logic"""
    for i in range(10):  # Retry 10 times
        try:
            producer = KafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            print(f"Successfully connected to Kafka producer")
            return producer
        except Exception as e:
            print(f"Failed to connect to Kafka producer (attempt {i+1}/10): {e}")
            if i < 9:  # Don't sleep on the last attempt
                time.sleep(5)
    
    # If we get here, we failed to connect after all retries
    raise Exception("Failed to connect to Kafka producer after multiple retries")

# Initialize sentiment analysis model with retry logic
def init_sentiment_analyzer(model, tokenizer, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            print("Loading sentiment analysis model...")
            # Use a smaller model for faster processing
            sentiment_analyzer = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
            print("Model loaded successfully!")
            return sentiment_analyzer
        except Exception as e:
            retries += 1
            print(f"Error loading sentiment analysis model (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
    
    print("Failed to load sentiment analysis model after multiple attempts")
    return None

# Function to analyze sentiment
def analyze_sentiment(analyzer, text):
    if not text or len(text) == 0:
        return {
            'label': 'NEUTRAL',
            'score': 0.5
        }
    
    try:    
        # Truncate text to 512 tokens as most models have limits
        result = analyzer(text[:512])
        # Map the model output to POSITIVE/NEGATIVE/NEUTRAL format
        label = result[0]['label'].upper()
        if label not in ["POSITIVE", "NEGATIVE"]:
            label = "NEUTRAL"
        return {
            'label': label,
            'score': float(result[0]['score'])
        }
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return {
            'label': 'NEUTRAL',
            'score': 0.5
        }

def process_messages(consumer, producer, sentiment_analyzer):
    """Process messages from Kafka, analyze sentiment, and produce to output topic"""
    print("Analyzer started. Waiting for messages...")
    
    # Process messages
    for message in consumer:
        try:
            data = message.value
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            print(f"Received message: {data.get('id', 'unknown')}")
            
            # Extract text for sentiment analysis
            type = data.get('type')
            if type == "reddit_post":
                text = data.get('title', 'unknown') + ' ' + data.get('text', 'unknown')
            else:
                text = data.get('text', 'unknown')
            
            # Skip if no text is found
            if not text:
                print(f"No text content found in message: {data.get('id','unknown')}")
                continue
            
            # Perform sentiment analysis
            sentiment_result = analyze_sentiment(sentiment_analyzer, text)
            
            # Prepare analysis result
            analysis_result = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'raw_data': data,
                'sentiment': sentiment_result,
                'analysis_type': 'sentiment'
            }
            
            if type == 'reddit_post':
            # Send to Kafka output topic
                producer.send(config.KAFKA_OUTPUT_TOPIC_POST, analysis_result)
                print(f"Sent analyzed result to Kafka topic: {config.KAFKA_OUTPUT_TOPIC_POST}")
            else:
                producer.send(config.KAFKA_OUTPUT_TOPIC_COMMENTS, analysis_result)
                print(f"Sent analyzed result to Kafka topic: {config.KAFKA_OUTPUT_TOPIC_COMMENTS}")
            
        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == '__main__':
    # Wait for other services to start
    print("Starting sentiment analyzer service...")
    time.sleep(10)

    try:
        # Create Kafka consumer and producer
        consumer = create_kafka_consumer()
        producer = create_kafka_producer()

        # Initialize sentiment analyzer
        sentiment_analyzer = init_sentiment_analyzer(model, tokenizer)
        if sentiment_analyzer is None:
            print("Could not initialize sentiment analyzer. Exiting.")
            sys.exit(1)
        
        print("Starting to process data...")
        
        # Process Kafka messages
        process_messages(consumer, producer, sentiment_analyzer)
        
    except Exception as e:
        print(f"Error in analyzer: {e}")
        print("Exiting...")
        sys.exit(1) 