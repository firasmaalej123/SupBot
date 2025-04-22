# streamlit_app.py
import streamlit as st
import requests
import logging
import time
import config # Import config to potentially get API URL

# Setup logger for Streamlit (optional but good practice)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Define the Flask API URL (ensure this points correctly, especially in Docker)
# If running docker-compose, service name 'flask' on port 5000 might be http://flask:5000/chat
# If running single docker container via supervisor, localhost should work inside container network
# If running locally:
FLASK_API_URL = f"http://localhost:{config.FLASK_PORT}/chat"
# Double-check this URL based on your deployment method (Docker vs Local)
logger.info(f"Streamlit connecting to Flask API at: {FLASK_API_URL}")


st.set_page_config(page_title="SupCom Chatbot", layout="wide")

st.title("🎓 SupBot")
st.caption("Posez vos questions sur l'École Supérieure des Communications de Tunis (SupCom).")

# --- Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display prior messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"]) # Keep using markdown for existing messages

# --- User Input ---
user_query = st.chat_input("Votre question sur SupCom...")

if user_query:
    # Add user message to display and history
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # --- Get Bot Response using Streaming ---
    with st.chat_message("assistant"):
        start_time = time.time()
        full_response = "" # Variable to accumulate the full response for history

        try:
            logger.info(f"Sending query to Flask API for streaming: {FLASK_API_URL}")
            # Use stream=True with requests
            with requests.post(FLASK_API_URL, json={"query": user_query}, stream=True, timeout=1000) as api_response:
                api_response.raise_for_status() # Check for HTTP errors early

                # Use st.write_stream to display the content as it arrives
                # iter_content(decode_unicode=True) provides text chunks
                response_stream = api_response.iter_content(chunk_size=None, decode_unicode=True)

                # Display the stream and accumulate the full response
                full_response = st.write_stream(response_stream)

            end_time = time.time()
            processing_time = end_time - start_time
            logger.info(f"Finished streaming response in {processing_time:.2f} seconds.")

        except requests.exceptions.Timeout:
            logger.error("Request to Flask API timed out.")
            full_response = "Désolé, la requête a pris trop de temps. Veuillez réessayer."
            st.error(full_response) # Display error in chat
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Flask API: {e}", exc_info=True)
            status_code = e.response.status_code if e.response is not None else "N/A"
            full_response = f"Désolé, une erreur de connexion au backend s'est produite (Status: {status_code}). Détails : {e}"
            st.error(full_response) # Display error in chat
        except Exception as e:
            logger.error(f"An unexpected error occurred in Streamlit app during streaming: {e}", exc_info=True)
            full_response = "Désolé, une erreur inattendue s'est produite lors de l'affichage de la réponse."
            st.error(full_response) # Display error in chat

        # Add the *complete* bot response to history *after* the stream is finished
        if full_response: # Ensure we don't add empty messages on error
             st.session_state.messages.append({"role": "assistant", "content": full_response})
        # No need to manually update a placeholder as st.write_stream handles the display area

# Optional: Add a sidebar or footer
st.sidebar.info("Ce chatbot est en version bêta. Il utilise un modèle de langage (LLM) et une recherche dans le site web de SUPCOM pour répondre aux questions.")
st.sidebar.warning("Les réponses sont générées automatiquement. Elles peuvent être inexactes ou non à jour. Une vérification humaine est recommandée.")
st.sidebar.warning("la géneration de réponse peut prendre une minute.")
