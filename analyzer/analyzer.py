import time
import json
import sys
from datetime import datetime, timezone
from kafka import KafkaConsumer, KafkaProducer
from transformers import pipeline
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import logging
from utils import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    KAFKA_RAW_DATA_TOPIC,
    OUTPUT_TOPIC_POST,
    OUTPUT_TOPIC_COMMENTS
)

logging.basicConfig(
    level=logging.INFO
)
logger = logging.getLogger(__name__ if __name__ != "__main__" else "analyzer")

model_name = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = DistilBertTokenizer.from_pretrained(model_name)
model = DistilBertForSequenceClassification.from_pretrained(model_name)

def create_kafka_consumer():
    """Create a Kafka consumer with retry logic"""
    for i in range(10):
        try:
            consumer = KafkaConsumer(
                KAFKA_RAW_DATA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,   
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                group_id=KAFKA_CONSUMER_GROUP,
                consumer_timeout_ms=30000
            )
            logger.info(f"Successfully connected to Kafka consumer")
            return consumer
        except Exception as e:
            logger.error(f"Failed to connect to Kafka consumer (attempt {i+1}/10): {e}")
            if i < 9:  
                time.sleep(5)
    
    raise Exception("Failed to connect to Kafka consumer after multiple retries")

def create_kafka_producer():
    """Create a Kafka producer with retry logic"""
    for i in range(10): 
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            logger.info(f"Successfully connected to Kafka producer")
            return producer
        except Exception as e:
            logger.error(f"Failed to connect to Kafka producer (attempt {i+1}/10): {e}")
            if i < 9:  
                time.sleep(5)
    
    raise Exception("Failed to connect to Kafka producer after multiple retries")

def init_sentiment_analyzer(model, tokenizer, max_retries=3):
    """Initialize the sentiment analysis model with retry logic"""
    retries = 0
    while retries < max_retries:
        try:
            logger.info("Loading sentiment analysis model...")
            sentiment_analyzer = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
            logger.info("Model loaded successfully!")
            return sentiment_analyzer
        except Exception as e:
            retries += 1
            logger.error(f"Error loading sentiment analysis model (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                logger.info(f"Retrying in 5 seconds...")
                time.sleep(5)
    
    logger.error("Failed to load sentiment analysis model after multiple attempts")
    return None

def analyze_sentiment(analyzer, text):
    """Analyze sentiment of the given text using the provided analyzer"""
    if not text or len(text) == 0:
        return {
            'label': 'NEUTRAL',
            'score': 0.5
        }
    
    try:    
        result = analyzer(text[:512])
        label = result[0]['label'].upper()
        if label not in ["POSITIVE", "NEGATIVE"]:
            label = "NEUTRAL"
        return {
            'label': label,
            'score': float(result[0]['score'])
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {
            'label': 'NEUTRAL',
            'score': 0.5
        }

def process_messages(sentiment_analyzer):
    """Process messages from Kafka, analyze sentiment, and produce to output topic"""

    try:
        consumer = create_kafka_consumer()
        producer = create_kafka_producer()
        count_messages = 0
        logger.info("Analyzer started. Waiting for messages...")

        for message in consumer:
            data = message.value
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now(timezone.utc).isoformat()

            type = data.get('type')
            if type == "reddit_post":
                text = data.get('title', 'unknown') + ' ' + data.get('text', 'unknown')
            else:
                text = data.get('text', 'unknown')
            if not text:
                continue
            
            sentiment_result = analyze_sentiment(sentiment_analyzer, text)
            analysis_result = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'raw_data': data,
                'sentiment': sentiment_result,
                'analysis_type': 'sentiment'
            }
            
            if type == 'reddit_post':
                producer.send(OUTPUT_TOPIC_POST, analysis_result)
            else:
                producer.send(OUTPUT_TOPIC_COMMENTS, analysis_result)

            count_messages += 1
            if count_messages % 100 == 0:
                logger.info(f"Processed {count_messages} messages so far")
                
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise
    finally:
        producer.flush()
        producer.close()
        consumer.commit()
        consumer.close()
    logger.info(f"Finished processing {count_messages}. Exiting...")
    sys.exit(0)

if __name__ == '__main__':

    logger.info("Starting sentiment analyzer service...")
    
    sentiment_analyzer = init_sentiment_analyzer(model, tokenizer)
    if sentiment_analyzer is None:
        logger.error("Could not initialize sentiment analyzer")
        raise RuntimeError("Sentiment analyzer initialization failed")
        
    logger.info("Service initialized. Starting to process data...")
    process_messages(sentiment_analyzer)