from flask import Flask, render_template, jsonify
from pymongo import MongoClient
import random
import re  # Import regex module to clean up placeholders

app = Flask(__name__, template_folder='../aime/public')

from flask_cors import CORS
CORS(app)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['amc10']
problems_collection = db['problems']

@app.route("/")
def show_problem():
    problem = problems_collection.aggregate([{ "$sample": { "size": 1 } }]).next()  # Fetch a random problem
    problem['_id'] = str(problem['_id'])  # Convert ObjectId to string if needed
    return jsonify(problem)  # Send JSON response instead of rendering template

if __name__ == "__main__":
    app.run(debug=True, port=5001)
