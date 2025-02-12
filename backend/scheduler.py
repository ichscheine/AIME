from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

import time
from scraper import (
    scrape_problems,
    scrape_answer_keys,
    save_problems_to_mongodb,
    save_answer_keys_to_mongodb
)

# List of URLs to scrape
PROBLEM_URLS = [
    "https://artofproblemsolving.com/wiki/index.php/2023_AMC_10A_Problems",
    # Add more problem URLs here
]

ANSWER_KEY_URLS = [
    "https://artofproblemsolving.com/wiki/index.php/2023_AMC_10A_Answer_Key",
    # Add more answer key URLs here
]

def scheduled_scrape():
    print("Starting scheduled scraping job...")
    
    # Scrape and save problems for each URL.
    for url in PROBLEM_URLS:
        print(f"Scraping problems from {url}")
        problems = scrape_problems(url)
        if problems:
            save_problems_to_mongodb(problems)
            print(f"Inserted {len(problems)} problems from {url} into the database.")
        else:
            print(f"No problems scraped from {url}.")
    
    # Scrape and save answer keys for each URL.
    for url in ANSWER_KEY_URLS:
        print(f"Scraping answer keys from {url}")
        answer_keys = scrape_answer_keys(url)
        if answer_keys:
            save_answer_keys_to_mongodb(answer_keys)
            print(f"Inserted answer keys from {url} into the database.")
        else:
            print(f"No answer keys scraped from {url}.")
    
    print("Scheduled scraping job completed.")

if __name__ == "__main__":
    # Create a BackgroundScheduler instance.
    scheduler = BackgroundScheduler()

    # Schedule the job to run every 6 hours (for example).
    scheduler.add_job(scheduled_scrape, 'interval', hours=6, next_run_time=datetime.now())

    # Start the scheduler.
    scheduler.start()
    
    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        # Keep the main thread alive.
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")
