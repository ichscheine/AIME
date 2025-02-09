from flask import Flask, jsonify, request, abort
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
answer_keys_collection = db['answer_keys']  # Collection containing the answer keys document

@app.route("/")
def show_problem():
    """
    This endpoint returns a random problem.
    It also looks up the corresponding answer key (using the problem's title)
    from the answer_keys collection and adds it to the JSON response.
    """
    # Fetch a random problem from the problems collection.
    problem = problems_collection.aggregate([{ "$sample": { "size": 1 } }]).next()
    problem['_id'] = str(problem['_id'])  # Convert ObjectId to string if needed

    # Fetch the answer keys document.
    answer_keys_doc = answer_keys_collection.find_one({})
    if answer_keys_doc:
        answer_keys_doc['_id'] = str(answer_keys_doc['_id'])
        # Extract the mapping of problem titles to their answers.
        answers = answer_keys_doc.get("answers", {})
        # Use the problem's title (e.g., "Problem 13") as the key.
        problem_title = problem.get("title", "")
        answer_key = answers.get(problem_title, None)
        problem["answer_key"] = answer_key
    else:
        problem["answer_key"] = None

    return jsonify(problem)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
