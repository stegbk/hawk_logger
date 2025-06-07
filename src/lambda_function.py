import os
import json
import pymongo
from datetime import datetime
from pytz import timezone
from openai import OpenAI

# MongoDB Atlas connection
mongo_client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = mongo_client["hawklogger"]
collection = db["bird_logs"]

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def lambda_handler(event, context):
    intent = event.get("request", {}).get("intent", {})
    slots = intent.get("slots", {})
    sentence = slots.get("utterance", {}).get("value", "")

    # Parse birdName early using a temporary GPT call
    bird_name = extract_bird_name(sentence) or "Unknown"
    today = datetime.now(timezone("US/Pacific")).strftime("%Y-%m-%d")
    log_key = {"birdName": bird_name, "date": today}

    existing = collection.find_one(log_key)
    if existing:
        log = existing.get("log", {})
    else:
        log = {
            "timestamp": datetime.now(timezone("US/Pacific")).isoformat(),
            "date": today,
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
        log_key,
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
                "text": f"Logged update for {updated_log.get('birdName', 'your bird')}"
            },
            "shouldEndSession": False
        }
    }

def update_log_with_chatgpt(log, user_input):
    prompt = f"""
Given the following JSON log:
{json.dumps(log, indent=2)}

Update the log based on this sentence:
"{user_input}"

If the bird's name is mentioned, update 'birdName'.
If food is mentioned in grams, update 'food'.
If weight is mentioned in grams, update 'weight'.
If there's behavior or attitude, update 'attitude' or 'notes'.

Return only the updated JSON.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that updates hawk feeding logs."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("GPT parse failed:", e)
        return log

def extract_bird_name(sentence):
    prompt = f"""
Extract the bird's name from this sentence:
"{sentence}"

Return only the name as a JSON string, or null if not found.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract bird names from natural speech."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        name = json.loads(response.choices[0].message.content)
        return name if isinstance(name, str) else None
    except Exception as e:
        print("Name extraction failed:", e)
        return None
