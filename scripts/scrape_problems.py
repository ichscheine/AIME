import requests
from bs4 import BeautifulSoup
import json
import random

URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Problems"
LATEX_BASE_URL = "https:"  # Ensure LaTeX images are absolute URLs
WIKI_IMAGE_BASE_URL = "https:"  # Ensure Screenshot images are absolute URLs

def scrape_problems(url):
    """Scrape problems and correctly capture LaTeX math and large screenshots."""
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

    for elem in content_div.find_all(["h2", "p", "figure", "table", "a"]):
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
                "answer_choices": "",
            }

        elif elem.name == "p" and current_problem:
            text_parts = []
            image_counter = 0

            for part in elem.contents:
                if isinstance(part, str):
                    text_parts.append(part.strip())

                elif part.name == "img":
                    img_src = part["src"]

                    if "latex.artofproblemsolving.com" in img_src:  # Math image
                        full_img_src = LATEX_BASE_URL + img_src  # Ensure full URL

                        # Check if the image alt contains any answer choices
                        alt_text = part.get("alt", "")
                        if "textbf{" in alt_text and "}" in alt_text:  # Answer choices have textbf{}
                            current_problem["answer_choices"] = full_img_src  # Store answer choices separately
                        else:
                            current_problem["math_images"].append(full_img_src)
                            text_parts.append(f"{{math_{image_counter}}}")
                        
                    elif "wiki-images.artofproblemsolving.com" in img_src:  # Large Screenshot images
                        full_img_src = img_src  # Full URL already present
                        current_problem["screenshot_images"].append(full_img_src)

                    image_counter += 1

            current_problem["problem_statement"] += " ".join(text_parts)

        elif elem.name == "a" and current_problem:  # Ensure screenshots in links are captured
            img_tag = elem.find("img")
            if img_tag:
                img_src = img_tag["src"]
                if "wiki-images.artofproblemsolving.com" in img_src:
                    full_img_src = img_src  # Full URL already present
                    current_problem["screenshot_images"].append(full_img_src)

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

def save_problems_to_json(problems, filename="scraped_data/amc_10a_2024_problems.json"):
    """Save problems to JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    problems = scrape_problems(URL)
    if problems:
        random.shuffle(problems)  # Shuffle before saving
        save_problems_to_json(problems)
        print(f"Scraped {len(problems)} problems successfully.")
