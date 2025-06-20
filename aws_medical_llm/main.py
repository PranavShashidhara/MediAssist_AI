from flask import Flask, request, jsonify
from flask_cors import CORS
from medical_llm import medical_assistant
from textract_ocr import extract_text_from_image
from openai_whisper import transcribe_with_openai_whisper, detect_language
from local_script_code.main_local import run_stt, run_tts, run_ocr
#from utils.logger import setup_logging
import logging
from utils.connectivity import is_connected
from utils.session import create_new_session, delete_session, get_all_sessions, save_user_input, get_user_inputs, get_user_inputs_formatted
from utils.audio import synthesize_speech_base64
from utils.LLM import get_answer, is_file_query
from threading import Thread
from TTS_online import play_speech
import subprocess
import tempfile
import os
from utils.language import translate_text
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

# Initialize logging
logger = logging.getLogger('medical_app')#setup_logging()

# Chat history file-based storage
# CHAT_HISTORY_DIR = Path("chat_history")
# CHAT_HISTORY_DIR.mkdir(exist_ok=True)

@app.route("/ask", methods=["POST"])
def handle_question():
    """Handle text-based questions"""
    try:
        data = request.json
        question = data.get("question")
        use_rag = data.get("use_rag", False)
        voice = data.get("voice", "Joanna")
        session_id = data.get("session_id")

        logger.info(f"Received question - Session: {session_id}, Use RAG: {use_rag}")

        if not question:
            logger.warning("Missing question in request")
            return jsonify({"error": "Missing 'question'"}), 400

        # Create session if not provided
        if not session_id:
            session_id = create_new_session()

        # Detect input language
        input_lang = "en"
        try:
            input_lang = detect_language(question)
            logger.info(f"Detected language: {input_lang}")
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")

        # Save user input
        save_user_input(session_id, question, 'text', input_language=input_lang)

        # Handle translation if needed
        connected = is_connected()
        if input_lang == "hi" and connected:
            translated_question = translate_text(question, "hi", "en")
            logger.info("Translated Hindi question to English")
        else:
            translated_question = question

        # Get answer with improved context handling
        answer_en, context, mode = get_answer(translated_question, use_rag, session_id)

        # Translate answer back if needed
        if input_lang == "hi" and connected:
            final_answer = translate_text(answer_en, "en", "hi")
            logger.info("Translated answer back to Hindi")
        else:
            final_answer = answer_en

        # Generate audio
        audio_base64 = synthesize_speech_base64(final_answer, voice_id=voice)
     
        logger.info(f"Successfully processed question - Mode: {mode}")
        
        return jsonify({
            "session_id": session_id,
            "question": question,
            "translated_question": translated_question if (input_lang == "hi" and connected) else None,
            "answer": final_answer,
            "audio_base64": audio_base64,
            "mode": mode,
            "context": context if context else None,
            "input_language": input_lang
        })

    except Exception as e:
        logger.error(f"Error in handle_question: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/ask_with_file", methods=["POST"])
def handle_question_with_file():
    """Handle questions with file uploads"""
    try:
        question = request.form.get("question", "")
        use_rag = request.form.get("use_rag", "false").lower() == "true"
        voice = request.form.get("voice", "Joanna")
        session_id = request.form.get("session_id")
        extracted_text = ""
        file_name = None

        logger.info(f"Received file question - Session: {session_id}")

        # Create session if not provided
        if not session_id:
            session_id = create_new_session()

        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                file_name = file.filename
                logger.info(f"Processing file: {file_name}")
                temp_path = tempfile.mktemp(suffix=".png")
                file.save(temp_path)
                try:
                    if is_connected():
                        # Online OCR 
                        extracted_text = extract_text_from_image(temp_path)
                        logger.info(f"Extracted {len(extracted_text)} characters from image (online OCR)")
                    else:
                        # Offline OCR fallback
                        extracted_text = run_ocr(temp_path)
                        logger.info(f"Extracted {len(extracted_text)} characters from image (offline OCR)")
                except Exception as e:
                    logger.error(f"Error extracting text from image: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        # Set default question if none provided
        if not question.strip() and extracted_text:
            question = "Please analyze and summarize the content of this file."

        if not question.strip():
            logger.warning("No question or file provided")
            return jsonify({"error": "No question or file provided"}), 400

        # Detect language
        input_lang = "en"
        try:
            input_lang = detect_language(question)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")

        # Save user input with file info
        user_message = question
        if file_name:
            user_message = f"📎 {file_name}\n{question}" if question else f"📎 File: {file_name}"
        
        save_user_input(session_id, user_message, 'file', 
                       file_name=file_name, extracted_text=extracted_text,
                       input_language=input_lang)

        connected = is_connected()

        # Prepare full question with file content
        full_question = question
        if extracted_text and is_file_query(question, extracted_text):
            full_question = f"{question}\n\nFile content:\n{extracted_text}"

        # Handle translation
        if input_lang == "hi" and connected:
            translated_question = translate_text(full_question, "hi", "en")
        else:
            translated_question = full_question

        # Process the question
        medical_terms = ["medical", "doctor", "medicine", "health", "symptom", "disease", "treatment", "diagnosis"]
        if is_file_query(question, extracted_text) and not any(med_term in question.lower() for med_term in medical_terms):
            if extracted_text:
                # Get chat history for file processing too
                chat_history = get_user_inputs_formatted(session_id, limit=5) if session_id else ""
                if chat_history:
                    file_question = f"{chat_history}User uploaded file and asked: {translated_question}\n\nFile content to analyze:\n{extracted_text}"
                else:
                    file_question = f"{translated_question}\n\nFile content to analyze:\n{extracted_text}"
                
                answer_en = medical_assistant(file_question)
                mode = "file_extraction"
                context = f"{chat_history}File content: {extracted_text}" if chat_history else extracted_text
                logger.info("Used file extraction mode with chat history")
            else:
                answer_en = "I couldn't extract any text from the uploaded file. Please make sure the file contains readable text or try a different format."
                mode = "file_extraction"
                context = ""
        else:
            answer_en, context, mode = get_answer(translated_question, use_rag, session_id)

        # Translate answer back if needed
        if input_lang == "hi" and connected:
            final_answer = translate_text(answer_en, "en", "hi")
        else:
            final_answer = answer_en

        # Generate audio
        audio_base64 = synthesize_speech_base64(final_answer, voice_id=voice)

        logger.info(f"Successfully processed file question - Mode: {mode}")

        return jsonify({
            "session_id": session_id,
            "question": question,
            "extracted_text": extracted_text if extracted_text else None,
            "translated_question": translated_question if (input_lang == "hi" and connected) else None,
            "answer": final_answer,
            "audio_base64": audio_base64,
            "mode": mode,
            "context": context if context else None,
            "input_language": input_lang
        })

    except Exception as e:
        logger.error(f"Error in handle_question_with_file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/transcribe", methods=["GET", "POST"])
def handle_transcription():
    """Handle voice transcription"""
    try:
        logger.info("Received transcription request")

        if "file" not in request.files:
            logger.warning("No audio file uploaded for transcription")
            return jsonify({"error": "No audio file uploaded"}), 400

        audio_file = request.files["file"]
        session_id = request.form.get("session_id")

        if not session_id:
            session_id = create_new_session()
            logger.info(f"Created new session ID: {session_id}")
        else:
            logger.info(f"Using existing session ID: {session_id}")

        logger.info("Saving uploaded audio file to temporary location")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_path = temp_file.name
            audio_file.save(temp_path)
            logger.info(f"Saved audio to: {temp_path}")

        try:
            pcm_path = temp_path.replace(".webm", ".wav")
            logger.info(f"Converting audio to WAV at: {pcm_path}")

            # Convert audio format
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_path,
                "-vn",  # disable video
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                pcm_path
            ], check=True)
            logger.info("Audio conversion completed successfully")

            connected = is_connected()
            logger.info(f"Internet connectivity status: {connected}")

            # Transcribe audio
            if connected:
                logger.info("Running online transcription (OpenAI Whisper)")
                transcript = transcribe_with_openai_whisper(pcm_path)
                input_lang = detect_language(transcript)
                logger.info(f"Detected input language: {input_lang}")
            else: 
                logger.info("Running offline transcription (FasterWhisper/local)")
                transcript = run_stt(pcm_path)
                input_lang = 'en'
                logger.info("Assumed English for offline mode")

            logger.info(f"Transcript: {transcript[:100]}{'...' if len(transcript) > 100 else ''}")

            # Save user voice input
            message_id = save_user_input(session_id, transcript, 'voice', input_language=input_lang)
            logger.info(f"Saved voice input with message ID: {message_id}")

            # Handle translation if necessary
            if input_lang == "hi" and connected:
                logger.info("Translating transcript from Hindi to English")
                translated_transcript = translate_text(transcript, "hi", "en")
                logger.info(f"Translated transcript: {translated_transcript[:100]}")
            else:
                translated_transcript = transcript

            # Get LLM answer
            logger.info("Getting answer from LLM pipeline")
            answer_en, context, mode = get_answer(translated_transcript, True, session_id)
            logger.info(f"LLM mode used: {mode}")

            if input_lang == "hi" and connected:
                logger.info("Translating answer from English back to Hindi")
                final_answer = translate_text(answer_en, "en", "hi")
                logger.info(f"Final translated answer: {final_answer[:100]}")
            else:
                final_answer = answer_en

            # Play audio response
            logger.info("Starting TTS response playback")
            if connected: 
                detected_output_lang = detect_language(final_answer)
                voice = "Aditi" if detected_output_lang == "hi" else "Joanna"
                logger.info(f"Using voice: {voice}")
                Thread(target=play_speech, args=(final_answer,), kwargs={"voice_id": voice}).start()
            else: 
                Thread(target=run_tts, args=(final_answer,)).start()
                logger.info("Used offline TTS playback")

            logger.info("Voice transcription flow completed successfully")
            return jsonify({
                "session_id": session_id,
                "transcript": transcript,
                "translated_transcript": translated_transcript if (input_lang == "hi" and connected) else None,
                "answer": final_answer,
                "context": context if context else None,
                "mode": mode,
                "input_language": input_lang
            })

        except subprocess.CalledProcessError as e:
            logger.error(f"Audio conversion failed with ffmpeg: {e}")
            return jsonify({"error": "Audio conversion failed"}), 500

        finally:
            logger.info("Skipping temp file deletion for debugging purposes")
            logger.info(f"Temp file paths:\n - {temp_path}\n - {pcm_path}")
            # Comment these lines out for now:
            # for path in [temp_path, pcm_path]:
            #     if os.path.exists(path):
            #         os.remove(path)
            #         logger.info(f"Deleted temp file: {path}")

    except Exception as e:
        logger.error(f"Error in handle_transcription: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Chat history management endpoints

@app.route("/history/<session_id>", methods=["GET"])
def get_session_history(session_id):
    """Get user input history for a specific session"""
    try:
        limit = request.args.get('limit', 50, type=int)
        inputs = get_user_inputs(session_id, limit)
        logger.info(f"Retrieved history for session {session_id}: {len(inputs)} inputs")
        return jsonify({
            "session_id": session_id,
            "user_inputs": inputs
        })
    except Exception as e:
        logger.error(f"Error getting session history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/sessions", methods=["GET"])
def get_sessions():
    """Get all chat sessions"""
    try:
        sessions = get_all_sessions()
        logger.info(f"Retrieved {len(sessions)} sessions")
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/session/new", methods=["POST"])
def create_session():
    """Create a new chat session"""
    try:
        session_id = create_new_session()
        return jsonify({"session_id": session_id})
    except Exception as e:
        logger.error(f"Error creating new session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/session/<session_id>", methods=["DELETE"])
def delete_session_endpoint(session_id):
    """Delete a chat session and all its user inputs"""
    try:
        success = delete_session(session_id)
        if success:
            return jsonify({"message": "Session deleted successfully"})
        else:
            return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/history/export/<session_id>", methods=["GET"])
def export_session_history(session_id):
    """Export user input history as JSON"""
    try:
        inputs = get_user_inputs(session_id, limit=1000)  # Export all inputs
        logger.info(f"Exported history for session {session_id}")
        return jsonify({
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "user_inputs": inputs
        })
    except Exception as e:
        logger.error(f"Error exporting session history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    """Health check endpoint"""
    logger.info("Health check accessed")
    return jsonify({
        "status": "Medical LLM backend running with improved user input history and context handling",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    logger.info("Starting Medical LLM backend server with improved context handling")
    app.run(host="0.0.0.0", port=8000)