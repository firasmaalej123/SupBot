# SupBot 🤖💬

SupBot is an LLM and RAG-powered chatbot tailored to answer user questions using a combination of custom knowledge bases and live web search. Originally designed for SUP'COM, it can be easily personalized for any institution, company, or specific domain.

---

## 🔧 Features

- ✅ Accepts natural language questions from users
- 🌐 Searches for the most relevant information using **Google Custom Search API**
- 🧠 Retrieves and matches content from a local **summaries database** (`summaries.db`) for SUP'COM-related pages
- 🕸️ If not found locally, performs a **live web search** and retrieves summaries
- 🧩 Combines all gathered content to generate accurate answers using an **LLM (HuggingFace or OpenAI-based)**
- 🔄 Easily customizable for other organizations or knowledge domains

---

## 🧠 How it Works

1. User inputs a question.
2. The bot uses **Google CSE** to fetch the top 10 most relevant links.
3. It checks each link against a local `summaries.db`.
4. If content isn't found, it performs a live scrape + summarization.
5. Finally, it uses a **language model** (LLM) to generate an answer using RAG (Retrieval-Augmented Generation).

---

## 🔑 Prerequisites

You will need API keys/tokens for the following:
- `GOOGLE_API_KEY` – Google Search API Key
- `GOOGLE_CSE_ID` – Google Custom Search Engine ID
- `HF_TOKEN` – HuggingFace token (or OpenAI key if used)

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/firasmaalej123/SupBot.git
cd SupBot
### 2. create .env file with your credentials
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
HF_TOKEN=your_huggingface_token
### 3. install requirements
### 4. run the front-end and the back-end
python app.py
streamlit run streamlit_app.py

