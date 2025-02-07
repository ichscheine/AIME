import requests
from bs4 import BeautifulSoup
import json
import random

URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Problems"
LATEX_BASE_URL = "https:"  # AoPS LaTeX images use relative URLs

def scrape_problems(url):
    """Scrape problems and correctly insert placeholders for LaTeX images."""
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

    for elem in content_div.find_all(["h2", "p"]):
        if elem.name == "h2":
            if current_problem:
                problems.append(current_problem)  # Save previous problem
            problem_title = elem.get_text(strip=True)
            current_problem = {"title": problem_title, "problem_statement": "", "image_urls": []}

        elif elem.name == "p" and current_problem:
            text_parts = []
            image_counter = 0

            for part in elem.contents:
                if isinstance(part, str):
                    text_parts.append(part.strip())

                elif part.name == "img" and "latex" in part.get("class", []):
                    img_src = LATEX_BASE_URL + part["src"]
                    current_problem["image_urls"].append(img_src)
                    text_parts.append(f"{{math_{image_counter}}}")  # Unique placeholder
                    image_counter += 1

            current_problem["problem_statement"] += " ".join(text_parts)

    if current_problem:
        problems.append(current_problem)

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
