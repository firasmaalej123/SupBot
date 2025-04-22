# app.py
# **** ADDED IMPORTS ****
from flask import Flask, request, jsonify, Response, stream_with_context
# **********************
import logging
import config
from chatbot_logic import process_user_query
import traceback # For detailed error logging

# Configure Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
# Use Flask's logger or a custom one that integrates with Gunicorn/Supervisor
logger = logging.getLogger("gunicorn.error" if __name__ != '__main__' else __name__)


# Eagerly initialize LLM service on startup
try:
    from llm_service import get_llm_service
    get_llm_service() # Ensure initialization happens
    logger.info("LLM Service initialized successfully for Flask app.")
except Exception as e:
    logger.critical(f"CRITICAL ERROR: Failed to initialize LLM Service: {e}", exc_info=True)
    # Consider exiting if model loading fails critically
    # raise SystemExit("Failed to load model, exiting.")


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    API endpoint for chat. Supports streaming responses.
    Expects JSON: {'query': 'user question here'}
    Returns either:
        - Non-streaming: JSON {'response': 'chatbot answer here'} (if stream=false requested, though not implemented in client yet)
        - Streaming: text/plain stream of tokens
    """
    if not request.is_json:
        logger.warning("Received non-JSON request")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_query = data.get('query')

    if not user_query:
        logger.warning("Received request with missing 'query' field")
        return jsonify({"error": "Missing 'query' in request body"}), 400

    logger.info(f"Received query via API: {user_query}")

    try:
        # Always request stream=True from the logic layer for this endpoint
        response_generator = process_user_query(user_query, stream=True)

        # Define the streaming generator function for Flask
        def generate_flask_stream():
            try:
                for token in response_generator:
                    # logger.debug(f"Streaming token: {token}") # Verbose logging if needed
                    yield token
            except Exception as e:
                 logger.error(f"Error during response generation stream in Flask: {e}\n{traceback.format_exc()}")
                 yield f"\n\n[STREAM ERROR: {e}]" # Send error within the stream

        # Return the streaming response
        # Use text/plain; Streamlit's write_stream handles chunking/display well.
        # Using text/event-stream adds complexity not needed here yet.
        return Response(stream_with_context(generate_flask_stream()), mimetype='text/plain')

    except Exception as e:
        # Catch errors *before* starting the stream if possible
        logger.error(f"An unexpected error occurred processing query '{user_query}' before streaming: {e}\n{traceback.format_exc()}", exc_info=True)
        # Return a non-streaming error response
        return jsonify({"error": f"An internal server error occurred before streaming could start: {e}"}), 500

if __name__ == '__main__':
    # Run with Flask's built-in server for local debugging ( Gunicorn is used in Docker)
    # Note: Flask's dev server might not be ideal for testing robust streaming under load.
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False, threaded=True) # threaded=True might help with streaming