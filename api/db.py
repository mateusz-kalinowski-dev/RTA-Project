from pymongo import MongoClient
import config

def connect_to_mongodb():
    client = MongoClient(config.MONGODB_URI)
    db = client[config.MONGODB_DB_NAME]
    return db

def get_posts_collection():
    db = connect_to_mongodb()
    posts = db['reddit_posts']
    return posts

def get_comments_collection():
    db = connect_to_mongodb()
    comments = db['reddit_comments']
    return comments