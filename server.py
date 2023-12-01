from flask import Flask, request, jsonify, Response
import logging
import json
import os
from pymongo.mongo_client import MongoClient

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


app = Flask(__name__)

user = os.environ.get("MONGO_USER", "")
password = os.environ.get("MONGO_PASS", "")
uri = f"mongodb+srv://{user}:{password}@viberbotcluster.fyohhnr.mongodb.net/?retryWrites=true&w=majority"
logger.debug(uri)
client = MongoClient(uri)
subscriptions = client.subs.subs

@app.route('/', methods=['POST'])
def webhook():
	data = request.get_json()
	if data['event'] not in ["subscribed", "unsubscribed"]:
		return Response(status=200)
	
	if data['event'] == "subscribed":
		subscribe(data)
	elif data['event'] == "unsubscribed":
		unsubscribe(data)

	logger.debug("received request. post data:\n {0}".format(data))
	return Response(status=200)

@app.route('/', methods=['GET'])
def get_subscriber_data():
	return jsonify([subscription for subscription in subscriptions.find()])

def subscribe(data):
    present = subscriptions.find_one({"_id": data['user']['id']})
    if present:
        return
    
    subscriptions.insert_one({"_id": data['user']['id'], 'name': data['user']['name']})

def unsubscribe(data):
    present = subscriptions.find_one({"_id": data['user_id']})
    if not present:
        return
    
    subscriptions.delete_one({"_id": data['user_id']})
