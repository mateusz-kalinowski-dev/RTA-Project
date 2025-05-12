import time
import praw
import json
from datetime import datetime, timedelta, timezone
from kafka import KafkaProducer
import config

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

# Track last processed time for each subreddit
last_processed_timestamps = {}
for subreddit in config.SUBREDDITS_TO_MONITOR:
    last_processed_timestamps[subreddit] = datetime.utcnow() - timedelta(hours=24)

def init_reddit_client():
    """Initialize the Reddit API client"""
    if not config.REDDIT_CLIENT_ID or not config.REDDIT_CLIENT_SECRET:
        raise ValueError("Reddit API credentials required. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.")
    
    print(f"Initializing Reddit client for subreddits: {', '.join(config.SUBREDDITS_TO_MONITOR)}")
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT
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

def send_to_kafka(data):
    """Send data to Kafka topic"""
    producer.send(config.KAFKA_RAW_DATA_TOPIC, data)
    print(f"Sent to Kafka: {data['id']}")

def fetch_new_posts(reddit_client, subreddit_name):
    """Fetch new posts from a subreddit"""
    print(f"Fetching new posts from r/{subreddit_name}")
    
    subreddit = reddit_client.subreddit(subreddit_name)
    last_timestamp = last_processed_timestamps[subreddit_name]
    
    # Get new posts
    new_posts = []
    for post in subreddit.new(limit=20):  # Keep limit small to avoid rate limiting
        post_datetime = datetime.fromtimestamp(post.created_utc)
        if post_datetime > last_timestamp:
            new_posts.append(post)
            # Update the last processed timestamp if this post is newer
            if post_datetime > last_processed_timestamps[subreddit_name]:
                last_processed_timestamps[subreddit_name] = post_datetime
    
    print(f"Found {len(new_posts)} new posts in r/{subreddit_name}")
    return new_posts

def fetch_comments(post):
    """Fetch comments for a post"""
    print(f"Fetching comments for post: {post.id} - {post.title[:30]}...")
    
    # Load top-level comments with limited depth
    post.comments.replace_more(limit=5)
    all_comments = list(post.comments.list())
    
    print(f"Found {len(all_comments)} comments for post {post.id}")
    return all_comments

def collect_reddit_data():
    """Main function to collect Reddit data"""
    try:
        reddit_client = init_reddit_client()
        
        # Process each subreddit
        for subreddit_name in config.SUBREDDITS_TO_MONITOR:
            # Get new posts
            new_posts = fetch_new_posts(reddit_client, subreddit_name)
            
            for post in new_posts:
                # Process and send post data to Kafka
                post_data = process_post(post)
                send_to_kafka(post_data)
                
                # Get comments for this post
                comments = fetch_comments(post)
                
                # Process and send each comment to Kafka
                for comment in comments:
                    comment_data = process_comment(
                        comment, 
                        post_id=post.id,
                        post_title=post.title
                    )
                    send_to_kafka(comment_data)
                
                # Avoid hitting Reddit API rate limits
                time.sleep(1)
            
    except Exception as e:
        print(f"Error collecting Reddit data: {e}")

if __name__ == "__main__":

    producer = create_kafka_producer()
    # Run indefinitely
    while True:
        print(f"Starting Reddit data collection at {datetime.now().isoformat()}")
        collect_reddit_data()
        print(f"Completed collection cycle, waiting 60 seconds before next cycle")
        time.sleep(60)  # Collect every minute 