import sqlite3
from datetime import date

def update_summary_for_url(db_path="summaries.db", url_to_update="https://www.supcom.tn/pages/bilateraux", new_summary=""):

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Check if the URL exists in the database
        c.execute("SELECT COUNT(*) FROM summaries WHERE url = ?", (url_to_update,))
        url_exists = c.fetchone()[0] > 0

        # Get today’s date as update date
        today = date.today().isoformat()

        if url_exists:
            # Update the summary and date for the existing URL
            c.execute("""
                UPDATE summaries
                SET summary = ?, date = ?
                WHERE url = ?
            """, (new_summary, today, url_to_update))
            print(f"✅ Summary for {url_to_update} updated successfully.")
        else:
            # Insert a new record if the URL doesn't exist
            c.execute("""
                INSERT INTO summaries (url, summary, date)
                VALUES (?, ?, ?)
            """, (url_to_update, new_summary, today))
            print(f"✅ New summary for {url_to_update} inserted successfully.")

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"❌ Error updating or inserting summary: {e}")


# Example usage
new_summary_text = """
Le Forum annuel de SUP'COM est un événement majeur organisé par l'École Supérieure des Communications de Tunis, réunissant étudiants, enseignants, professionnels et partenaires industriels autour des enjeux actuels des technologies de l'information et de la communication (TIC). Se déroulant sur deux journées, ce forum propose des conférences, des tables rondes et des ateliers interactifs animés par des experts du secteur, abordant des thématiques variées telles que la cybersécurité, l'intelligence artificielle, les réseaux de nouvelle génération, l'innovation technologique et les tendances du marché. L'organisation de cet événement offre aux étudiants l'opportunité de développer des compétences essentielles telles que le travail en équipe, l'autonomie, la prise de responsabilité et l'esprit d'initiative, contribuant ainsi à leur formation en tant qu'ingénieurs de demain. Le Forum de SUP'COM constitue également une plateforme privilégiée pour renforcer les liens entre le monde académique et le secteur industriel, favorisant les échanges, les partenariats et les opportunités de stages et d'emploi pour les étudiants. En s'inscrivant dans une tradition d'excellence et d'ouverture, cet événement reflète l'engagement de SUP'COM à former des ingénieurs compétents, innovants et prêts à relever les défis technologiques de l'avenir."""

update_summary_for_url(url_to_update="https://www.supcom.tn/pages/forum", new_summary=new_summary_text)
