import os
from local_script_code.speech_to_text import transcribe_with_faster_whisper, download_model as download_whisper_model
from local_script_code.medical_advisor_agent import download_model as download_biogpt_model, BioGPTChat
from local_script_code.text_to_speech import speak_text
from local_script_code.local_ocr import extract_text_easyocr
HUGGINGFACE_TOKEN = os.getenv("HF_TOKEN")
WHISPER_MODEL_REPO = 'Systran/faster-whisper-base.en'

def run_stt(audio_input_path: str):
    print('⬇️ Downloading Whisper model for STT...')
    whisper_model_path = download_whisper_model(WHISPER_MODEL_REPO, HUGGINGFACE_TOKEN)
    print(f'🎧 Transcribing audio from: {audio_input_path}')
    transcript = transcribe_with_faster_whisper(audio_input_path, whisper_model_path)
    return transcript

def run_llm(prompt_text: str):
    print('🤖 Downloading/loading BioGPT model...')
    model_path = download_biogpt_model()
    print('🧬 Initializing BioGPTChat model instance...')
    bio_gpt = BioGPTChat(model_path, n_ctx=2048)
    print('💬 Generating LLM response...')
    response = bio_gpt.generate_response(prompt_text)
    return response

def run_tts(text_response: str):
    print('🔊 Synthesizing text to speech...')
    speak_text(text_response)
    print('🎵 Synthesized audio is sent to speaker.')

def run_ocr(image_path: str):
    print(f'🖼️ Extracting text from image: {image_path}')
    extracted_text = extract_text_easyocr(image_path)
    print(f'📄 Extracted Text:\n{extracted_text}')
    return extracted_text

def main():
    print('=== Starting Local Medical LLM Pipeline ===')
    input_audio_path = 'input_audio.wav'
    output_audio_path = 'output_response.wav'
    transcribed_text = run_stt(input_audio_path)
    print(f'\n📝 Transcribed Text:\n{transcribed_text}')
    llm_response = run_llm(transcribed_text)
    print(f'\n💡 LLM Response:\n{llm_response}')
    audio_file = run_tts(llm_response)
    print(f'\n✅ Pipeline complete. Output audio file: {audio_file}')
    image_path = 'C:/Users/prana/OneDrive - University of Maryland/Desktop/Internship and Part time/Hackathon/aws_medical_llm/Doctor-Note-Template-V02.jpg'
    if os.path.exists(image_path):
        ocr_text = run_ocr(image_path)
        print(f'\n🖼️ OCR Text:\n{ocr_text}')
if __name__ == '__main__':
    main()