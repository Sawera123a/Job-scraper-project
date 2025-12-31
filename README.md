## 1L Summer Law Jobs Scraper & API

## Sources
Indeed.com (public & free) – easy to access and has most 1L summer law listings.

### Tech Stack
- Python
- SeleniumBase
- SQLite
- FastAPI

## 1L Definition

A job is considered a 1L position 
if the job title or description explicitly mentions “1L” or “first-year law student,” or 
if it is listed as a summer law internship.

## How to Run
pip install fastapi uvicorn seleniumbase beautifulsoup4
python scraper.py
uvicorn api:app --reload

## API Example

Fetch jobs:
http://127.0.0.1:8000/jobs?page=1&limit=50