import sqlite3
import re
import time
from seleniumbase import SB
from selenium.common.exceptions import NoSuchElementException

# Database Setup and Helper Functions 
DB_NAME = "jobs.db"

def init_db():
    """Initializes the SQLite database and creates the 'jobs' table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           job_title TEXT,
           firm_name TEXT,
           city TEXT,
           state TEXT,
           area_of_law TEXT,
           description TEXT,
           salary TEXT,
           deadline TEXT,
           mentions_1l BOOLEAN,
           source_url TEXT UNIQUE,
           scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized successfully.")

def save_job_to_db(job_data):
    """Saves a single job record to the database, ignoring duplicates based on source_url."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR IGNORE INTO jobs (
                job_title, firm_name, city, state, area_of_law,
                description, salary, deadline, mentions_1l, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data['job_title'],
            job_data['firm_name'],
            job_data['city'],
            job_data['state'],
            job_data['area_of_law'],
            job_data['description'],
            job_data['salary'],
            job_data['deadline'],
            job_data['mentions_1l'],
            job_data['source_url']
        ))
        conn.commit()
        if cur.rowcount > 0:
            print(f"  -> Saved new job to DB: {job_data['job_title']}")
        else:
            print(f"  -> Job already exists in DB: {job_data['job_title']}")
    except sqlite3.Error as e:
        print(f"  -> Database error for '{job_data['job_title']}': {e}")
    finally:
        conn.close()

def mentions_1l(text):
    """Checks if the text explicitly mentions '1L' or 'first-year law'."""
    return bool(re.search(r"\b1L\b|first[- ]year law", text, re.I))

def detect_area(text):
    """Detects the area of law from the job description text."""
    text_lower = text.lower()
    if "corporate" in text_lower:
        return "Corporate Law"
    if "litigation" in text_lower:
        return "Litigation"
    if "criminal" in text_lower:
        return "Criminal Law"
    if "intellectual property" in text_lower or "ip" in text_lower:
        return "Intellectual Property"
    return "General Law"

def find_deadline(text):
    """A basic function to find an application deadline in the text."""
    match = re.search(r"(?:deadline|apply by)\s*:?\s*(\w+\s\d{1,2}(?:st|nd|rd|th)?(?:,\s\d{4})?)", text, re.I)
    if match:
        return match.group(1)
    return None

# Main Scraping Logic 

def get_text_if_exists(sb_instance, selector):
    """Safely gets text from an element, returning an empty string if not found."""
    try:
        return sb_instance.get_text(selector).strip()
    except NoSuchElementException:
        return ""

def scrape_and_save_jobs():
    """
    Scrapes job listings from Indeed, processes the data, and saves it to a SQLite database.
    """
    with SB(uc=True, headless=False) as sb:
        url = "https://www.indeed.com/jobs?q=1L+Summer+Law&l=Georgia"
        sb.driver.uc_open_with_reconnect(url, 3)

        try:
            sb.click('button[aria-label="close"]', timeout=6)
            print("Closed a pop-up window.")
        except Exception:
            print("No pop-up window found or it was already closed.")

        sb.wait_for_element_visible("#mosaic-provider-jobcards ul")
        job_cards = sb.find_elements("div.cardOutline.tapItem")
        print(f"Found {len(job_cards)} job cards to process.")

        for i, card in enumerate(job_cards):
            print(f"\nProcessing job card {i+1}/{len(job_cards)}...")
            
            # This dictionary will hold the raw scraped data
            scraped_data = {}
            source_url = ""

            try:
                # Get the unique source URL for duplicate checking
                link_element = card.find_element("css selector", "a.jcs-JobTitle")
                relative_url = link_element.get_attribute('href')
                source_url = f"https://www.indeed.com{relative_url}"
                
                # Use a reliable JavaScript click to avoid "element not interactable" errors
                sb.driver.execute_script("arguments[0].click();", card)
                
                sb.wait_for_element_visible("div.jobsearch-JobInfoHeader-title-container", timeout=10)
                time.sleep(0.5)

                # Scrape raw data
                title_raw = get_text_if_exists(sb, "div.jobsearch-JobInfoHeader-title-container h2")
                scraped_data['title'] = title_raw.split('\n')[0].strip() if title_raw else "Not listed"
                
                print(f"Scraping details for: {scraped_data['title']}")
                
                scraped_data['company'] = get_text_if_exists(sb, 'div[data-testid="inlineHeader-companyName"]')
                scraped_data['location_raw'] = get_text_if_exists(sb, 'div[data-testid="inlineHeader-companyLocation"]')
                scraped_data['salary_text'] = get_text_if_exists(sb, '#salaryInfoAndJobType')
                scraped_data['description'] = get_text_if_exists(sb, "#jobDescriptionText")

                # Process and Clean the Scraped Data for DB Insertion 
                
                # Parse Location
                location_parts = scraped_data['location_raw'].split(', ')
                city = location_parts[0].strip() if location_parts else "N/A"
                state = location_parts[1].strip().split('•')[0] if len(location_parts) > 1 else "GA"

                # Parse Salary and Job Type
                salary, job_type = "Not provided", "Not specified"
                if scraped_data['salary_text']:
                    if '$' in scraped_data['salary_text']:
                        parts = [p.strip() for p in scraped_data['salary_text'].split(' - ')]
                        salary = parts[0]
                        if len(parts) > 1:
                            job_type = parts[1]
                    else:
                        job_type = scraped_data['salary_text']

                # Prepare the final record for the database
                db_record = {
                    'job_title': scraped_data['title'],
                    'firm_name': scraped_data['company'],
                    'city': city,
                    'state': state,
                    'area_of_law': detect_area(scraped_data['description']),
                    'description': scraped_data['description'],
                    'salary': salary,
                    'deadline': find_deadline(scraped_data['description']),
                    'mentions_1l': mentions_1l(scraped_data['title'] + " " + scraped_data['description']),
                    'source_url': source_url
                }
                
                # Save the processed record to the database
                save_job_to_db(db_record)

            except Exception as e:
                print(f"  -> ERROR: Could not process this job card. Skipping. Details: {e}")
                continue

if __name__ == "__main__":
    # Initialize the database and table
    init_db()
    
    # Run the scraper and save the data
    scrape_and_save_jobs()
    
    print("\n--- SCRAPING AND SAVING COMPLETE ---")
    print(f"All found jobs have been processed and saved to '{DB_NAME}'.")