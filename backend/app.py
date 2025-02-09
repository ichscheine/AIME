from flask import Flask, render_template
from pymongo import MongoClient
import random
import re  # Import regex module to clean up placeholders

app = Flask(__name__, template_folder='../aime/public')

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['amc10']
problems_collection = db['problems']

@app.route("/")
def show_problem():
    problem = problems_collection.aggregate([{"$sample": {"size": 1}}]).next()  # Select random problem

    # Replace {math_image_x} with actual math image URLs
    if problem and "problem_statement" in problem and "math_images" in problem:
        for i, img_url in enumerate(problem["math_images"]):
            problem["problem_statement"] = problem["problem_statement"].replace(f"{{math_image_{i}}}", f'<img src="{img_url}" class="math-image">', 1)

    # Replace {screenshot_image_x} with actual screenshot image URLs
    if problem and "problem_statement" in problem and "screenshot_images" in problem:
        for i, img_url in enumerate(problem["screenshot_images"]):
            problem["problem_statement"] = problem["problem_statement"].replace(f"{{screenshot_image_{i}}}", f'<img src="{img_url}" class="screenshot-image">', 1)

    # 🛑 Remove any remaining {math_image_x} or {screenshot_image_x} placeholders
    problem["problem_statement"] = re.sub(r"{math_image_\d+}", "", problem["problem_statement"])  # Remove remaining math placeholders
    problem["problem_statement"] = re.sub(r"{screenshot_image_\d+}", "", problem["problem_statement"])  # Remove remaining screenshot placeholders

    # Debugging output
    print("==== Processed Problem Before Rendering ====")
    print(f"Title: {problem['title']}")
    print(f"Statement: {problem['problem_statement']}")
    print("==========================================")

    return render_template("index.html", problem=problem)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
