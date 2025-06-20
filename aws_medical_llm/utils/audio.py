import logging 
import boto3 
from utils.connectivity import is_connected
from local_script_code.main_local  import run_tts
import base64

def synthesize_speech_base64(text, voice_id="Joanna", region="us-east-1"):
    """Synthesize speech and return base64 encoded audio"""
    logger = logging.getLogger('medical_app')
    try:
        output_audio_path = "output_response.wav"
        if not is_connected():
            logger.info("Using offline TTS")
            audio_file = run_tts(text, output_audio_path)
            return audio_file 
        
        logger.info(f"Using online TTS with voice: {voice_id}")
        polly = boto3.client("polly", region_name=region)
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice_id
        )
        audio_stream = response["AudioStream"].read()
        audio_base64 = base64.b64encode(audio_stream).decode("utf-8")
        return audio_base64
        
    except Exception as e:
        logger.error(f"Error in speech synthesis: {e}")
        return None