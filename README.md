## 1L Summer Law Jobs Scraper & API

## Sources
Indeed.com (public & free) – easy to access and has most 1L summer law listings.

### Tech Stack
- Python
- SeleniumBase
- SQLite
- FastAPI

## 1L Definition

Job ko 1L mana gaya agar:
Title ya description me "1L" ya "first-year law student" likha ho
Ya summer law internship ho

## How to Run
pip install fastapi uvicorn seleniumbase beautifulsoup4
python scraper.py
uvicorn api:app --reload

## API Example

Fetch jobs:
http://127.0.0.1:8000/jobs?page=1&limit=50

## Limitations

Area of law detection is heuristic-based and may not always be accurate.
Salary and application deadlines are often missing.
The scraper fetches jobs only from Indeed.com.
The API serves only already scraped data; it does not perform real-time scraping.

## Possible Improvements

Support and job sources
Better area-of-law detection using NLP
Filters for salary, deadline, firm size, etc.
API authentication