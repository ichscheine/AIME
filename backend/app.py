from flask import Flask, jsonify
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app)

# Load problem data
with open("scraped_data/amc_10a_2024_problems.json", "r", encoding="utf-8") as f:
    problems = json.load(f)

@app.route("/random_problem", methods=["GET"])
def get_random_problem():
    """Return a single random problem with images instead of LaTeX."""
    if not problems:
        return jsonify({"error": "No problems available"}), 500
    
    random_problem = random.choice(problems)
    return jsonify(random_problem)

@app.route("/", methods=["GET"])
def home():
    return "Math Problem API is running. Use /random_problem to get a problem."

if __name__ == "__main__":
    print("Starting Flask server at http://0.0.0.0:5001")
    app.run(debug=True, host="0.0.0.0", port=5001)