# 🏥 Medical LLM App (Voice/Text Input with Online/Offline Modes)

This is a powerful and privacy-conscious medical assistant app that uses both **cloud-based** and **offline** AI models to answer user questions via voice or text. The app supports **Hindi and English** output, uses **Claude 3.5 via AWS Bedrock** for high-quality online answers, and falls back to **BioGPT + offline TTS/STT** for offline use.

---

## ✅ How It Works (Working First)

- The app accepts **voice or text input** and returns responses via **voice (TTS)** or **text**.
- With an **internet connection**, it uses:
  - 🎙️ **OpenAI Whisper** (STT)
  - 🤖 **Claude 3.5 via AWS Bedrock** for responses
  - 📚 **RAG** (Retrieval Augmented Generation) with **Pinecone**
  - 🗣️ **Amazon Polly** for voice output
  - 📝 **Textract & Translate** (for OCR and multilingual support)

- Without internet, it runs **completely offline** using:
  - 🧠 **BioGPT (Q5_K_M GGUF)** for LLM responses
  - 🧾 **easyOCR** (OCR)
  - 🗣️ **Glow-TTS** (TTS)
  - 🧏‍♂️ **faster-whisper-base.en** (STT)

- The system:
  - Uses **chat history** as part of the context to improve response quality.
  - Saves conversations locally by **session**.
  - Can analyze **uploaded files or images** (OCR + language detection + summarization).
  - Automatically chooses online or offline mode depending on connectivity.

---

## 🛠️ Technologies Used

| Area         | Online Tools                              | Offline Tools                             |
|--------------|-------------------------------------------|-------------------------------------------|
| LLM          | Claude 3.5 (AWS Bedrock)                  | BioGPT (Q5_K_M, GGUF via llama.cpp)       |
| STT          | OpenAI Whisper API                        | faster-whisper-base.en                    |
| TTS          | Amazon Polly                              | Glow-TTS                                  |
| OCR          | AWS Textract                              | easyOCR                                   |
| RAG          | Pinecone (Free Tier)                      | Local fallback context only               |
| Language     | AWS Translate / Langdetect                | Langdetect                                 |
| Chat History | File-based JSON session storage           | Same                                       |
| API Backend  | Flask + CORS                              | Flask                                      |
| Frontend     | React (Voice UI, file input, etc.)        | Same                                       |

---

## 📦 Datasets Used for RAG

The vector search backend is populated using the following medical QA datasets:

1. **PubMedQA** (`qiaojin/PubMedQA`)
   - Both `pqa_labeled` and `pqa_unlabeled` versions
   - Used `final_decision`, `context`, and `long_answer` fields

2. **MedQuad** (`keivalya/MedQuad-MedicalQnADataset`)
   - Includes curated question-answer pairs from multiple medical sources

### Embedding Model
- `all-MiniLM-L6-v2` via Hugging Face
- Sentences chunked, embedded, and upserted into Pinecone vector DB

---

## 🧠 Model Metadata (YAML in Markdown)

```yaml
license: apache-2.0
tags:
  - medical
  - RAG
  - offline
  - whisper
  - bedrock
  - biogpt
  - TTS
  - STT
  - Hindi
datasets:
  - qiaojin/PubMedQA
  - keivalya/MedQuad-MedicalQnADataset
language:
  - en
  - hi
model:
  - BioGPT Q5_K_M GGUF
  - Claude 3.5 (Bedrock)
  - all-MiniLM-L6-v2 (embeddings)
stt:
  - OpenAI Whisper API
  - faster-whisper-base.en
tts:
  - Amazon Polly
  - Glow-TTS
ocr:
  - AWS Textract
  - easyOCR
vector_store:
  - Pinecone (free-tier)
api:
  - Flask (backend)
  - React (frontend)
