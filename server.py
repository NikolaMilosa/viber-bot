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

try:
	with open('db.json', "x") as file:
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
	with open('db.json', 'r+') as db:
		current = json.load(db)
		return jsonify(current)

def subscribe(data):
	with open('db.json', 'r+') as db:
		current = json.load(db)
		if 'subscribes' not in current:
			current['subscribers'] = []
		
		for user in current['subscribers']:
			if user['id'] == data['user']['id']:
				return

		current['subscribers'].append({
			'id': data['user']['id'],
			'name': data['user']['name']
		})
		db.seek(0)
		db.truncate()
		json.dump(current, db)

def unsubscribe(data):
	with open('db.json', 'r+') as db:
		current = json.load(db)
		if 'subscribes' not in current:
			current['subscribers'] = []
		
		current['subscribers'] = [user for user in current['subscribers'] if user['id'] != data['user_id']]
		db.seek(0)
		db.truncate()
		json.dump(current, db)


app.run(host='0.0.0.0', port=80, debug=True)