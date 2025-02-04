# from flask import Flask, jsonify
# import json
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)  # Allows frontend to access backend

# # Load problems from JSON file
# with open("../scraped_data/amc_10a_2024_problems.json", "r", encoding="utf-8") as f:
#     problems = json.load(f)

# @app.route("/problems", methods=["GET"])
# def get_problems():
#     return jsonify(problems)

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

from flask import Flask, jsonify
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows frontend access

# Load scraped problems
with open("../scraped_data/amc_10a_2024_problems.json", "r", encoding="utf-8") as f:
    problems = json.load(f)

@app.route("/problems", methods=["GET"])
def get_problems():
    return jsonify(problems)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
