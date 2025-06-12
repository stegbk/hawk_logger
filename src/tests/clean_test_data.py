import os
from pymongo import MongoClient

client = MongoClient(os.environ["MONGODB_URI"])
db = client["hawklogger"]
bird_registry = db["birds"]
collection = db["bird_logs"]

deleted_birds = bird_registry.delete_many({"name": {"$regex": "^test_"}})
deleted_logs = collection.delete_many({"log.birdName": {"$regex": "^test_"}})

print(f"Deleted {deleted_birds.deleted_count} test birds and {deleted_logs.deleted_count} test logs.")
