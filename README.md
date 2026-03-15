# Medical LLM Application

A comprehensive healthcare assistant that leverages both cloud-based and offline artificial intelligence models to provide medical guidance through voice or text input. The application supports bilingual output in Hindi and English, employs Claude 3.5 via AWS Bedrock for online consultations, and incorporates BioGPT for offline functionality.

## Executive Summary

The Medical LLM Application prioritizes user privacy, data security, and uninterrupted availability regardless of internet connectivity. It combines state-of-the-art language models with medical knowledge bases to deliver accurate, contextual healthcare information through an intuitive interface.

## Key Features

- **Dual-Mode Operation**: Seamlessly switches between cloud-based and offline models based on connectivity
- **Multilingual Support**: Delivers responses in English and Hindi
- **Voice & Text Interface**: Accept queries and deliver answers via voice or text
- **Document Analysis**: Analyzes medical images and prescriptions using OCR
- **Contextual Intelligence**: Maintains chat history for improved response quality
- **Privacy-First Design**: Offline mode eliminates data transmission for sensitive queries
- **Auto Fallback**: Automatically detects and switches to offline mode when needed

## System Architecture

### Online Mode

When internet connectivity is available, the application leverages cloud-based services:

| Component | Technology |
|-----------|------------|
| Speech Recognition | OpenAI Whisper API |
| LLM Engine | Claude 3.5 (AWS Bedrock) |
| Knowledge Retrieval | Retrieval Augmented Generation (RAG) with Pinecone |
| Speech Synthesis | Amazon Polly |
| Optical Character Recognition | AWS Textract |
| Language Translation | AWS Translate |
| Chat History | File-based JSON session storage |

### Offline Mode

When internet connectivity is unavailable, the application operates independently using locally deployed models:

| Component | Technology |
|-----------|------------|
| Speech Recognition | Faster-Whisper (base.en model) |
| LLM Engine | BioGPT (Q5_K_M GGUF via llama.cpp) |
| Speech Synthesis | Glow-TTS |
| Optical Character Recognition | easyOCR |
| Knowledge Retrieval | Local fallback context |
| Language Detection | Langdetect |

## Knowledge Base

The application utilizes curated medical datasets for its Retrieval Augmented Generation (RAG) pipeline:

### Datasets

- **PubMedQA**: Large-scale medical question-answering dataset with labeled and unlabeled subsets
- **MedQuad**: Curated medical question-answer pairs from multiple medical sources

### Embedding & Retrieval

- Embedding Model: `all-MiniLM-L6-v2` (Hugging Face)
- Vector Database: Pinecone (Free Tier)
- Chunking Strategy: Sentence-level with vector storage

## Installation & Setup

The application consists of two parts:
- **Backend**: Flask (Python) API running on port 5000
- **Frontend**: React (Node.js) application running on port 3000

### Prerequisites

- **Python 3.8 or higher** (for Flask backend)
- **Node.js 14+** (for React frontend)
- AWS Bedrock access (for online mode)
- 4GB+ RAM recommended

### Step 1: Clone the Repository

```bash
git clone https://github.com/PranavShashidhara/MediAssist_AI.git
cd MediAssist_AI
```

### Step 2: Backend Setup (Flask)

The backend runs on Flask (Python framework) on port 5000.

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Backend - Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```ini
PINECONE_API_KEY=your-pinecone-api-key
OPENAI_API_KEY=your-openai-api-key
HF_TOKEN=your-hugging-face-token
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
```

### Step 4: Backend - Set API Keys in Configuration File

Before running the application, ensure the following environment variables are configured in your `.env` file:

```ini
HF_TOKEN=your-hugging-face-token
PINECONE_API_KEY=your-pinecone-api-key
OPENAI_API_KEY=your-openai-api-key
```

These will be loaded automatically when the Flask application starts.

**Note**: For offline mode, API keys can be left unconfigured. The system will automatically use local models.

### Step 5: Backend - Flask API Configuration

The Flask API is configured in `aws_medical_llm/main.py`. The application includes the following endpoints:

**Available Endpoints:**

- `POST /ask` — Handle text-based medical questions
  - Request: `{ "question": "...", "session_id": "...", "use_rag": true/false }`
  - Response: `{ "answer": "...", "audio_base64": "...", "mode": "online/offline" }`

- `POST /upload` — Upload and analyze medical documents
- `GET /history/<session_id>` — Retrieve conversation history
- `POST /translate` — Translate text between languages

The Flask app automatically:
- Detects internet connectivity
- Switches between online/offline modes
- Manages session history
- Handles language detection and translation

### Step 6: Backend - Download Offline Models (Optional)

For optimal offline performance, pre-download these models:

- **BioGPT Q5_K_M GGUF**: Place in `models/biogpt/`
- **Faster-Whisper (base.en)**: Auto-downloads on first use
- **Glow-TTS**: Auto-downloads on first use

Models will auto-download on first use if not pre-downloaded.

### Step 7: Backend - Start Flask Server

```bash
cd aws_medical_llm
python main.py
```

The Flask backend will start at `http://localhost:5000`

### Step 8: Frontend Setup (React)

The frontend runs on React (Node.js) on port 3000.

```bash
cd my-chat-app
npm install
npm start
```

The React application will run at `http://localhost:3000`

**Important**: Ensure the Flask backend is running (Step 7) before starting the frontend, as the React app communicates with the Flask API on `http://localhost:5000`.

## Running the Application

### Terminal 1: Start Flask Backend

```bash
# From project root
cd aws_medical_llm
python main.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Terminal 2: Start React Frontend

```bash
# From project root
cd my-chat-app
npm start
```

Expected output:
```
Compiled successfully!

You can now view my-chat-app in the browser.
  Local:            http://localhost:3000
```

Open `http://localhost:3000` in your browser to access the application.

## Usage

1. **Open the Application**
   - Navigate to `http://localhost:3000` in your web browser

2. **Submit Queries**
   - Use voice input by clicking the microphone icon
   - Type medical questions directly into the text field
   - Select your preferred language (English or Hindi)

3. **Upload Documents**
   - Upload medical images or prescriptions for OCR analysis
   - The system will extract text and provide relevant medical information

4. **Receive Responses**
   - Get answers via text output
   - Enable voice synthesis to listen to responses
   - Access chat history from previous sessions

5. **Offline Operation**
   - Disconnect from Wi-Fi to trigger offline mode
   - Application functionality remains unchanged
   - All conversations stored locally

## Technology Stack

| Area | Technology |
|------|-----------|
| Backend | Flask + Python |
| Frontend | React + JavaScript |
| Language Models | Claude 3.5 (Bedrock), BioGPT |
| Speech-to-Text | OpenAI Whisper, Faster-Whisper |
| Text-to-Speech | Amazon Polly, Glow-TTS |
| OCR | AWS Textract, easyOCR |
| Vector Search | Pinecone |
| Embeddings | all-MiniLM-L6-v2 |
| API Gateway | CORS-enabled Flask |
| Storage | Local JSON sessions |

## Security & Privacy

- **Privacy-Focused Design**: Offline mode eliminates data transmission for sensitive medical information
- **Local Storage**: Conversations stored locally without cloud dependency
- **Automatic Mode Switching**: Intelligent fallback ensures continuous operation
- **No Persistent Cloud Logging**: Medical queries processed locally when possible
- **Session-Based History**: Secure local session management

## API Endpoints

### Health Check
```bash
GET /health
```

### Process Query
```bash
POST /api/query
Content-Type: application/json

{
  "query": "What are the symptoms of diabetes?",
  "language": "en",
  "mode": "auto"
}
```

### Upload & Analyze Document
```bash
POST /api/analyze-document
Content-Type: multipart/form-data

file: <binary>
language: en
```

### Get Chat History
```bash
GET /api/history/<session_id>
```

## Project Structure

```
MediAssist_AI/
├── aws_medical_llm/                    # Backend Flask application
│   ├── main.py                         # Flask server entry point
│   ├── medical_llm.py                  # Medical LLM logic
│   ├── openai_whisper.py               # OpenAI Whisper integration
│   ├── textract_ocr.py                 # AWS Textract OCR
│   ├── TTS_online.py                   # Text-to-speech synthesis
│   ├── data_encoder.py                 # Data encoding utilities
│   ├── Pinecone data fetcher.py        # Pinecone vector DB integration
│   ├── local_script_code/              # Offline mode implementations
│   │   ├── main_local.py               # Local mode entry point
│   │   ├── speech_to_text.py           # Local STT (faster-whisper)
│   │   ├── text_to_speech.py           # Local TTS (Glow-TTS)
│   │   ├── local_ocr.py                # Local OCR (easyOCR)
│   │   └── medical_advisor_agent.py    # BioGPT medical agent
│   └── utils/                          # Helper utilities
│       ├── connectivity.py             # Internet connectivity check
│       ├── session.py                  # Session management
│       ├── LLM.py                      # LLM answer generation
│       ├── language.py                 # Language detection/translation
│       └── audio.py                    # Audio processing
├── my-chat-app/                        # React frontend
│   ├── src/
│   │   ├── components/                 # React components
│   │   ├── pages/                      # Application pages
│   │   └── App.js                      # Main React app
│   ├── package.json                    # Node dependencies
│   ├── package-lock.json               # Dependency lock file
│   └── public/                         # Static assets
├── assets/                             # Documentation assets
│   └── AWS_Mediassist_AI.png           # Architecture diagram
├── requirements.txt                    # Python dependencies
├── README.md                           # Project documentation
└── .env                                # Environment variables (create this)
```

## Performance Considerations

### Online Mode
- **Latency**: 2-5 seconds typical response time
- **Accuracy**: High-quality responses via Claude 3.5
- **Knowledge Recency**: Current medical information via RAG
- **Bandwidth**: ~2-5 MB per session

### Offline Mode
- **Latency**: 5-15 seconds (hardware dependent)
- **Accuracy**: Reliable medical guidance from BioGPT
- **Knowledge**: Static medical datasets
- **Bandwidth**: None required

## Troubleshooting

### Backend Won't Start
- Verify Python version: `python --version` (3.8+)
- Check virtual environment activation
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### API Key Errors
- Verify `.env` file exists in backend directory
- Confirm API keys are valid and have appropriate permissions
- For offline mode, comment out API key requirements

### Frontend Connection Issues
- Ensure backend is running on port 5000
- Check CORS configuration in Flask app
- Verify `http://localhost:5000` is accessible from browser

### Offline Model Loading
- Pre-download models to `models/` directory
- Check disk space (BioGPT requires ~3-4GB)
- Verify llama.cpp installation

## Model Information

```yaml
License: Apache 2.0

Tags:
  - Medical AI
  - RAG (Retrieval Augmented Generation)
  - Offline-capable
  - Multilingual
  - Healthcare

Languages:
  - English
  - Hindi

Models:
  - BioGPT (Q5_K_M GGUF)
  - Claude 3.5 (AWS Bedrock)
  - all-MiniLM-L6-v2 (Embeddings)

Speech Recognition:
  - OpenAI Whisper API
  - Faster-Whisper (base.en)

Speech Synthesis:
  - Amazon Polly
  - Glow-TTS

OCR:
  - AWS Textract
  - easyOCR

Vector Store: Pinecone

Datasets:
  - PubMedQA
  - MedQuad
```

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -m 'Add improvement'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

## Acknowledgments

This project integrates technologies and contributions from:

- **Amazon Web Services (AWS)** — Bedrock, Polly, Textract, Translate
- **Hugging Face** — Transformer models and embedding architectures
- **Pinecone** — Vector database for semantic search
- **Microsoft** — BioGPT biomedical language model
- **Glow-TTS** — Text-to-speech synthesis
- **Faster-Whisper** — Optimized speech recognition
- **OpenAI** — Whisper speech recognition API

## License

This project is licensed under the Apache License 2.0. See LICENSE file for details.

## Contact & Support

For issues, questions, or suggestions:

- GitHub Issues: [GitHub Repository](https://github.com/PranavShashidhara/MediAssist_AI/issues)
- Email: [maintainer@example.com]

## Disclaimer

This application provides medical information for educational purposes. It should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for medical concerns.


**Last Updated**: March 2026  
**Version**: 1.0.0