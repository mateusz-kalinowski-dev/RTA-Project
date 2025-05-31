import time
import praw
import json
from datetime import datetime, timedelta, timezone
from kafka import KafkaProducer
import logging
from airflow.sdk import Variable
from utils import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_RAW_DATA_TOPIC,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    SUBREDDITS_TO_MONITOR
)

logging.basicConfig(
    level=logging.INFO
)

logger = logging.getLogger(__name__ if __name__ != "__main__" else "scrapp_data_from_reddit")

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

def get_last_timestamps():
    """Get last processed POST timestamps from Airflow Variables (ignoring comments)"""
    default_ts = datetime.utcnow() - timedelta(hours=24)
    timestamps = {}
    try:
        timestamps_json = Variable.get("last_reddit_post_timestamps", default="{}")  
        saved_timestamps = json.loads(timestamps_json)
        
        for subreddit in SUBREDDITS_TO_MONITOR:
            ts = saved_timestamps.get(subreddit)
            if ts:
                try:
                    timestamps[subreddit] = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
                except (ValueError, TypeError):
                    timestamps[subreddit] = default_ts
            else:
                timestamps[subreddit] = default_ts
                
    except Exception as e:
        logger.error(f"Error loading timestamps, using defaults: {e}")
        timestamps = {subreddit: default_ts for subreddit in SUBREDDITS_TO_MONITOR}
    
    return timestamps

def save_last_timestamps(timestamps_dict):
    """Save only POST timestamps to Airflow Variables"""
    try:
        timestamps_to_save = {
            subreddit: ts.isoformat()
            for subreddit, ts in timestamps_dict.items()
        }
        Variable.set("last_reddit_post_timestamps", json.dumps(timestamps_to_save))
    except Exception as e:
        logger.error(f"Failed to save timestamps: {e}")
        raise

def init_reddit_client():
    """Initialize the Reddit API client"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError("Reddit API credentials required.")
    
    logger.info(f"Initializing Reddit client for subreddits: {', '.join(SUBREDDITS_TO_MONITOR)}")
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

def process_post(post):
    """Convert post to a structured dictionary"""
    return {
        "id": f"reddit_post_{post.id}",
        "type": "reddit_post",
        "subreddit": post.subreddit.display_name,
        "title": post.title,
        "text": post.selftext,
        "url": post.url,
        "author": str(post.author),
        "score": post.score,
        "upvote_ratio": post.upvote_ratio,
        "num_comments": post.num_comments,
        "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def process_comment(comment, post_id=None, post_title=None):
    """Convert comment to a structured dictionary"""
    return {
        "id": f"reddit_comment_{comment.id}",
        "type": "reddit_comment",
        "post_id": f"reddit_post_{post_id}",
        "post_title": post_title,
        "subreddit": comment.subreddit.display_name,
        "text": comment.body,
        "author": str(comment.author),
        "score": comment.score,
        "created_utc": datetime.fromtimestamp(comment.created_utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def send_to_kafka(producer, data):
    """Send data to Kafka topic"""
    producer.send(KAFKA_RAW_DATA_TOPIC, data)

def fetch_new_posts(reddit_client, subreddit_name, last_timestamp):
    """Fetch only new posts since last timestamp"""
    if not isinstance(last_timestamp, datetime):
        last_timestamp = datetime.utcnow() - timedelta(hours=24)
        logger.warning(f"Invalid timestamp for r/{subreddit_name}, using default")
    
    logger.info(f"Fetching posts from r/{subreddit_name} since {last_timestamp}")
    
    subreddit = reddit_client.subreddit(subreddit_name)
    new_posts = []
    
    try:
        for post in subreddit.new(limit=None):
            post_time = datetime.fromtimestamp(post.created_utc)
            if post_time > last_timestamp:
                new_posts.append(post)
            else:
                break  
        
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        
    logger.info(f"Found {len(new_posts)} new posts in r/{subreddit_name}")
    return new_posts

def fetch_comments(post):
    """Fetch comments for a post"""
    try:
        post.comments.replace_more(limit=5)
        all_comments = list(post.comments.list())
        logger.info(f"Fetching {len(all_comments)} comments for post: {post.id} - {post.title[:30]}...")
        return all_comments
    except Exception as e:
        logger.error(f"Error fetching comments for post {post.id}: {e}")
        return []

def collect_reddit_data():
    """Main function with improved post tracking"""
    try:
        producer = create_kafka_producer()
        reddit_client = init_reddit_client()
        last_timestamps = get_last_timestamps()
        updated_timestamps = {}
        
        for subreddit_name in SUBREDDITS_TO_MONITOR:
            subreddit_last = last_timestamps[subreddit_name]
            new_posts = fetch_new_posts(reddit_client, subreddit_name, subreddit_last)
            
            if new_posts:
                newest_post_time = datetime.fromtimestamp(new_posts[0].created_utc)
                updated_timestamps[subreddit_name] = newest_post_time
                
                for post in new_posts:
                    post_data = process_post(post)
                    send_to_kafka(producer, post_data)
                    
                    comments = fetch_comments(post)
                    for comment in comments:
                        comment_data = process_comment(comment, post.id, post.title)
                        send_to_kafka(producer, comment_data)
                    
                    time.sleep(1)
            else:
                updated_timestamps[subreddit_name] = subreddit_last

        save_last_timestamps(updated_timestamps)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        producer.flush()
        producer.close()