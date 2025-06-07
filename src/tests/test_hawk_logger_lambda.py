
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from lambda_function import lambda_handler
from pymongo import MongoClient
from datetime import datetime
import pathlib

@pytest.fixture(scope="module")
def mongo_client():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(uri)
    yield client
    client.close()

def load_event(filename):
    base_dir = pathlib.Path(__file__).parent
    path = base_dir / filename
    with open(path, 'r') as f:
        return json.load(f)

def test_hawk_logger_end_to_end(mongo_client):
    db = mongo_client["hawklogger"]
    birds = db["birds"]
    logs = db["bird_logs"]

    birds.delete_many({})
    logs.delete_many({})

    # Register a bird
    response = lambda_handler(load_event("01_register_a_bird.json"), {})
    assert "Added" in response["response"]["outputSpeech"]["text"]

    # Log food
    response = lambda_handler(load_event("02_log_food_update.json"), {})
    assert "Logged update" in response["response"]["outputSpeech"]["text"]

    # Log weight
    response = lambda_handler(load_event("03_log_weight_update.json"), {})
    assert "Logged update" in response["response"]["outputSpeech"]["text"]

    # Query missing fields
    response = lambda_handler(load_event("04_query_missing_fields.json"), {})
    assert "missing" in response["response"]["outputSpeech"]["text"]

    # Get all birds
    response = lambda_handler(load_event("05_query_all_birds.json"), {})
    assert "registered birds" in response["response"]["outputSpeech"]["text"]

    # Soft delete the bird
    response = lambda_handler(load_event("06_delete_bird.json"), {})
    assert "Marked" in response["response"]["outputSpeech"]["text"]

    # Attempt update after delete
    response = lambda_handler(load_event("07_update_deleted_bird.json"), {})
    assert "not recognized" in response["response"]["outputSpeech"]["text"]

    # Attempt unregistered bird update
    response = lambda_handler(load_event("08_update_unregistered_bird.json"), {})
    assert "not recognized" in response["response"]["outputSpeech"]["text"]
