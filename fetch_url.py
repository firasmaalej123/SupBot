import sqlite3

def fetch_links_with_summary_and_date(db_path="summaries.db"):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Fetch URL, summary, and date
        c.execute("SELECT url, summary, date FROM summaries")
        results = c.fetchall()
        conn.close()

        return results

    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

# Example usage
records = fetch_links_with_summary_and_date()
for i, (url, summary, date) in enumerate(records, 1):
    print(f"\n--- Entry #{i} ---")
    print(f"URL: {url}")
    print(f"Date: {date}")
    print(f"Summary:\n{summary}")
