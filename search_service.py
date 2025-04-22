# search_service.py
import requests
import logging
import config

logger = logging.getLogger(__name__)

def search_google(search_term, api_key=config.GOOGLE_API_KEY, cse_id=config.GOOGLE_CSE_ID, num_results=config.SEARCH_DEPTH, site_filter=config.SITE_FILTER):
    """Performs a Google Custom Search."""
    service_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_term,
        "key": api_key,
        "cx": cse_id,
        "num": num_results,
        "lr": "lang_fr",  # Préférence pour les résultats en français
        "gl": "tn"       
    }
    # Add site filter if specified
    if site_filter:
        params["siteSearch"] = site_filter
        params["siteSearchFilter"] = "i" # Include results from this site
        logger.info(f"Performing search for '{search_term}' with site filter: {site_filter}")
    else:
         logger.info(f"Performing search for '{search_term}'")

    try:
        response = requests.get(service_url, params=params, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
        results = response.json()

        if "items" not in results or not results["items"]:
            logger.warning(f"No search results found for term: '{search_term}' (Site filter: {site_filter})")
            # If site filter was active and failed, maybe try without it? (Optional)
            # if site_filter:
            #     logger.info(f"Retrying search for '{search_term}' without site filter.")
            #     return search_google(search_term, api_key, cse_id, num_results, site_filter=None)
            return []

        logger.info(f"Found {len(results['items'])} search results.")
        return results["items"] # Return the list of items

    except requests.exceptions.Timeout:
        logger.error(f"Google Search API request timed out for term: '{search_term}'")
        return []
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Google Search API HTTP error occurred: {http_err} - Response: {response.text}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Google Search API error occurred: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during search: {e}", exc_info=True)
        return []