import os
import json
import openai
import pymongo
from datetime import datetime
from pytz import timezone

# MongoDB Atlas connection
mongo_client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = mongo_client["hawklogger"]
collection = db["bird_logs"]

openai.api_key = os.environ["OPENAI_API_KEY"]

def lambda_handler(event, context):
    intent = event.get("request", {}).get("intent", {})
    slots = intent.get("slots", {})

    sentence = slots.get("sentence", {}).get("value", "")
    bird_name = slots.get("birdName", {}).get("value", "Unknown")
    session_id = event.get("session", {}).get("sessionId", "default")

    session_key = f"{session_id}::{bird_name}"

    existing = collection.find_one({"sessionKey": session_key})
    if existing:
        log = existing.get("log", {})
    else:
        log = {
            "timestamp": datetime.now(timezone("US/Pacific")).isoformat(),
            "birdName": bird_name,
            "weight": None,
            "food": None,
            "attitude": None,
            "performance": None,
            "notes": "",
            "enrichment": None
        }

    updated_log = update_log_with_chatgpt(log, sentence)

    collection.update_one(
        {"sessionKey": session_key},
        {
            "$set": {
                "log": updated_log,
                "updatedAt": datetime.now(timezone("US/Pacific")).isoformat()
            }
        },
        upsert=True
    )

    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": f"Logged update for {bird_name}."
            },
            "shouldEndSession": False
        }
    }

def update_log_with_chatgpt(log, user_input):
    prompt = f"""
Given the following JSON log:
{json.dumps(log, indent=2)}

Update the log based on this user sentence:
"{user_input}"

Return only the updated JSON.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0.2,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that updates hawk feeding logs."},
            {"role": "user", "content": prompt}
        ]
    )

    try:
        return json.loads(response['choices'][0]['message']['content'])
    except Exception as e:
        print("GPT parse failed:", e)
        return log
