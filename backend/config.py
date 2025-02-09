import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import random

URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Problems"
LATEX_BASE_URL = "https:"  # Ensure LaTeX images are absolute URLs
WIKI_IMAGE_BASE_URL = "https:"  # Ensure Screenshot images are absolute URLs

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017")
    db = client['amc10']  # Name of the database
    problems_collection = db['problems']  # Name of the collection
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

def scrape_problems(url):
    """Scrape problems and correctly capture LaTeX math, answer choices, and large screenshots."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch {url}")
        return None

    soup = BeautifulSoup(response.text, "lxml")
    content_div = soup.find("div", {"class": "mw-parser-output"})
    if not content_div:
        print("Error: Could not find the main content div")
        return None

    problems = []
    current_problem = None

    for elem in content_div.find_all(["h2", "p", "ul", "li", "img", "a"]):
        if elem.name == "h2":
            if current_problem:
                # Only append valid problems
                if current_problem["problem_statement"] or current_problem["math_images"] or current_problem["screenshot_images"] or current_problem["answer_choices"]:
                    problems.append(current_problem)  # Save previous problem
            problem_title = elem.get_text(strip=True)
            current_problem = {
                "title": problem_title,
                "problem_statement": "",
                "math_images": [],
                "screenshot_images": [],
                "answer_choices": [],
            }

        elif elem.name == "p" and current_problem:
            text_parts = []
            for part in elem.contents:
                if isinstance(part, str):
                    text_parts.append(part.strip())
                elif part.name == "img":
                    img_src = part["src"]
                    if "latex.artofproblemsolving.com" in img_src:  # Math image or answer choice
                        full_img_src = LATEX_BASE_URL + img_src  # Ensure full URL
                        alt_text = part.get("alt", "")
                        if "textbf{" in alt_text and "}" in alt_text:  # Answer choices have textbf{}
                            if full_img_src not in current_problem["answer_choices"]:
                                current_problem["answer_choices"].append(full_img_src)
                        else:
                            if full_img_src not in current_problem["math_images"]:
                                current_problem["math_images"].append(full_img_src)
                                placeholder = f"{{math_image_{len(current_problem['math_images']) - 1}}}"
                                text_parts.append(placeholder)
                    elif "wiki-images.artofproblemsolving.com" in img_src:  # Screenshot image
                        full_img_src = img_src  # Full URL already present
                        if full_img_src not in current_problem["screenshot_images"]:
                            current_problem["screenshot_images"].append(full_img_src)
                            placeholder = f"{{screenshot_image_{len(current_problem['screenshot_images']) - 1}}}"
                            text_parts.append(placeholder)
            current_problem["problem_statement"] += " ".join(text_parts)

        elif elem.name == "ul" and current_problem:
            for li in elem.find_all("li"):
                text_parts = []
                for part in li.contents:
                    if isinstance(part, str):
                        text_parts.append(part.strip())
                    elif part.name == "img":
                        img_src = part["src"]
                        if "latex.artofproblemsolving.com" in img_src:  # Math image or answer choice
                            full_img_src = LATEX_BASE_URL + img_src  # Ensure full URL
                            alt_text = part.get("alt", "")
                            if "textbf{" in alt_text and "}" in alt_text:  # Answer choices have textbf{}
                                if full_img_src not in current_problem["answer_choices"]:
                                    current_problem["answer_choices"].append(full_img_src)
                            else:
                                if full_img_src not in current_problem["math_images"]:
                                    current_problem["math_images"].append(full_img_src)
                                    placeholder = f"{{math_image_{len(current_problem['math_images']) - 1}}}"
                                    text_parts.append(placeholder)
                        elif "wiki-images.artofproblemsolving.com" in img_src:  # Screenshot image
                            full_img_src = img_src  # Full URL already present
                            if full_img_src not in current_problem["screenshot_images"]:
                                current_problem["screenshot_images"].append(full_img_src)
                                placeholder = f"{{screenshot_image_{len(current_problem['screenshot_images']) - 1}}}"
                                text_parts.append(placeholder)
                current_problem["problem_statement"] += " ".join(text_parts)

        elif elem.name == "img" and current_problem:
            img_src = elem["src"]
            if "latex.artofproblemsolving.com" in img_src:  # Math image or answer choice
                full_img_src = LATEX_BASE_URL + img_src  # Ensure full URL
                alt_text = elem.get("alt", "")
                if "textbf{" in alt_text and "}" in alt_text:  # Answer choices have textbf{}
                    if full_img_src not in current_problem["answer_choices"]:
                        current_problem["answer_choices"].append(full_img_src)
                else:
                    if full_img_src not in current_problem["math_images"]:
                        current_problem["math_images"].append(full_img_src)
                        placeholder = f"{{math_image_{len(current_problem['math_images']) - 1}}}"
                        current_problem["problem_statement"] += placeholder
            elif "wiki-images.artofproblemsolving.com" in img_src:  # Screenshot image
                full_img_src = img_src  # Full URL already present
                if full_img_src not in current_problem["screenshot_images"]:
                    current_problem["screenshot_images"].append(full_img_src)
                    placeholder = f"{{screenshot_image_{len(current_problem['screenshot_images']) - 1}}}"
                    current_problem["problem_statement"] += placeholder

        elif elem.name == "a" and current_problem:  # Ensure screenshots in links are captured
            img_tag = elem.find("img")
            if img_tag:
                img_src = img_tag["src"]
                if "wiki-images.artofproblemsolving.com" in img_src:
                    full_img_src = img_src  # Full URL already present
                    if full_img_src not in current_problem["screenshot_images"]:
                        current_problem["screenshot_images"].append(full_img_src)
                        placeholder = f"{{screenshot_image_{len(current_problem['screenshot_images']) - 1}}}"
                        current_problem["problem_statement"] += placeholder

    if current_problem:
        # Only append valid problems
        if current_problem["problem_statement"] or current_problem["math_images"] or current_problem["screenshot_images"] or current_problem["answer_choices"]:
            problems.append(current_problem)

    # Debugging Output - Check captured images
    for problem in problems[:5]:
        print("==== Debugging Scraper Output ====")
        print(f"Title: {problem['title']}")
        print(f"Statement: {problem['problem_statement']}")
        print(f"Math Images: {problem['math_images']}")
        print(f"Screenshot Images: {problem['screenshot_images']}")
        print(f"Answer Choices: {problem['answer_choices']}")
        print("===============================\n")

    return problems

def save_problems_to_mongodb(problems):
    """Save problems to MongoDB."""
    try:
        for problem in problems:
            # Create a problem document with the required fields
            problem_document = {
                "title": problem.get("title", ""),
                "problem_statement": problem.get("problem_statement", ""),
                "math_images": problem.get("math_images", []),
                "screenshot_images": problem.get("screenshot_images", []),
                "answer_choices": problem.get("answer_choices", [])
            }

            # Insert the problem document into the database
            problems_collection.insert_one(problem_document)

        print(f"Inserted {len(problems)} problems into the database.")
    except Exception as e:
        print(f"Error saving problems to MongoDB: {e}")

if __name__ == "__main__":
    problems = scrape_problems(URL)
    if problems:
        random.shuffle(problems)  # Shuffle before saving
        save_problems_to_mongodb(problems)  # Save problems to MongoDB
        print(f"Scraped {len(problems)} problems successfully.")