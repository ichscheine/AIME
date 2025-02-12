import os
from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS

# Load environment variables (make sure OPENAI_API_KEY is set in your environment or .env file)
# (The adaptive learning generation is handled separately.)
app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['amc10_test']
problems_collection = db['problems']
answer_keys_collection = db['answer_keys']
adaptive_collection = db['adaptive_learning']

###############################################
# Endpoint: Return a Random Problem
###############################################
@app.route("/")
def show_problem():
    try:
        problem = problems_collection.aggregate([{ "$sample": { "size": 1 } }]).next()
    except StopIteration:
        return jsonify({"error": "No problems found"}), 404

    problem['_id'] = str(problem['_id'])
    
    # Attach the answer key from the answer_keys_collection (if available)
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
# Endpoint: Get Adaptive Learning Data
###############################################
@app.route("/adaptive_learning", methods=["GET"])
def get_adaptive_learning():
    year = request.args.get("year")
    contest = request.args.get("contest")
    problem_number = request.args.get("problem_number")
    difficulty = request.args.get("difficulty", "medium")

    if not (year and contest and problem_number):
        return jsonify({"error": "Missing required parameters."}), 400

    query = {
        "year": year,
        "contest": contest,
        "problem_number": problem_number
    }
    adaptive_doc = adaptive_collection.find_one(query)
    if not adaptive_doc:
        return jsonify({
            "error": "Adaptive data not found.",
            "query": query,
            "message": "Please ensure that adaptive learning data has been generated for this problem."
        }), 404

    adaptive_doc["_id"] = str(adaptive_doc["_id"])
    solution_summaries = adaptive_doc.get("solution_summaries", [])
    solution_summary = solution_summaries[0] if solution_summaries else "No solution available."
    followup_questions = adaptive_doc.get("followup_questions", {})
    followup = followup_questions.get(difficulty, "No follow-up question available.")

    response_data = {
        "solution": solution_summary,
        "followup": followup,
        "available_difficulties": list(followup_questions.keys())
    }
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
