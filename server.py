from flask import Flask, request, jsonify, Response
import logging
import json
from threading import Lock
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

mutex = Lock()
DB = "db.json"
try:
	with open(DB, "x") as file:
		# Write initial content if needed
		file.write("{}")

except Exception as e:
	logger.debug("File exists")

app = Flask(__name__)
@app.route('/', methods=['POST'])
def webhook():
	data = request.get_json()
	if data['event'] not in ["subscribed", "unsubscribed"]:
		return Response(status=200)
	
	if data['event'] == "subscribed":
		with mutex:
			subscribe(data)
	elif data['event'] == "unsubscribed":
		with mutex:
			unsubscribe(data)

	logger.debug("received request. post data:\n {0}".format(data))
	return Response(status=200)

@app.route('/', methods=['GET'])
def get_subscriber_data():
	with open(DB, 'r+') as db:
		current = json.load(db)
		return jsonify(current)

def subscribe(data):
    with open(DB, 'r+') as db:
        current = json.load(db)
        if 'subscribers' not in current:
            current['subscribers'] = []

        # Check if the user is already subscribed
        user_id = data['user']['id']
        if any(user['id'] == user_id for user in current['subscribers']):
            return

        current['subscribers'].append({
            'id': user_id,
            'name': data['user']['name']
        })

        # Move the file cursor to the beginning and truncate any remaining content
        db.seek(0)
        db.truncate()

        # Write the updated data back to the file
        json.dump(current, db)

def unsubscribe(data):
    with open(DB, 'r+') as db:
        current = json.load(db)
        if 'subscribes' not in current:
            current['subscribers'] = []

        # Create a new list without the user to be unsubscribed
        user_id = data['user_id']
        current['subscribers'] = [user for user in current['subscribers'] if user['id'] != user_id]

        # Move the file cursor to the beginning and truncate any remaining content
        db.seek(0)
        db.truncate()

        # Write the updated data back to the file
        json.dump(current, db)

