import sqlite3

def delete_summary_for_url(db_path="summaries.db", url_to_delete="https://www.supcom.tn/pages/stages"):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Delete the row with the specific URL
        c.execute("DELETE FROM summaries WHERE url = ?", (url_to_delete,))

        conn.commit()

        # Check if any rows were deleted
        if c.rowcount > 0:
            print(f"✅ Row with URL {url_to_delete} deleted successfully.")
        else:
            print(f"❌ URL {url_to_delete} not found in the database.")

        conn.close()

    except Exception as e:
        print(f"❌ Error deleting row: {e}")

# Example usage
delete_summary_for_url(url_to_delete="https://www.supcom.tn/pages/theses-soutenues")
