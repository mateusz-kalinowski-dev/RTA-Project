
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
    from_time = parse_time_param(from_str, default=datetime.utcnow() - timedelta(days=1))
    to_time = parse_time_param(to_str, default=datetime.utcnow())

    reddit_posts = db.get_posts_collection()
    reddit_comments = db.get_comments_collection()

    posts = list(reddit_posts.find({
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }))
    comments = list(reddit_comments.find({
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }))

    sentiment_counts_for_posts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    sentiment_counts_for_comments = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for doc in posts:
        label = doc.get("sentiment", {}).get("label")
        sentiment_counts_for_posts[label] += 1

    for doc in comments:
        label = doc.get("sentiment", {}).get("label")
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
    from_time = parse_time_param(from_str, default=datetime.utcnow() - timedelta(days=1))
    to_time = parse_time_param(to_str, default=datetime.utcnow())

    query = {
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }
    if sentiment_filter:
        query["sentiment.label"] = sentiment_filter.upper()

    reddit_posts = db.get_posts_collection()
    posts = list(reddit_posts.find(query))
    posts.sort(key=lambda x: x["raw_data"].get("score", 0), reverse=True)

    return jsonify([{
        "id": post["raw_data"]["id"],
        "title": post["raw_data"].get("title"),
        "score": post["raw_data"].get("score"),
        "num_comments": post["raw_data"].get("num_comments"),
        "created_utc": post["raw_data"].get("timestamp"),
        "sentiment": post["sentiment"].get("label")
    } for post in posts])

@app.route("/api/posts/<post_id>", methods=['GET'])
def get_post_details(post_id):
    reddit_posts = db.get_posts_collection()
    reddit_comments = db.get_comments_collection()

    post = reddit_posts.find_one({"raw_data.id": post_id})
    comments = list(reddit_comments.find({"raw_data.post_id": post_id}))
    # do rozwinięcia jeszcze co to ma robić
    return jsonify({
        "post": post,
        "comments": comments
    })


@app.route("/api/top-posts", methods=['GET'])
def get_top_posts():
    from_str = request.args.get('from')
    to_str = request.args.get('to')
    from_time = parse_time_param(from_str, default=datetime.utcnow() - timedelta(days=1))
    to_time = parse_time_param(to_str, default=datetime.utcnow())
    reddit_posts = db.get_posts_collection()

    posts = list(reddit_posts.find({
        "raw_data.created_utc": {"$gte": from_time.isoformat(), "$lte": to_time.isoformat()}
    }).sort("raw_data.score", -1).limit(10))

    return jsonify([{
        "title": post["raw_data"].get("title"),
        "score": post["raw_data"].get("score"),
        "sentiment": post["sentiment"].get("label")
    } for post in posts])

if __name__ == "__main__":
    print(f"Starting API server on {config.API_HOST}:{config.API_PORT}")
    app.run(
        host=config.API_HOST,
        port = config.API_PORT,
        debug=True
    )