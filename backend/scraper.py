import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re

# URLs for problems and answer key pages
URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Problems"
ANSWER_KEY_URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Answer_Key"
LATEX_BASE_URL = "https:"  # Ensure LaTeX images are absolute URLs

# Connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017")
    db = client['amc10_test']  # Name of the database
    problems_collection = db['problems']         # Collection for problems
    answer_keys_collection = db['answer_keys']     # Collection for answer keys
    solutions_collection = db['solutions']         # Collection for solutions
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

def scrape_solution_page(relative_url):
    """
    Given a relative URL (e.g. "/wiki/index.php/2024_AMC_10A_Problems/Problem_1"),
    fetch the solution page and extract its text.
    """
    base_url = "https://artofproblemsolving.com"
    full_url = base_url + relative_url
    print(f"Fetching solution from: {full_url}")
    response = requests.get(full_url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch solution page {full_url}")
        return ""
    sol_soup = BeautifulSoup(response.text, "lxml")
    content_div = sol_soup.find("div", {"class": "mw-parser-output"})
    if not content_div:
        print("Error: Could not find solution content div.")
        return ""
    # Gather text from all paragraphs that have content.
    paragraphs = content_div.find_all("p")
    solution_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    return solution_text

def scrape_problems(url):
    """
    Scrape problems from the main AoPS page.
    In addition to capturing LaTeX math, answer choices, screenshots,
    and metadata, this version looks for a "Solution" link in a <p> element.
    When found, it fetches the solution page and stores its text in a "solution" field.
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
    skip_headers = ["see also", "references", "external links", "contents"]

    # Process elements in document order.
    for elem in content_div.find_all(["h2", "p", "ul", "li", "img", "a"]):
        if elem.name == "h2":
            # Finalize the previous problem if it exists.
            if current_problem:
                meta_str = f"({current_problem['year']} {current_problem['contest']}, Problem {current_problem['problem_number']})"
                current_problem["problem_statement"] += "\n" + meta_str
                problems.append(current_problem)
            # A new <h2> signals a new problem.
            problem_title = elem.get_text(strip=True)
            if problem_title.strip().lower() in skip_headers:
                current_problem = None
                continue
            if "problem" not in problem_title.lower():
                current_problem = None
                continue

            # Extract problem number from the header (e.g. "Problem 1")
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
                # "solution" field will be added if a solution link is found.
            }
        elif elem.name == "p" and current_problem:
            # Check if this paragraph contains a "Solution" link.
            anchor = elem.find(lambda tag: tag.name == "a" and tag.get_text(strip=True).lower() == "solution")
            if anchor:
                # Avoid re-scraping if already found.
                if "solution" not in current_problem:
                    solution_href = anchor.get("href")
                    sol_text = scrape_solution_page(solution_href)
                    current_problem["solution"] = sol_text
                # Skip further processing of this <p> element.
                continue

            # Otherwise, process the paragraph as part of the problem statement.
            text_parts = []
            for part in elem.contents:
                if isinstance(part, str):
                    text_parts.append(part.strip())
                elif part.name == "img":
                    img_src = part.get("src")
                    if not img_src:
                        continue
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
        elif elem.name == "ul" and current_problem:
            for li in elem.find_all("li"):
                text_parts = []
                for part in li.contents:
                    if isinstance(part, str):
                        text_parts.append(part.strip())
                    elif part.name == "img":
                        img_src = part.get("src")
                        if not img_src:
                            continue
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
            img_src = elem.get("src")
            if not img_src:
                continue
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
            # In case a solution link appears outside a <p> (fallback)
            if elem.get_text(strip=True).lower() == "solution":
                if "solution" not in current_problem:
                    solution_href = elem.get("href")
                    sol_text = scrape_solution_page(solution_href)
                    current_problem["solution"] = sol_text
    # Append the final problem.
    if current_problem:
        meta_str = f"({current_problem['year']} {current_problem['contest']}, Problem {current_problem['problem_number']})"
        current_problem["problem_statement"] += "\n" + meta_str
        problems.append(current_problem)

    # Debug output for the first few problems
    for prob in problems[:5]:
        print("==== Debugging Scraper Output ====")
        print(f"Meta: {prob.get('year')} {prob.get('contest')}, Problem Number: {prob.get('problem_number')}")
        print(f"Statement: {prob['problem_statement']}")
        print(f"Math Images: {prob['math_images']}")
        print(f"Screenshot Images: {prob['screenshot_images']}")
        print(f"Answer Choices: {prob['answer_choices']}")
        if "solution" in prob:
            print(f"Solution (first 100 chars): {prob['solution'][:100]}...")
        print("===============================\n")

    return problems

def scrape_answer_keys(url):
    """
    Scrape answer keys from AoPS and extract metadata (year and contest).
    """
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
    ol = content_div.find("ol")
    if ol:
        lis = ol.find_all("li")
        for idx, li in enumerate(lis, start=1):
            text = li.get_text(strip=True)
            answer_keys[f"Problem {idx}"] = text
    else:
        # Fallback method.
        problem_number = 1
        for elem in content_div.find_all("li"):
            text = elem.get_text(strip=True)
            if text.startswith(f"{problem_number}."):
                answer = text.split(".", 1)[-1].strip()
                answer_keys[f"Problem {problem_number}"] = answer
                problem_number += 1

    print("Scraped answer keys:", answer_keys)
    return {"year": year, "contest": contest, "answers": answer_keys}

def save_problems_to_mongodb(problems):
    """
    Save problems to MongoDB after validating that there are exactly 25 problems.
    """
    if len(problems) != 25:
        print(f"Error: Expected 25 problems, but scraped {len(problems)} problems. Skipping save.")
        return
    try:
        for problem in problems:
            # Remove the title field before saving.
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
    """
    answers = answer_keys_data.get("answers", {})
    if len(answers) != 25:
        print(f"Error: Expected 25 answer keys, but scraped {len(answers)} answer keys. Skipping save.")
        return
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

def save_solutions_to_mongodb(solutions):
    """
    Save scraped solutions to a separate MongoDB collection.
    Each solution document includes metadata (year, contest, problem_number) and the solution text.
    """
    if not solutions:
        print("No solutions found to save.")
        return
    try:
        for sol in solutions:
            solutions_collection.insert_one(sol)
        print(f"Inserted {len(solutions)} solutions into the database.")
    except Exception as e:
        print(f"Error saving solutions to MongoDB: {e}")

# --- For direct running ---
if __name__ == "__main__":
    # Scrape problems (which now may include a solution field)
    problems = scrape_problems(URL)
    if problems:
        # Save problems to the problems collection.
        for problem in problems:
            problems_collection.insert_one(problem)
        print(f"Scraped {len(problems)} problems successfully.")

        # Extract and save solutions (if available) to the solutions collection.
        solutions = []
        for problem in problems:
            if "solution" in problem and problem["solution"].strip():
                solution_document = {
                    "year": problem.get("year", ""),
                    "contest": problem.get("contest", ""),
                    "problem_number": problem.get("problem_number", ""),
                    "solution": problem["solution"].strip()
                }
                solutions.append(solution_document)
        save_solutions_to_mongodb(solutions)

    # Scrape and save answer keys with metadata.
    answer_keys_data = scrape_answer_keys(ANSWER_KEY_URL)
    if answer_keys_data:
        save_answer_keys_to_mongodb(answer_keys_data)
        print("Scraped answer keys successfully.")
