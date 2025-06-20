import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path

# Setup basic logger if not already set
logger = logging.getLogger('medical_app')
logger.setLevel(logging.INFO)

# Add console handler if not added
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Directory to store chat history
CHAT_HISTORY_DIR = Path("chat_sessions")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)
def create_new_session():
    """Create a new session ID"""
    session_id = str(uuid.uuid4())
    logger.info(f"Created new session: {session_id}")
    return session_id

def delete_session(session_id):
    """Delete a chat session"""
    try:
        session_file = CHAT_HISTORY_DIR / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted session: {session_id}")
            return True
        else:
            logger.warning(f"Session file not found for deletion: {session_id}")
            return False
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return False

def get_all_sessions():
    """Get all chat sessions"""
    try:
        sessions = []
        for session_file in CHAT_HISTORY_DIR.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_info = {
                    "session_id": session_data.get("session_id"),
                    "created_at": session_data.get("created_at"),
                    "last_updated": session_data.get("last_updated"),
                    "input_count": len(session_data.get("user_inputs", [])),
                    "last_input_time": session_data.get("user_inputs", [{}])[-1].get("timestamp") if session_data.get("user_inputs") else None
                }
                sessions.append(session_info)
                
            except Exception as e:
                logger.error(f"Error reading session file {session_file}: {e}")
                continue
        
        # Sort by last_updated
        sessions.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return sessions
        
    except Exception as e:
        logger.error(f"Error getting all sessions: {e}")
        return []
    
def save_user_input(session_id, message, message_type='text', file_name=None, 
                   extracted_text=None, input_language='en'):
    """Save only user input to file-based storage"""
    try:
        session_file = CHAT_HISTORY_DIR / f"{session_id}.json"
        
        # Load existing session data or create new
        session_data = {"session_id": session_id, "user_inputs": []}
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error loading session file {session_file}: {e}")
        
        # Create new input entry
        input_entry = {
            "message_id": str(uuid.uuid4()),
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat(),
            "input_language": input_language
        }
        
        # Add optional fields
        if file_name:
            input_entry["file_name"] = file_name
        if extracted_text:
            input_entry["extracted_text"] = extracted_text
        
        # Add to session data
        session_data["user_inputs"].append(input_entry)
        session_data["last_updated"] = datetime.now().isoformat()
        
        # Create session metadata if not exists
        if "created_at" not in session_data:
            session_data["created_at"] = datetime.now().isoformat()
        
        # Save to file
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved user input for session {session_id}: {message_type}")
        return input_entry["message_id"]
        
    except Exception as e:
        logger.error(f"Error saving user input: {e}")
        return None

def get_user_inputs(session_id, limit=50):
    """Get user input history for a session"""
    try:
        session_file = CHAT_HISTORY_DIR / f"{session_id}.json"
        
        if not session_file.exists():
            logger.warning(f"Session file not found: {session_id}")
            return []
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        inputs = session_data.get("user_inputs", [])
        # Return last 'limit' inputs
        return inputs[-limit:] if len(inputs) > limit else inputs
        
    except Exception as e:
        logger.error(f"Error getting user inputs for session {session_id}: {e}")
        return []

def get_user_inputs_formatted(session_id, limit=8):
    """
    Get user input history for a session with better formatting for context.
    Returns formatted string ready to be used as context.
    """
    try:
        session_file = CHAT_HISTORY_DIR / f"{session_id}.json"
        
        if not session_file.exists():
            logger.warning(f"Session file not found: {session_id}")
            return ""
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        inputs = session_data.get("user_inputs", [])
        # Get last 'limit' inputs
        recent_inputs = inputs[-limit:] if len(inputs) > limit else inputs
        
        if not recent_inputs:
            return ""
        
        formatted_context = "Previous conversation history:\n"
        for input_item in recent_inputs:
            timestamp = input_item.get('timestamp', '')
            message = input_item.get('message', '')
            message_type = input_item.get('message_type', 'text')
            
            # Format timestamp to be more readable
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_time = timestamp
            
            # Format based on message type
            if message_type == 'file':
                file_name = input_item.get('file_name', 'Unknown file')
                extracted_text = input_item.get('extracted_text', '')
                if extracted_text:
                    # Truncate extracted text for context
                    text_preview = extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
                    formatted_context += f"[{formatted_time}] User uploaded '{file_name}' and asked: {message}\nFile content: {text_preview}\n\n"
                else:
                    formatted_context += f"[{formatted_time}] User uploaded '{file_name}' and asked: {message}\n\n"
            elif message_type == 'voice':
                formatted_context += f"[{formatted_time}] User said (voice): {message}\n\n"
            else:
                formatted_context += f"[{formatted_time}] User: {message}\n\n"
        
        formatted_context += "---\n\n"
        return formatted_context
        
    except Exception as e:
        logger.error(f"Error getting formatted user inputs for session {session_id}: {e}")
        return ""