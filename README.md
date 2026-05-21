# PDF Analyser

[![Live](https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge)](https://analyser-for-pdf.streamlit.app/)
[![App](https://img.shields.io/badge/Open%20App-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://analyser-for-pdf.streamlit.app/)


---

## What It Does

Upload a PDF and the app will:

- **Parse and chunk** the document with overlap-aware recursive splitting
- **Generate an AI report** summarizing the document's topic and key points
- **Let you chat** with the document — ask anything, get context-aware answers
- **Remember conversation history** using a summarization system so the model never gets overloaded
- **Better Mode** — toggle on for smarter, deeper answers on complex questions

---

## Better Mode

By default the app runs in standard mode — one retrieval pass, fast answers.

Toggle **Better Mode** on in the sidebar when:
- The document is long or dense
- Your question needs information spread across multiple sections
- The standard answer feels incomplete

When Better Mode is on, the model first checks if the retrieved chunks have enough context. If not, it generates targeted follow-up queries, retrieves additional chunks, then answers using the combined context. Slower but significantly more accurate on hard questions.

---

## How It Works

```
PDF Upload
    ↓
Recursive Chunking (500 char chunks, 50 char overlap)
    ↓
BGE Embeddings (BAAI/bge-base-en-v1.5) + FAISS Index
    ↓
AI Report Generation (top 5 chunks → Gemini)
    ↓
Chat Loop (Standard):
    Question → Embed → Retrieve Top-5 Chunks → Gemini → Answer

Chat Loop (Better Mode):
    Question → Embed → Retrieve Chunks → Gemini checks if enough context
        → If yes: Answer directly
        → If no:  Generate sub-queries → Retrieve more chunks → Answer with full context

Each turn summarized → LLM history stays lean regardless of conversation length
```

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Groq llama-3.3-70b-versatile |
| Embeddings | `BAAI/bge-base-en-v1.5` via sentence-transformers |
| Vector Search | FAISS (IndexFlatIP) |
| PDF Parsing | pdfplumber |
| Deployment | Streamlit Community Cloud |

---

## Requirements

```
streamlit
sentence-transformers
numpy
pdfplumber
python-dotenv
faiss-cpu
groq
```

---

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/AliAkbar4025/PDF-Analyser
cd PDF-Analyser
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your API key**

Create a `.env` file:
```
GROQ_API_KEY=your_key_here
```

Get your key from [Groq](https://console.groq.com/keys)

**4. Run**
```bash
streamlit run app.py
```

---

## Deployment

Deployed on Streamlit Community Cloud. API key stored as a Streamlit secret under `GROQ_API_KEY`.

---

## Roadmap

- [ ] Multi-PDF support
- [ ] Export chat as PDF
- [ ] Support for scanned PDFs (OCR)
- [ ] Streaming responses for real-time output
- [ ] Better Mode optimization — reduce API calls via batched sub-query retrieval
- [ ] Better Mode call counter — show user how many calls a question used