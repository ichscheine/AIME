import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
import random

# URLs for problems and answer key pages
URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Problems"
ANSWER_KEY_URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Answer_Key"
LATEX_BASE_URL = "https:"  # Ensure LaTeX images are absolute URLs
WIKI_IMAGE_BASE_URL = "https:"  # Ensure Screenshot images are absolute URLs

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017")
    db = client['amc10']  # Name of the database
    problems_collection = db['problems']         # Collection for problems
    answer_keys_collection = db['answer_keys']     # Collection for answer keys
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

def scrape_problems(url):
    """
    Scrape problems and correctly capture LaTeX math, answer choices, screenshots,
    and extract metadata such as year, contest, and problem number.
    The metadata is appended to the problem statement and the separate title is removed.
    """
    # Extract metadata from the URL
    metadata = re.search(r'/index\.php/(\d+)_([A-Za-z0-9_]+)_Problems', url)
    if metadata:
        year = metadata.group(1)
        contest = metadata.group(2).replace('_', ' ')
    else:
        year = ""
        contest = ""
    
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

    # Define headers we want to skip
    skip_headers = ["see also", "references", "external links", "contents"]

    for elem in content_div.find_all(["h2", "p", "ul", "li", "img", "a"]):
        if elem.name == "h2":
            # Finalize and append the previous problem if it exists and is valid.
            if current_problem:
                # Only append if its header was valid (i.e. not in skip_headers)
                if current_problem.get("title", "").strip().lower() not in skip_headers:
                    # Append metadata to the problem statement
                    meta_str = f"({current_problem['year']} {current_problem['contest']}, Problem {current_problem['problem_number']})"
                    current_problem["problem_statement"] += "\n" + meta_str
                    # Remove the title field (as requested)
                    del current_problem["title"]
                    problems.append(current_problem)
            # Start a new problem
            problem_title = elem.get_text(strip=True)
            # Skip headers that are not actual problems
            if problem_title.strip().lower() in skip_headers:
                current_problem = None
                continue
            # Optionally, only accept headers that contain the word "problem"
            if "problem" not in problem_title.lower():
                current_problem = None
                continue

            # Extract problem number from the header (e.g., "Problem 25")
            problem_number = None
            match = re.search(r"Problem\s+(\d+)", problem_title)
            if match:
                problem_number = match.group(1)

            current_problem = {
                "title": problem_title,
                "problem_statement": "",
                "math_images": [],
                "screenshot_images": [],
                "answer_choices": [],
                "year": year,
                "contest": contest,
                "problem_number": problem_number
            }

        elif elem.name == "p" and current_problem:
            text_parts = []
            for part in elem.contents:
                if isinstance(part, str):
                    text_parts.append(part.strip())
                elif part.name == "img":
                    img_src = part["src"]
                    if "latex.artofproblemsolving.com" in img_src:  # Math image or answer choice
                        full_img_src = LATEX_BASE_URL + img_src
                        alt_text = part.get("alt", "")
                        if "textbf{" in alt_text and "}" in alt_text:
                            if full_img_src not in current_problem["answer_choices"]:
                                current_problem["answer_choices"].append(full_img_src)
                        else:
                            if full_img_src not in current_problem["math_images"]:
                                current_problem["math_images"].append(full_img_src)
                                placeholder = f"{{math_image_{len(current_problem['math_images']) - 1}}}"
                                text_parts.append(placeholder)
                    elif "wiki-images.artofproblemsolving.com" in img_src:  # Screenshot image
                        full_img_src = img_src
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
                        if "latex.artofproblemsolving.com" in img_src:
                            full_img_src = LATEX_BASE_URL + img_src
                            alt_text = part.get("alt", "")
                            if "textbf{" in alt_text and "}" in alt_text:
                                if full_img_src not in current_problem["answer_choices"]:
                                    current_problem["answer_choices"].append(full_img_src)
                            else:
                                if full_img_src not in current_problem["math_images"]:
                                    current_problem["math_images"].append(full_img_src)
                                    placeholder = f"{{math_image_{len(current_problem['math_images']) - 1}}}"
                                    text_parts.append(placeholder)
                        elif "wiki-images.artofproblemsolving.com" in img_src:
                            full_img_src = img_src
                            if full_img_src not in current_problem["screenshot_images"]:
                                current_problem["screenshot_images"].append(full_img_src)
                                placeholder = f"{{screenshot_image_{len(current_problem['screenshot_images']) - 1}}}"
                                text_parts.append(placeholder)
                current_problem["problem_statement"] += " ".join(text_parts)

        elif elem.name == "img" and current_problem:
            img_src = elem["src"]
            if "latex.artofproblemsolving.com" in img_src:
                full_img_src = LATEX_BASE_URL + img_src
                alt_text = elem.get("alt", "")
                if "textbf{" in alt_text and "}" in alt_text:
                    if full_img_src not in current_problem["answer_choices"]:
                        current_problem["answer_choices"].append(full_img_src)
                else:
                    if full_img_src not in current_problem["math_images"]:
                        current_problem["math_images"].append(full_img_src)
                        placeholder = f"{{math_image_{len(current_problem['math_images']) - 1}}}"
                        current_problem["problem_statement"] += placeholder
            elif "wiki-images.artofproblemsolving.com" in img_src:
                full_img_src = img_src
                if full_img_src not in current_problem["screenshot_images"]:
                    current_problem["screenshot_images"].append(full_img_src)
                    placeholder = f"{{screenshot_image_{len(current_problem['screenshot_images']) - 1}}}"
                    current_problem["problem_statement"] += placeholder

        elif elem.name == "a" and current_problem:
            img_tag = elem.find("img")
            if img_tag:
                img_src = img_tag["src"]
                if "wiki-images.artofproblemsolving.com" in img_src:
                    full_img_src = img_src
                    if full_img_src not in current_problem["screenshot_images"]:
                        current_problem["screenshot_images"].append(full_img_src)
                        placeholder = f"{{screenshot_image_{len(current_problem['screenshot_images']) - 1}}}"
                        current_problem["problem_statement"] += placeholder

    # Append the final problem if it exists and is valid.
    if current_problem:
        if current_problem.get("title", "").strip().lower() not in skip_headers:
            meta_str = f"({current_problem['year']} {current_problem['contest']}, Problem {current_problem['problem_number']})"
            current_problem["problem_statement"] += "\n" + meta_str
            del current_problem["title"]
            problems.append(current_problem)

    # Debugging Output for the first few problems
    for problem in problems[:5]:
        print("==== Debugging Scraper Output ====")
        print(f"Meta: {problem.get('year')} {problem.get('contest')}, Problem Number: {problem.get('problem_number')}")
        print(f"Statement: {problem['problem_statement']}")
        print(f"Math Images: {problem['math_images']}")
        print(f"Screenshot Images: {problem['screenshot_images']}")
        print(f"Answer Choices: {problem['answer_choices']}")
        print("===============================\n")

    return problems

def scrape_answer_keys(url):
    """Scrape answer keys from AoPS and extract metadata (year and contest)."""
    # Extract metadata from URL
    metadata = re.search(r'/index\.php/(\d+)_([A-Za-z0-9_]+)_Answer_Key', url)
    if metadata:
        year = metadata.group(1)
        contest = metadata.group(2).replace('_', ' ')
    else:
        year = ""
        contest = ""
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch {url}")
        return None

    soup = BeautifulSoup(response.text, "lxml")
    content_div = soup.find("div", {"class": "mw-parser-output"})
    if not content_div:
        print("Error: Could not find the main content div")
        return None

    answer_keys = {}

    # Try to locate an ordered list (<ol>) containing the answers.
    ol = content_div.find("ol")
    if ol:
        lis = ol.find_all("li")
        for idx, li in enumerate(lis, start=1):
            text = li.get_text(strip=True)
            answer_keys[f"Problem {idx}"] = text
    else:
        # Fallback: look for <li> elements that start with a number followed by a period.
        problem_number = 1
        for elem in content_div.find_all("li"):
            text = elem.get_text(strip=True)
            if text.startswith(f"{problem_number}."):
                answer = text.split(".", 1)[-1].strip()
                answer_keys[f"Problem {problem_number}"] = answer
                problem_number += 1

    print("Scraped answer keys:", answer_keys)
    # Return a dictionary that includes metadata along with the answers.
    return {"year": year, "contest": contest, "answers": answer_keys}

def save_problems_to_mongodb(problems):
    """Save problems to MongoDB after validating that there are exactly 25 problems."""
    # Validate that we have exactly 25 problems.
    if len(problems) != 25:
        print(f"Error: Expected 25 problems, but scraped {len(problems)} problems. Skipping save.")
        return  # Skip saving if validation fails.

    try:
        for problem in problems:
            # Create a problem document with the required fields, including metadata.
            problem_document = {
                "problem_statement": problem.get("problem_statement", ""),
                "math_images": problem.get("math_images", []),
                "screenshot_images": problem.get("screenshot_images", []),
                "answer_choices": problem.get("answer_choices", []),
                "year": problem.get("year", ""),
                "contest": problem.get("contest", ""),
                "problem_number": problem.get("problem_number", "")
            }
            problems_collection.insert_one(problem_document)

        print(f"Inserted {len(problems)} problems into the database.")
    except Exception as e:
        print(f"Error saving problems to MongoDB: {e}")


def save_answer_keys_to_mongodb(answer_keys_data):
    """
    Save answer keys to MongoDB after validating that there are exactly 25 answer keys.
    answer_keys_data should be a dictionary with keys: "year", "contest", and "answers"
    where "answers" is a dictionary mapping problem numbers (e.g., "Problem 1") to the answer.
    """
    answers = answer_keys_data.get("answers", {})
    if len(answers) != 25:
        print(f"Error: Expected 25 answer keys, but scraped {len(answers)} answer keys. Skipping save.")
        return  # Skip saving if validation fails.

    try:
        answer_keys_document = {
            "title": f"{answer_keys_data['year']} {answer_keys_data['contest']} Answer Key",
            "year": answer_keys_data['year'],
            "contest": answer_keys_data['contest'],
            "answers": answers
        }
        answer_keys_collection.insert_one(answer_keys_document)
        print("Inserted answer keys into the database.")
    except Exception as e:
        print(f"Error saving answer keys to MongoDB: {e}")

# --- For direct running ---
if __name__ == "__main__":
    # Scrape and save problems
    problems = scrape_problems(URL)
    if problems:
        # For example, you might want to shuffle or check for duplicates here.
        for problem in problems:
            problems_collection.insert_one(problem)
        print(f"Scraped {len(problems)} problems successfully.")

    # Scrape and save answer keys with metadata
    answer_keys_data = scrape_answer_keys(ANSWER_KEY_URL)
    if answer_keys_data:
        save_answer_keys_to_mongodb(answer_keys_data)
        print("Scraped answer keys successfully.")