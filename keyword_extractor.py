# keyword_extractor.py
import spacy
import logging
import config

logger = logging.getLogger(__name__)

try:
    # Try loading the specified model
    nlp = spacy.load(config.SPACY_MODEL, disable=["parser", "ner"]) # Disable unused pipes for speed
    logger.info(f"spaCy model '{config.SPACY_MODEL}' loaded successfully.")
except OSError:
    # If loading fails, try downloading it (useful in Docker setup)
    logger.warning(f"spaCy model '{config.SPACY_MODEL}' not found. Attempting download...")
    try:
        spacy.cli.download(config.SPACY_MODEL)
        nlp = spacy.load(config.SPACY_MODEL, disable=["parser", "ner"])
        logger.info(f"spaCy model '{config.SPACY_MODEL}' downloaded and loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download or load spaCy model '{config.SPACY_MODEL}': {e}", exc_info=True)
        nlp = None # Indicate failure
except Exception as e:
     logger.error(f"An unexpected error occurred loading spaCy model: {e}", exc_info=True)
     nlp = None

def extract_keywords_spacy(text):
    """Extracts potential keywords (nouns, proper nouns) using spaCy."""
    if not nlp:
        logger.error("spaCy model not available. Cannot extract keywords.")
        # Fallback: return raw text or simple split
        return text

    # Add "SupCom" as a base keyword if not present
    base_keyword = "SupCom"
    keywords = [base_keyword]

    # Process the text
    doc = nlp(text)

    # Extract Nouns and Proper Nouns, excluding the base keyword if already added
    extracted = [
        token.lemma_.lower() for token in doc # Use lemma for base form
        if token.pos_ in ["NOUN", "PROPN"] and token.text.lower() != base_keyword.lower() and not token.is_stop
    ]

    # Combine and limit keywords (e.g., base + top 3 extracted)
    keywords.extend(extracted)
    final_keywords = list(dict.fromkeys(keywords)) # Remove duplicates while preserving order
    keyword_str = " ".join(final_keywords[:4]) # Limit to ~4 keywords

    logger.info(f"Extracted spaCy keywords for '{text}': '{keyword_str}'")
    return keyword_str