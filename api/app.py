from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from flask_cors import CORS
import config
import db

app = Flask(__name__)
CORS(app)

def parse_time_param(param, default=None):
    try:
        return datetime.fromisoformat(param)
    except Exception:
        return default

@app.route("/api/summary", methods=['GET'])
def get_summary():
    from_str = request.args.get('from')
    to_str = request.args.get('to')
    subreddit = request.args.get('subreddit')

    from_time = parse_time_param(from_str, default=datetime.utcnow() - timedelta(days=1))
    to_time = parse_time_param(to_str, default=datetime.utcnow())

    reddit_posts = db.get_posts_collection()
    reddit_comments = db.get_comments_collection()

    post_query = {
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }
    comment_query = {
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }
    if subreddit:
        post_query["raw_data.subreddit"] = subreddit
        comment_query["raw_data.subreddit"] = subreddit

    posts = list(reddit_posts.find(post_query))
    comments = list(reddit_comments.find(comment_query))

    sentiment_counts_for_posts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    sentiment_counts_for_comments = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for doc in posts:
        label = doc.get("sentiment", {}).get("label")
        if label:
            sentiment_counts_for_posts[label] += 1

    for doc in comments:
        label = doc.get("sentiment", {}).get("label")
        if label:
            sentiment_counts_for_comments[label] += 1

    return jsonify({
        "num_posts": len(posts),
        "num_comments": len(comments),
        "sentiment_distribution_by_posts": sentiment_counts_for_posts,
        "sentiment_distribution_by_comments": sentiment_counts_for_comments
    })

@app.route("/api/posts", methods=['GET'])
def get_posts():
    from_str = request.args.get('from')
    to_str = request.args.get('to')
    sentiment_filter = request.args.get('sentiment')
    subreddit = request.args.get('subreddit')

    from_time = parse_time_param(from_str, default=datetime.utcnow() - timedelta(days=1))
    to_time = parse_time_param(to_str, default=datetime.utcnow())

    query = {
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }
    if sentiment_filter:
        query["sentiment.label"] = sentiment_filter.upper()
    if subreddit:
        query["raw_data.subreddit"] = subreddit

    reddit_posts = db.get_posts_collection()
    posts = list(reddit_posts.find(query))
    posts.sort(key=lambda x: x["raw_data"].get("score", 0), reverse=True)

    return jsonify([{
        "id": post["raw_data"]["id"],
        "title": post["raw_data"].get("title"),
        "score": post["raw_data"].get("score"),
        "num_comments": post["raw_data"].get("num_comments"),
        "created_utc": post["raw_data"].get("timestamp"),
        "sentiment": post["sentiment"].get("label"),
        "subreddit": post["raw_data"].get("subreddit")
    } for post in posts])

@app.route("/api/comments", methods=['GET'])
def get_comments():
    from_str = request.args.get('from')
    to_str = request.args.get('to')
    subreddit = request.args.get('subreddit')

    from_time = parse_time_param(from_str, default=datetime.utcnow() - timedelta(days=1))
    to_time = parse_time_param(to_str, default=datetime.utcnow())

    query = {
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }
    if subreddit:
        query["raw_data.subreddit"] = subreddit

    reddit_comments = db.get_comments_collection()
    comments = list(reddit_comments.find(query))

    return jsonify([{
        "created_utc": comment["raw_data"].get("timestamp"),
        "sentiment": comment["sentiment"].get("label"),
        "subreddit": comment["raw_data"].get("subreddit")
    } for comment in comments])

@app.route("/api/posts/<post_id>", methods=['GET'])
def get_post_details(post_id):
    reddit_posts = db.get_posts_collection()
    reddit_comments = db.get_comments_collection()

    post = reddit_posts.find_one({"raw_data.id": post_id})
    comments = list(reddit_comments.find({"raw_data.post_id": post_id}))

    if post and "_id" in post:
        del post["_id"]

    for comment in comments:
        if "_id" in comment:
            del comment["_id"]

    return jsonify({
        "post": post,
        "comments": comments
    })


@app.route("/api/top-posts", methods=['GET'])
def get_top_posts():
    from_str = request.args.get('from')
    to_str = request.args.get('to')
    subreddit = request.args.get('subreddit')

    from_time = parse_time_param(from_str, default=datetime.utcnow() - timedelta(days=1))
    to_time = parse_time_param(to_str, default=datetime.utcnow())

    query = {
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }
    if subreddit:
        query["raw_data.subreddit"] = subreddit

    reddit_posts = db.get_posts_collection()
    cursor = reddit_posts.find(query).sort("raw_data.score", -1)

    seen_ids = set()
    unique_posts = []
    for post in cursor:
        post_id = post.get("raw_data", {}).get("id")
        if post_id and post_id not in seen_ids:
            seen_ids.add(post_id)
            unique_posts.append(post)
        if len(unique_posts) >= 10:
            break

    return jsonify([{
        "id": post["raw_data"].get("id"),
        "title": post["raw_data"].get("title"),
        "score": post["raw_data"].get("score"),
        "sentiment": post["sentiment"].get("label"),
        "subreddit": post["raw_data"].get("subreddit")
    } for post in unique_posts])


@app.route("/api/subreddits", methods=['GET'])
def get_subreddits():
    reddit_posts = db.get_posts_collection()
    subreddits = reddit_posts.distinct("raw_data.subreddit")
    return jsonify(sorted(subreddits))

if __name__ == "__main__":
    print(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=True
    )
