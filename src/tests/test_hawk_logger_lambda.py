
import os
import json
import pytest
from lambda_function import lambda_handler
from pymongo import MongoClient

def load_event(filename):
    event_path = os.path.join(os.path.dirname(__file__), filename)
    with open(event_path) as f:
        return json.load(f)

@pytest.fixture(scope="module")
def mongo_client():
    client = MongoClient(os.environ["MONGODB_URI"])
    yield client
    client.close()

def dump_collections(db, label):
    print(f"\n--- {label}: birds ---")
    for doc in db["birds"].find({}, {"_id": 0}):
        print(json.dumps(doc, indent=2))

    print(f"\n--- {label}: bird_logs ---")
    for doc in db["bird_logs"].find({}, {"_id": 0}):
        print(json.dumps(doc, indent=2))

def test_hawk_logger_end_to_end(mongo_client):
    db = mongo_client["hawklogger"]
    birds = db["birds"]
    logs = db["bird_logs"]

    # Clean only test-prefixed birds and logs
    birds.delete_many({"name": {"$regex": "^test_"}})
    logs.delete_many({"log.birdName": {"$regex": "^test_"}})

    dump_collections(db, "BEFORE")

    # Register test bird
    response = lambda_handler(load_event("01_register_a_bird.json"), {})
    assert "Added" in response["response"]["outputSpeech"]["text"]

    # Update food
    response = lambda_handler(load_event("02_log_food_update.json"), {})
    assert "Logged update" in response["response"]["outputSpeech"]["text"]

    # Update weight
    response = lambda_handler(load_event("03_log_weight_update.json"), {})
    assert "Logged update" in response["response"]["outputSpeech"]["text"]

    # Query missing fields
    response = lambda_handler(load_event("04_query_missing_fields.json"), {})
    assert "missing" in response["response"]["outputSpeech"]["text"]

    # Query all birds
    response = lambda_handler(load_event("05_query_all_birds.json"), {})
    assert "registered birds" in response["response"]["outputSpeech"]["text"]

    dump_collections(db, "AFTER")
    