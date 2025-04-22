# web_scraper.py
import requests
from bs4 import BeautifulSoup
import logging
import config

logger = logging.getLogger(__name__)

def retrieve_content(url):
    """Retrieves and cleans text content from a given URL."""
    logger.info(f"Attempting to retrieve content from: {url}")
    try:
        response = requests.get(
            url,
            headers=config.SCRAPE_HEADERS,
            timeout=config.SCRAPE_TIMEOUT
        )
        response.raise_for_status() # Check for HTTP errors

        # Check content type - basic check for HTML
        content_type = response.headers.get('content-type', '').lower()
        if 'html' not in content_type:
            logger.warning(f"Skipping non-HTML content ({content_type}) at URL: {url}")
            return None

        # Use 'html.parser' for robustness, consider 'lxml' if installed for speed
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose() # Remove tags and their content

        # Get text, separated by spaces, and strip extra whitespace
        text = soup.get_text(separator=" ", strip=True)

        # Limit the amount of text processed further
        max_chars = config.SCRAPE_MAX_TOKENS * 4 # Rough estimate
        if len(text) > max_chars:
             logger.info(f"Truncating content from {url} to {max_chars} characters.")
             text = text[:max_chars]

        logger.info(f"Successfully retrieved and cleaned content from: {url} (Length: {len(text)} chars)")
        return text

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while retrieving content from {url}")
        return None
    except requests.exceptions.HTTPError as http_err:
        # Log common errors differently if needed (e.g., 404 Not Found, 403 Forbidden)
        logger.error(f"HTTP error retrieving {url}: {http_err}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve content from {url}: {e}", exc_info=True)
        return None
    except Exception as e:
         logger.error(f"An unexpected error occurred during scraping {url}: {e}", exc_info=True)
         return None