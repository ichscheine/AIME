import os
from flask import Flask, jsonify, abort, request
from pymongo import MongoClient
import random
import re
import openai
from flask_cors import CORS

# Load environment variables (make sure to set OPENAI_API_KEY in your environment or .env file)
openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['amc10']
problems_collection = db['problems']
answer_keys_collection = db['answer_keys']

# Import adaptive learning components from adaptive_learning.py
from adaptive_learning import (
    RLAgent,
    generate_explanation,
    generate_followup_question,
    explain_and_generate
)

# Instantiate a global RL agent with difficulty levels
actions = ["easy", "medium", "hard"]
agent = RLAgent(actions)

###############################################
# Existing Endpoint: Return a Random Problem
###############################################
@app.route("/")
def show_problem():
    try:
        problem = problems_collection.aggregate([{ "$sample": { "size": 1 } }]).next()
    except StopIteration:
        return jsonify({"error": "No problems found"}), 404

    problem['_id'] = str(problem['_id'])
    answer_keys_doc = answer_keys_collection.find_one({})
    if answer_keys_doc:
        answer_keys_doc['_id'] = str(answer_keys_doc['_id'])
        answers = answer_keys_doc.get("answers", {})
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

###############################################
# New Endpoint: Adaptive Explanation & Follow-up Generation
###############################################
@app.route("/adaptive_explain", methods=["POST"])
def adaptive_explain():
    data = request.get_json()
    problem_text = data.get("problem_text")
    student_answer = data.get("student_answer")
    correct_answer = data.get("correct_answer")
    if not problem_text or not student_answer or not correct_answer:
        return jsonify({"error": "Missing required fields."}), 400

    result = explain_and_generate(problem_text, student_answer, correct_answer, agent)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
