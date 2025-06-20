import logging 
from utils.connectivity import is_connected
from utils.session import get_user_inputs_formatted
from local_script_code.main_local import run_llm
from medical_llm import medical_rag_assistant, get_context_from_pinecone
def get_answer(question, use_rag, session_id=None):
    """
    Returns answer and context depending on connection and use_rag flag.
    Always includes chat history in context for better continuity.
    """
    logger = logging.getLogger('medical_app')

    try:
        connected = is_connected()
        logger.info(f"Getting answer - Connected: {connected}, Use RAG: {use_rag}")
        
        # Get formatted chat history
        chat_history = get_user_inputs_formatted(session_id, limit=8) if session_id else ""
        
        if use_rag and connected:
            # Get RAG context
            rag_context = get_context_from_pinecone(question)
            
            # Always combine contexts intelligently
            if chat_history and rag_context:
                full_context = f"{chat_history}Relevant medical information:\n{rag_context}"
                logger.info("Using combined chat history and RAG context")
            elif chat_history:
                full_context = chat_history
                logger.info("Using only chat history context (RAG context empty)")
            elif rag_context:
                full_context = f"Relevant medical information:\n{rag_context}"
                logger.info("Using only RAG context (no chat history)")
            else:
                full_context = ""
                logger.info("No context available (neither RAG nor chat history)")
            
            answer = medical_rag_assistant(question, full_context)
            mode = "online_with_rag"
            
        else: 
            # Offline or non-RAG mode
            full_context = chat_history
            if connected:
    # Optional: add chat history for online mode
                if chat_history:
                    full_question = f"{chat_history}Current question: {question}"
                    logger.info("Using chat history for online model")
                else:
                    full_question = question
            else:
                # Offline mode (BioGPT) — no history
                full_question = question.strip()
                logger.info("Running offline mode with no chat history")
                    
            answer = run_llm(full_question)
            mode = "offline" if not connected else "online_no_rag"

        logger.info(f"Used {mode} mode with context length: {len(full_context)}")
        return answer, full_context, mode
        
    except Exception as e:
        logger.error(f"Error getting answer: {e}")
        return "I apologize, but I encountered an error processing your question.", "", "error"

def is_file_query(question, extracted_text):
    """Check if the query is related to file content"""
    file_keywords = [
        "file", "document", "image", "text", "content", "extract", 
        "what does", "what is in", "analyze", "summarize", "tell me about",
        "information from", "show me", "read", "content of"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in file_keywords) or len(extracted_text.strip()) > 0