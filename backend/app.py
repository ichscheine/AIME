from flask import Flask, jsonify, abort, request
from pymongo import MongoClient
import random

app = Flask(__name__)
# Allow CORS as needed (optional)
from flask_cors import CORS
CORS(app)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['amc10']
problems_collection = db['problems']
answer_keys_collection = db['answer_keys']

@app.route("/")
def show_problem():
    """
    This endpoint returns a random problem and attaches its corresponding answer key
    by using the problem_number field.
    """
    # Fetch a random problem
    try:
        problem = problems_collection.aggregate([{ "$sample": { "size": 1 } }]).next()
    except StopIteration:
        return jsonify({"error": "No problems found"}), 404

    # Convert the ObjectId to string if needed
    problem['_id'] = str(problem['_id'])

    # Fetch the answer keys document
    answer_keys_doc = answer_keys_collection.find_one({})
    if answer_keys_doc:
        answer_keys_doc['_id'] = str(answer_keys_doc['_id'])
        answers = answer_keys_doc.get("answers", {})

        # Use the problem_number field to construct the key.
        problem_number = problem.get("problem_number", None)
        if problem_number:
            key = f"Problem {problem_number}"
            answer_key = answers.get(key, None)
            problem["answer_key"] = answer_key
        else:
            problem["answer_key"] = None
    else:
        problem["answer_key"] = None

    return jsonify(problem)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
