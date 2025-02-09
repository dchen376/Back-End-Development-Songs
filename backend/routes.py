from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

# create the /health endpoint
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK"}), 200

# create the /count endpoint
@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})

    return {"count": count}, 200

# exercise 2 : implement the GET /song endpoint
@app.route("/song", methods=['GET']) # a flask route to the GET method for endpoint /song/
def songs(): # a function called 'songs'
    results = list(db.songs.find({})) # find({}) to return all documents in database. and put into a list.
    return {'songs': parse_json(results)}, 200 # Send the data as a list in the form of {"songs":list of songs} and a return code of HTTP_200_OK back to the caller.

#ex 3: the GET /song/id endpoint
# Create a Flask route that responds to the GET method for the endpoint /song/<id>.
# Create a function called get_song_by_id(id) to hold the implementation.
# Use the db.songs.find_one({"id": id}) method to find a song by id
# Return a message of {"message": "song with id not found"} with an HTTP code of 404 NOT FOUND if the id is not found.
# Return the song as json with a status of 200 HTTP OK if you find the song in the database
@app.route("/song/<int:id>", methods=['GET'])
def get_song_by_id(id):
    song = db.songs.find_one({'id' : id})
    if not song:
        return {'message': f"song with id {id} not found"}, 404
    return parse_json(song), 200


#ex4: implement POST /song endpoint
# Create a Flask route that responds to the POST method for the endpoint /song/<id>. Use the methods=["POST"] in your app decorator.
# Create a function called create_song() to hold the implementation.
# You will first extract the song data from the request body and then append it to the data list.
# If a song with the id already exists, send an HTTP code of 302 back to the user with a message of {"Message": "song with id {song['id']} already present"}.
@app.route('/song', methods=['POST'])
def create_song():
    # get data from the json body
    song_in = request.json

    song = db.songs.find_one({'id': song_in['id']})
    if song:
        return {"Message": f"song with id {song['id']} already present"} ,302

    #extract song and append to the data list
    insert_id: InsertOneResult = db.songs.insert_one(song_in)

    return {'inserted id': parse_json(insert_id.inserted_id)}, 201

    
#ex 5: implement PUT /song endpoint
@app.route("/song/<int:id>", methods = ['PUT'])
def update_song(id):
    song_data = request.json
    song = db.songs.find_one({'id': id})

    if song == None:
        return {'message': 'song not found'}, 404

    updated_data = {"$set": song_data} # $set is use to update values in MongoDB
    result = db.songs.update_one({'id': id}, updated_data)

    if result.modified_count == 0:
        return {'message': 'song found, but nothing updated'}, 200
    else:
        return parse_json(db.songs.find_one({'id': id})), 201


#ex 6: DELETE /song endpoint
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = db.songs.delete_one({"id": id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    else:
        return "", 204