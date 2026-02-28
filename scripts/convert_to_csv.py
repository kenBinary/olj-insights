"""
convert_to_csv.py
-----------------
Run from the project root with:

    py -m scripts.convert_to_csv

Reads all records from the 'jobs' table in data/olj-jobs-cleaned.db,
extracts skills and date_updated from the raw_text HTML, and writes a
cleaned CSV file with the columns:

    id, job_id, title, work_type, salary, hours_per_week, date_updated, skills
"""

import csv
import sqlite3
from pathlib import Path

from bs4 import BeautifulSoup

from utils.date_extract import extract_date_updated
from utils.skill_extract import extract_skills_from_html

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "olj-jobs-cleaned.db"
OUTPUT_CSV = PROJECT_ROOT / "data" / "olj-jobs-cleaned.csv"

# ---------------------------------------------------------------------------
# CSV columns
# ---------------------------------------------------------------------------
FIELDNAMES = [
    "id",
    "job_id",
    "title",
    "work_type",
    "salary",
    "hours_per_week",
    "date_updated",
    "skills",
]


def main() -> None:
    # Ensure the output directory exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, job_id, title, work_type, salary, hours_per_week, raw_text FROM olj_jobs"
    )
    rows = cursor.fetchall()
    conn.close()

    print(f"Found {len(rows)} record(s). Processing…")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()

        for i, row in enumerate(rows, start=1):
            raw_text: str = row["raw_text"] or ""

            # --- Extract date_updated ---
            # extract_date_updated expects a BeautifulSoup object
            soup = BeautifulSoup(raw_text, "html.parser")
            date_updated = extract_date_updated(soup)

            # --- Extract skills ---
            # extract_skills_from_html expects the raw HTML string
            skills = extract_skills_from_html(raw_text)

            writer.writerow(
                {
                    "id": row["id"],
                    "job_id": row["job_id"],
                    "title": row["title"],
                    "work_type": row["work_type"],
                    "salary": row["salary"],
                    "hours_per_week": row["hours_per_week"],
                    "date_updated": date_updated,
                    "skills": skills,
                }
            )

            if i % 100 == 0:
                print(f"  Processed {i}/{len(rows)} records…")

    print(f"\nDone! CSV written to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
