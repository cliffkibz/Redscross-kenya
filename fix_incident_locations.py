from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['redcross_kenya']
incidents = db['incidents']

count = 0
for doc in incidents.find({"location": {"$type": "object"}}):
    loc = doc['location']
    if isinstance(loc, dict):
        new_location = loc.get('address') or str(loc)
        incidents.update_one({"_id": doc["_id"]}, {"$set": {"location": new_location}})
        count += 1

print(f"Updated {count} incidents with string location.")
