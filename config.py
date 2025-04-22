# config.py
import os
import torch
from dotenv import load_dotenv
import logging
from transformers import pipeline
# Load environment variables from .env file
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Secrets ---
HF_TOKEN = os.getenv("HF_TOKEN")
GOOGLE_API_KEY=os.getenv("GOOGLE_API")
GOOGLE_CSE_ID=os.getenv("CSE_ID")
if not all([HF_TOKEN, GOOGLE_API_KEY, GOOGLE_CSE_ID]):
    logger.warning("One or more API keys/tokens are missing in environment variables.")
    # You might want to raise an error here in a production setting
    # raise ValueError("Missing required environment variables for API keys/tokens.")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", tokenizer="sshleifer/distilbart-cnn-12-6")
# --- Model Configuration ---
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
logger.info(f"Using device: {DEVICE} with dtype: {DTYPE}")

# --- Generation Settings ---
# Default config for general responses
DEFAULT_MAX_NEW_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9

# Config for summarization (can be shorter)
SUMMARY_MAX_NEW_TOKENS = 512
SUMMARY_TEMPERATURE = 0.6
SUMMARY_TOP_P = 0.9
SUMMARY_CHARACTER_LIMIT = 1500 # Approx character limit for summaries

# Config for keyword generation (if using LLM method)
# KEYWORD_MAX_NEW_TOKENS = 50
# KEYWORD_DO_SAMPLE = False

# --- Search Configuration ---
SEARCH_DEPTH = 5 # Number of search results to fetch
SITE_FILTER = None # Optional: e.g., "supcom.tn" to restrict search

# --- Web Scraping Configuration ---
SCRAPE_MAX_TOKENS = 10000 # Max tokens to process from a webpage (approx)
SCRAPE_TIMEOUT = 15 # Seconds
SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# --- Spacy Configuration ---
SPACY_MODEL = "fr_core_news_sm"

# --- Deployment Settings ---
FLASK_HOST="0.0.0.0"
FLASK_PORT=10000
STREAMLIT_PORT=8501

# --- Prompts ---
SUMMARIZATION_PROMPT_TEMPLATE = (
    "Vous êtes un expert sur SupCom (École Supérieure des Communications de Tunis). "
    "Résumez le contenu web suivant pertinent pour les termes de recherche '{search_term}' et la requête initiale de l'utilisateur '{user_query}' "
    "en environ {character_limit} caractères ou moins. Concentrez-vous sur l'extraction des détails clés spécifiquement liés à SupCom "
    "(par exemple, programmes, admissions, recherche, contacts, événements). "
    "Éliminez les balises HTML, les menus de navigation non pertinents, les pieds de page génériques et le contenu promotionnel excessif. "
    "Produisez un résumé concis et informatif sous forme de paragraphe unique. "
    "Évitez d'inclure des informations non pertinentes ou spéculatives."
)

FINAL_RESPONSE_PROMPT_TEMPLATE = (
    "Vous êtes un assistant expert sur SupCom (École Supérieure des Communications de Tunis), nommé SupBot. "
    "En vous basant UNIQUEMENT sur les informations contextuelles fournies ci-dessous (résumés de recherche web), "
    "répondez de manière complète et utile à la question de l'utilisateur : **'{user_query}'**. "
    "Synthétisez les détails clés des différents résumés fournis, en privilégiant les informations les plus pertinentes pour la question. "
    "Structurez votre réponse de manière claire et facile à lire (utilisez des paragraphes, éventuellement des listes si approprié). "
    "Citez vos sources à la fin de chaque information pertinente en utilisant le format [numéro] correspondant à l'ordre des résultats fournis dans le contexte. "
    "Si les informations contextuelles fournies ne permettent pas de répondre à la question, répondez par : "
    "'Désolé, les informations trouvées lors de la recherche ne permettent pas de répondre précisément à votre question.' et n'inventez rien. "
    "Terminez TOUJOURS votre réponse en listant toutes les sources utilisées, numérotées comme suit : \nSources:\n[1] lien1\n[2] lien2\netc.\n\n"
    "CONTEXTE (Résumés de recherche web) :\n"
    "{context_data}"
)

# --- Keyword Generation Prompt (if using LLM method) ---
# KEYWORD_SYSTEM_PROMPT = (
#     "Vous êtes un générateur de termes de recherche spécialisé dans SupCom (École Supérieure des Communications de Tunis). "
#     "Analysez la requête de l'utilisateur et générez exactement 3 à 4 termes de recherche Google concis et très spécifiques à SupCom. "
#     "Concentrez-vous sur les mots-clés essentiels liés à SupCom (par exemple, noms de programmes, conditions d'admission, projets de recherche spécifiques, noms de laboratoires, procédures d'inscription). "
#     "Produisez UNIQUEMENT les termes, séparés par des espaces, sans aucune explication, ponctuation superflue ou texte supplémentaire. "
#     "Exemples :\n"
#     "Requête : 'quels sont les programmes de master à SupCom' -> 'SupCom master programmes admission'\n"
#     "Requête : 'recherche en réseaux à SupCom' -> 'SupCom recherche réseaux laboratoire LACS'\n"
#     "Requête : 'comment s'inscrire au cycle ingénieur' -> 'SupCom inscription ingénieur concours exigences'"
# )