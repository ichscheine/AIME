import requests
from bs4 import BeautifulSoup
import json

# URL of the AMC 10A 2024 Problems page
URL = "https://artofproblemsolving.com/wiki/index.php/2024_AMC_10A_Problems"

def scrape_problem(url):
    """Scrape a problem page and extract full HTML content, including images."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Failed to fetch {url}")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Extract the problem content inside the main container
    problem_section = soup.find("div", {"class": "mw-parser-output"})
    if problem_section:
        # Convert the HTML inside the problem section into a string
        problem_html = str(problem_section)

        # Fix relative image URLs to absolute URLs
        for img in problem_section.find_all("img"):
            if img["src"].startswith("/"):
                img["src"] = "https://artofproblemsolving.com" + img["src"]

        return {
            "url": url,
            "problem_html": problem_html.strip()
        }

def scrape_all_problems():
    """Scrape all problems and save them as HTML for rendering."""
    problem_links = [URL]  # The main page should have all problems listed
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
