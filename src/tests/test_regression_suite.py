import os
import pytest
from pymongo import MongoClient
from lambda_function import lambda_handler
import json

EVENTS = [
    "01_register_a_bird.json",
    "02_log_food_update.json",
    "03_log_weight_update.json",
    "04_query_missing_fields.json",
    "05_query_all_birds.json"
]

def load_event(filename):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with open(full_path) as f:
        return json.load(f)

@pytest.fixture(scope="module")
def mongo_client():
    client = MongoClient(os.environ["MONGODB_URI"])
    yield client
    client.close()

def test_regression_scenarios(mongo_client):
    db = mongo_client["hawklogger"]
    birds = db["birds"]
    logs = db["bird_logs"]
    birds.delete_many({"name": {"$regex": "^test_"}})
    logs.delete_many({"log.birdName": {"$regex": "^test_"}})

    for event_file in EVENTS:
        print(f"\n--- Running {event_file} ---")
        event = load_event(event_file)
        response = lambda_handler(event, {})
        assert "response" in response
        assert "outputSpeech" in response["response"]
        assert "text" in response["response"]["outputSpeech"]
        print("Response:", response["response"]["outputSpeech"]["text"])
