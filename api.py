from fastapi import FastAPI
import sqlite3

DB_NAME = "jobs.db"

app = FastAPI(title="1L Summer Law Jobs API")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def root():
    return {"message": "API is running"}


@app.get("/jobs")
def get_jobs(page: int = 1, limit: int = 50, keyword: str = None, city: str = None):
    offset = (page - 1) * limit

    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT job_title, firm_name, city, area_of_law,
               description, mentions_1l, source_url
        FROM jobs
        WHERE 1=1
    """
    params = []

    if keyword:
        query += " AND (job_title LIKE ? OR description LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    return {
        "page": page,
        "count": len(rows),
        "jobs": [dict(r) for r in rows]
    }
