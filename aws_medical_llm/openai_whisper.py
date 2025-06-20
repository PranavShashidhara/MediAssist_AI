import tempfile
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import soundfile as sf
import librosa
import openai
import os
from dotenv import load_dotenv
from langdetect import detect

# === CONFIGURATION ===
load_dotenv()
SAMPLE_RATE = 16000
openai.api_key = os.getenv("OPENAI_API_KEY")

# === RECORD AUDIO ===
def record_audio(duration=5, fs=SAMPLE_RATE):
    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    print("Recording complete.")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(temp_file.name, fs, audio_data)
    print(f"Saved to {temp_file.name}")
    return temp_file.name

# === CONVERT TO PCM FORMAT ===
def convert_to_pcm(input_path, output_path, target_samplerate=SAMPLE_RATE):
    print(f"Reading input WAV: {input_path}")
    data, samplerate = librosa.load(input_path, sr=None, mono=True)  # Always returns float32 mono
    print(f"Original samplerate: {samplerate}, shape: {data.shape}")

    if samplerate != target_samplerate:
        data = librosa.resample(data, orig_sr=samplerate, target_sr=target_samplerate)
        print(f"Resampled shape: {data.shape}")

    # Normalize and convert to int16
    data_int16 = np.int16(data / np.max(np.abs(data)) * 32767)
    write(output_path, target_samplerate, data_int16)
    print(f"Saved converted PCM WAV to: {output_path}")

# === TRANSCRIBE AUDIO ===
def transcribe_with_openai_whisper(audio_file_path):
    print("Transcribing with OpenAI Whisper...")
    with open(audio_file_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1"
        )
    return transcript.text

# === DETECT LANGUAGE ===
def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

# === OPTIONAL: TRANSLATE IF NOT ENGLISH ===
def translate_to_english_if_needed(text, detected_language):
    if detected_language.lower() == "en":
        print("Text is already in English.")
        return text

    print(f"Detected language: {detected_language}, translating to English...")
    prompt = f"""Translate the following text to English:\n\n{text}"""
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# === MAIN WORKFLOW ===
if __name__ == "__main__":
    raw_audio = record_audio()
    pcm_audio = raw_audio.replace(".wav", "_pcm.wav")
    convert_to_pcm(raw_audio, pcm_audio)

    transcript_text = transcribe_with_openai_whisper(pcm_audio)
    print("Transcript:", transcript_text)

    language = detect_language(transcript_text)
    translated_text = translate_to_english_if_needed(transcript_text, language)

    print("Final English Output:", translated_text)
