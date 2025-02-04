import requests
from bs4 import BeautifulSoup
import json
import re

# URL of the AMC 10A 2024 Problems page
URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Problems"

def get_problem_links(url):
    """Scrape the main page to find problem links."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch {url}")
        return []
    
    soup = BeautifulSoup(response.text, "lxml")
    problem_links = []

    # Find all links leading to problems (identified by "Problem 1", "Problem 2", etc.)
    for link in soup.find_all("a", href=True):
        if "Problem_1" in link["href"] or "Problem_2" in link["href"]:  # Pattern match
            full_url = f"https://artofproblemsolving.com{link['href']}"
            problem_links.append(full_url)
    
    return problem_links

def scrape_problem(url):
    """Scrape a single problem's content and return structured data."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch {url}")
        return None
    
    soup = BeautifulSoup(response.text, "lxml")

    # Extract the problem statement
    problem_statement = ""
    problem_section = soup.find("div", {"class": "mw-parser-output"})
    if problem_section:
        paragraphs = problem_section.find_all("p")
        for p in paragraphs:
            text = p.get_text(separator=" ", strip=True)
            problem_statement += text + " "

    # Extract LaTeX equations if available
    latex_expressions = []
    for img in soup.find_all("img", {"class": "latex"}):
        latex_expressions.append(img["alt"])  # LaTeX is stored in the alt attribute

    # Clean problem text (remove wiki references)
    problem_statement = re.sub(r"\[.*?\]", "", problem_statement)

    return {
        "url": url,
        "problem_statement": problem_statement.strip(),
        "latex_expressions": latex_expressions
    }

def scrape_all_problems():
    """Scrape all problems from the 2024 AMC 10A main page."""
    problem_links = get_problem_links(URL)
    all_problems = []

    for link in problem_links:
        problem_data = scrape_problem(link)
        if problem_data:
            all_problems.append(problem_data)

    # Save data to JSON
    with open("scraped_data/amc_10a_2024_problems.json", "w", encoding="utf-8") as f:
        json.dump(all_problems, f, indent=4, ensure_ascii=False)

    print(f"Scraped {len(all_problems)} problems successfully.")

if __name__ == "__main__":
    scrape_all_problems()
