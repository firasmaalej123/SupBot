# llm_service.py
import torch
# **** ADDED IMPORTS ****
from threading import Thread
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig, TextIteratorStreamer
# **********************
from huggingface_hub import login
import logging
import time # Added for potential delays if needed
from threading import Lock
import config # Use our config file

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model_name=config.MODEL_NAME, device=config.DEVICE, dtype=config.DTYPE):
        self.model_name = model_name
        self.device = device
        self.dtype = dtype
        self.tokenizer = None
        self.model = None
        self.generation_config = None
        self._load_model()
        self.generate_lock = Lock()
    def _login_huggingface(self):
        try:
                    login(token=config.HF_TOKEN)
                    logger.info("Successfully logged into Hugging Face Hub.")
        except Exception as e:
                    logger.error(f"Hugging Face login failed: {e}. Check HF_TOKEN.", exc_info=True)
                    # Depending on the model, login might not be strictly required if it's public,
                    # but it's good practice for private models or rate limits.
                    # raise ConnectionError("Hugging Face login failed.") from e        pass # Placeholder

    def _load_model(self):
        # ... (keep existing code for login, tokenizer, model loading) ...
        self._login_huggingface()
        try:
            logger.info(f"Loading tokenizer: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            if self.tokenizer.pad_token_id is None:
                logger.warning("Tokenizer does not have a pad_token_id. Setting to eos_token_id.")
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            logger.info(f"Loading model: {self.model_name} to device: {self.device} with dtype: {self.dtype}")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=self.dtype,
                device_map="auto" # Let accelerate handle device placement
            )
            logger.info("Model loaded successfully.")

            self.generation_config = GenerationConfig.from_pretrained(self.model_name)
            self.generation_config.pad_token_id = self.tokenizer.pad_token_id
            logger.info("LLM Service initialized.")

        except Exception as e:
            logger.error(f"Failed to load model or tokenizer: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize LLM Service: {e}") from e


    # **** MODIFIED INTERNAL GENERATION FUNCTION ****
    def _generate_stream(self, messages, generation_config):
        """Internal generator function for streaming tokens."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model or tokenizer not loaded.")

        try:
            streamer = TextIteratorStreamer(
                self.tokenizer, skip_prompt=True, skip_special_tokens=True
            )

            input_tensor = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt"
            ).to(self.model.device)

            generation_kwargs = dict(
                input_ids=input_tensor,
                generation_config=generation_config,
                streamer=streamer,
                # You might need attention_mask depending on model/padding, but often okay with device_map="auto"
                # attention_mask=input_tensor.ne(self.tokenizer.pad_token_id)
            )
            with self.generate_lock:
                # Run generation in a separate thread for streaming
                thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
                thread.start()

            # Yield tokens as they become available
            logger.info("Starting token stream generation...")
            for new_text in streamer:
                yield new_text
            logger.info("Token stream generation finished.")

            thread.join() # Ensure thread finishes, though streamer should handle it

        except Exception as e:
            logger.error(f"Error during LLM stream generation: {e}", exc_info=True)
            yield f"Error generating response stream: {e}" # Yield error message as part of the stream

    # --- Keep non-streaming version if needed for other tasks (like summarization) ---
    def _generate_non_stream(self, messages, generation_config):
         # ... (original _generate logic without streamer) ...
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model or tokenizer not loaded.")
        try:
            input_tensor = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt"
            ).to(self.model.device)

            with torch.inference_mode():
                outputs = self.model.generate(
                    input_ids=input_tensor,
                    generation_config=generation_config,
                )
            response_ids = outputs[0][input_tensor.shape[1]:]
            result = self.tokenizer.decode(response_ids, skip_special_tokens=True).strip()
            return result
        except Exception as e:
            logger.error(f"Error during LLM non-stream generation: {e}", exc_info=True)
            return f"Error generating response: {e}"


    # --- Summarization still uses non-streaming ---
    def summarize_content(self, content, search_term, user_query):
        """Summarizes web content using the summarizer from config.py."""
        logger.info(f"Summarizing content for query: '{user_query}' related to '{search_term}'")

        try:
            # Prepare the prompt
            prompt = config.SUMMARIZATION_PROMPT_TEMPLATE.format(
                search_term=search_term,
                user_query=user_query,
                character_limit=config.SUMMARY_CHARACTER_LIMIT
            )
            
            # Combine prompt with content
            input_text = f"{prompt}\n\n{content[:config.SCRAPE_MAX_TOKENS * 5]}"
            
            # Use the summarizer's tokenizer to count tokens
            summarizer_tokenizer = config.summarizer.tokenizer
            max_input_tokens = 1024  # distilbart-cnn-12-6 max length
            tokens = summarizer_tokenizer(input_text, truncation=True, max_length=max_input_tokens, return_tensors="pt")
            truncated_text = summarizer_tokenizer.decode(tokens["input_ids"][0], skip_special_tokens=True)
            
            logger.info(f"Input truncated to {len(tokens['input_ids'][0])} tokens")

            # Use distilbart-cnn-12-6 from config.summarizer
            summary = config.summarizer(
                truncated_text,
                max_length=config.SUMMARY_MAX_NEW_TOKENS,
                min_length=30,
                do_sample=True,
                temperature=config.SUMMARY_TEMPERATURE,
                top_p=config.SUMMARY_TOP_P,
                num_beams=4,
                no_repeat_ngram_size=3
            )[0]['summary_text']

            summary = summary.strip()
            if not summary:
                logger.warning(f"Summarization failed for query '{user_query}'.")
                return None
            logger.info(f"Generated summary (first 100 chars): {summary[:100]}...")
            return summary[:int(config.SUMMARY_CHARACTER_LIMIT * 1.2)]

        except Exception as e:
            logger.error(f"Error during summarization: {e}", exc_info=True)
            return None


    # **** MODIFIED TO SUPPORT STREAMING ****
    def generate_final_response(self, user_query, context_results, stream=False):
        """
        Generates the final chatbot response based on summarized search results.
        Can either return the full response string or yield tokens via a generator.
        """
        logger.info(f"Generating final response for query: '{user_query}' (Stream={stream})")

        # Format context data and prepare source links
        context_str = ""
        source_links_list = []
        if context_results:
            for idx, result in enumerate(context_results):
                context_str += f"[{idx + 1}] Source: {result.get('link', 'N/A')}\n"
                context_str += f"   Title: {result.get('title', 'N/A')}\n"
                context_str += f"   Summary: {result.get('Summary', 'N/A')}\n\n"
                source_links_list.append(f"[{idx + 1}] {result.get('link', 'N/A')}")
            # Format the sources string to be appended *after* generation if needed
            sources_footer = "\n\nSources:\n" + "\n".join(source_links_list) if source_links_list else ""
        else:
            context_str = "Aucune information pertinente trouvée dans les recherches."
            sources_footer = "" # No sources if no results
            logger.warning("No context results provided for final response generation.")

        # Create generation config
        final_gen_config = GenerationConfig.from_dict(self.generation_config.to_dict())
        final_gen_config.max_new_tokens = config.DEFAULT_MAX_NEW_TOKENS
        final_gen_config.temperature = config.DEFAULT_TEMPERATURE
        final_gen_config.top_p = config.DEFAULT_TOP_P
        final_gen_config.do_sample = True
        final_gen_config.use_cache = True # Cache is generally okay with streaming too

        # Modify prompt slightly to encourage inclusion of sources *during* generation
        # but we will still append the footer defensively.
        system_prompt = config.FINAL_RESPONSE_PROMPT_TEMPLATE.format(
            user_query=user_query,
            context_data=context_str
        )
        # Remove the explicit "List sources at the end" instruction if we append manually
        system_prompt = system_prompt.replace("Listez les sources à la fin comme suit : Sources : [1] lien, [2] lien, etc.",
                                              "Citez vos sources DANS LE TEXTE en utilisant [numéro].")

        messages = [{"role": "system", "content": system_prompt}]

        if stream:
            # Return a generator function that yields tokens AND the sources footer
            def response_generator():
                full_response_text = ""
                # Yield tokens from the LLM stream
                token_stream = self._generate_stream(messages, final_gen_config)
                for token in token_stream:
                    full_response_text += token
                    yield token
                # After the LLM stream is done, yield the sources footer
                # Defensive check: If LLM included "Sources:", don't add duplicates.
                if "Sources:" not in full_response_text[-len(sources_footer)-20:]: # Check near end
                    yield sources_footer
                logger.info("Final response stream complete.")

            return response_generator() # Return the generator iterator
        else:
            # Use non-streaming generation and append sources manually
            response = self._generate_non_stream(messages, final_gen_config)
            if "Sources:" not in response[-len(sources_footer)-20:]: # Check near end
                response += sources_footer
            logger.info("Final response generated (non-stream).")
            return response


# --- Instantiate the service (singleton pattern) ---
llm_service_instance = LLMService()

def get_llm_service():
    """Returns the singleton LLM service instance."""
    return llm_service_instance