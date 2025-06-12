import os
import json
import pymongo
from datetime import datetime
from pytz import timezone # type: ignore
from openai import OpenAI # Import the OpenAI client

# MongoDB Atlas connection
mongo_client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = mongo_client["hawklogger"]
collection = db["bird_logs"]
bird_registry = db["birds"]
 
# Initialize the OpenAI client
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def lambda_handler(event, context):
    print("[RAW EVENT]", json.dumps(event, indent=2))
    intent = event.get("request", {}).get("intent", {})
    slots = intent.get("slots", {})
    sentence = slots.get("utterance", {}).get("value", "")
    print("[SLOT UTTERANCE]", event.get("request", {}).get("intent", {}).get("slots", {}).get("utterance", {}).get("value"))

    now = datetime.now(timezone("US/Pacific"))
    user_id = event.get("session", {}).get("user", {}).get("userId", "unknown")

    print("[PROMPT]", sentence)

    if "add a" in sentence.lower() and "named" in sentence.lower():
        new_bird = extract_bird_record(sentence)
        print("[CHATGPT RESPONSE - NEW BIRD]", new_bird)
        if new_bird and "name" in new_bird and "species" in new_bird:
            new_bird["addedAt"] = now.isoformat()
            new_bird["addedBy"] = user_id
            new_bird["deleted"] = False
            bird_registry.update_one(
                {"name": new_bird["name"], "deleted": {"$ne": True}},
                {"$set": new_bird},
                upsert=True
            )
            return speak(f"Added {new_bird['species']} named {new_bird['name']} to the registry.")
        else:
            return speak("Sorry, I couldn't extract a bird name and species.")

    if "delete bird" in sentence.lower():
        bird_name = extract_bird_name(sentence)
        print("[CHATGPT RESPONSE - DELETE]", bird_name)
        if bird_name:
            bird_registry.update_one({"name": bird_name}, {"$set": {"deleted": True}})
            return speak(f"Marked {bird_name} as deleted.")
        else:
            return speak("Sorry, I couldn't identify which bird to delete.")

    if "log of all birds" in sentence.lower():
        birds = bird_registry.find({"deleted": {"$ne": True}}, {"_id": 0})
        bird_list = [
            f"{b['name']} the {b['species']} (added on {b['addedAt'].split('T')[0]} by {b.get('addedBy', 'unknown')})"
            for b in birds if "name" in b and "species" in b and "addedAt" in b
        ]
        return speak("Here are the registered birds: " + "; ".join(bird_list)) if bird_list else speak("There are no birds registered yet.")

    bird_name = extract_bird_name(sentence)
    print("[CHATGPT RESPONSE - NAME EXTRACTION]", bird_name)
    if not bird_name:
        return speak("Sorry, I couldn't identify the bird's name. Please try again.")

    if not bird_registry.find_one({"name": bird_name, "deleted": {"$ne": True}}):
        return speak(f"The bird name {bird_name} is not recognized. Please add it first.")

    date_str = extract_date(sentence) or now.strftime("%Y-%m-%d")

    log_key = {"birdName": bird_name, "date": date_str}
    existing = collection.find_one(log_key)
    log = existing.get("log", {}) if existing else {
        "timestamp": now.isoformat(),
        "date": date_str,
        "birdName": bird_name,
        "weight": None,
        "food": None,
        "attitude": None,
        "performance": None,
        "notes": "",
        "enrichment": None
    }

    if "what information is still needed" in sentence.lower():
        missing_fields = [key for key, value in log.items() if key not in ("timestamp", "date", "birdName") and (value is None or value == "")]
        missing_text = ", ".join(missing_fields) if missing_fields else "nothing"
        return speak(f"The log for {bird_name} on {date_str} is missing: {missing_text}.")

    # `log` here is the existing or newly initialized log for the day
    gpt_suggested_updates = update_log_with_chatgpt(log, sentence)
    print("[CHATGPT RESPONSE - LOG UPDATE]", gpt_suggested_updates)

    # Start with the log state we based the GPT call on (or the default new log)
    final_log_for_db = log.copy() # Make a copy to modify
    if isinstance(gpt_suggested_updates, dict):
        final_log_for_db.update(gpt_suggested_updates) # Apply GPT's suggested changes

    # Ensure critical fields are set correctly, overriding any GPT suggestions for these
    final_log_for_db["birdName"] = bird_name
    final_log_for_db["date"] = date_str
    final_log_for_db["timestamp"] = now.isoformat() # Update to current interaction time

    collection.update_one(
        log_key,
        {
            "$set": {
                "log": final_log_for_db, # Save the merged log
                "updatedAt": now.isoformat()
            }
        },
        upsert=True
    )

    return speak(f"Logged update for {final_log_for_db.get('birdName', 'your bird')}")

def speak(text):
    print("[RESPONSE]", text)
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text
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
    print("[PROMPT TO GPT]", prompt)
    response = openai_client.chat.completions.create( # Use the initialized client
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
        print("[PROMPT TO GPT - NAME EXTRACTION]", prompt)
        response = openai_client.chat.completions.create( # Use the initialized client
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract bird names from natural speech."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        result = json.loads(response.choices[0].message.content)
        if result:
            return result

        # fallback: try matching any known name from the registry
        names = bird_registry.distinct("name", {"deleted": {"$ne": True}})
        for name in names:
            if name.lower() in sentence.lower():
                print(f"[FALLBACK NAME MATCH] Found '{name}' in sentence.")
                return name

    except Exception as e:
        print("Name extraction failed:", e)
    return None

def extract_date(sentence):
    prompt = f"""
Extract the date from this sentence in YYYY-MM-DD format.
If no date is mentioned, return null.
Sentence: "{sentence}"
"""
    try:
        print("[PROMPT TO GPT - DATE EXTRACTION]", prompt)
        response = openai_client.chat.completions.create( # Use the initialized client
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract a date in YYYY-MM-DD format from natural speech."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("Date extraction failed:", e)
        return None

def extract_bird_record(sentence):
    prompt = f"""
Extract the bird's name and species from this sentence:
"{sentence}"

Return a JSON object like {{"name": "Ahab", "species": "Harris Hawk"}} or null.
"""
    try:
        print("[PROMPT TO GPT - BIRD RECORD EXTRACTION]", prompt)
        response = openai_client.chat.completions.create( # Use the initialized client
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract bird records with name and species from natural speech."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("Bird record extraction failed:", e)
        return None
