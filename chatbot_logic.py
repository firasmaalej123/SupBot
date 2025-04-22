# chatbot_logic.py
import logging
import json
import time # Already imported
import config
from llm_service import get_llm_service
from search_service import search_google
from web_scraper import retrieve_content
from keyword_extractor import extract_keywords_spacy
import sqlite3

# Open the DB connection once before the loop

logger = logging.getLogger(__name__)

# **** MODIFIED TO SUPPORT STREAMING ****
def process_user_query(user_query, stream=False):
    """
    Processes the user query through the RAG pipeline.
    Returns a string (full response) or a generator (token stream).
    """
    start_time = time.time()
    logger.info(f"--- Starting processing for query: '{user_query}' (Stream={stream}) ---")

    # 1. Extract Keywords
    search_terms = extract_keywords_spacy(user_query)
    if not search_terms:
        logger.error("Failed to generate search terms.")
        # Need to handle this for streaming too - maybe yield an error message?
        if stream:
            def error_gen(): yield "Désolé, je n'ai pas pu déterminer les termes de recherche."
            return error_gen()
        else:
            return "Désolé, je n'ai pas pu déterminer les termes de recherche pour votre requête."

    logger.info(f"Using search terms: {search_terms}")

    # 2. Search Google
    search_items = search_google(search_terms)
    if not search_items:
        logger.warning("No search results returned from Google Search.")
        if stream:
            def error_gen(): yield "Désolé, aucun résultat de recherche pertinent trouvé."
            return error_gen()
        else:
            return "Désolé, je n'ai trouvé aucun résultat de recherche pertinent pour votre requête."

    # 3. Scrape & Summarize Results (Summarization itself remains non-streaming)
    processed_results = []
    llm = get_llm_service()
    summarization_limit = config.SEARCH_DEPTH

    for idx, item in enumerate(search_items[:summarization_limit]):
        item_start_time = time.time()
        url = item.get("link")
        title = item.get("title", "N/A")
        logger.info(f"Processing result {idx+1}/{len(search_items)}: {title} ({url})")

        if not url:
            continue
        conn = sqlite3.connect("summaries.db")
        cursor = conn.cursor()
    # Check if the URL exists in the database
        cursor.execute("SELECT summary FROM summaries WHERE url = ?", (url,))
        row = cursor.fetchone()

        if row:
            summary = row[0]
            logger.info(f"Found cached summary for URL: {url}")
        else:
            web_content = retrieve_content(url)
            if web_content is None:
                continue

        # Summarization uses the non-streaming method internally
            summary = llm.summarize_content(web_content, search_terms, user_query)

        # Save to DB if summary was generated
            
    
        item_end_time = time.time()

        if summary:
            processed_results.append({
                "order": idx + 1, "link": url, "title": title, "Summary": summary
            })
            logger.info(f"Successfully summarized result {idx+1} in {item_end_time - item_start_time:.2f} seconds.")
        else:
            logger.warning(f"Failed to summarize content for URL: {url}.")

# Close the connection when done
    conn.close()

    if not processed_results:
        logger.error("Failed to process any search results (scrape/summarize).")
        if stream:
            def error_gen(): yield "Désolé, impossible de traiter les résultats de recherche."
            return error_gen()
        else:
            return "Désolé, je n'ai pas pu traiter les résultats de recherche trouvés."

    logger.info(f"Processed {len(processed_results)} search results.")

    # 4. Generate Final Response (Potentially Streaming)
    # Pass the stream parameter here
    response_or_generator = llm.generate_final_response(user_query, processed_results, stream=stream)

    end_time = time.time()
    logger.info(f"--- Finished processing query in {end_time - start_time:.2f} seconds (Stream={stream}) ---")

    return response_or_generator # Return either the string or the generator