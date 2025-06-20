import os
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import tempfile
import queue
import threading
import sys
from huggingface_hub import snapshot_download
from faster_whisper import WhisperModel
import os 
from dotenv import load_dotenv

load_dotenv()
HUGGINGFACE_TOKEN = os.getenv("HF_TOKEN") 
MODEL_REPO_ID = "Systran/faster-whisper-base.en"  # or "Systran/faster-whisper-base.en" if you want that exact repo

def download_model(repo_id, token):
    print(f"Downloading model '{repo_id}' from Hugging Face with token...")
    local_model_path = snapshot_download(repo_id, use_auth_token=token)
    print(f"Model downloaded to: {local_model_path}")
    return local_model_path

def record_until_enter(sample_rate=16000, channels=1):
    # your existing record_until_enter code here ...
    q = queue.Queue()
    audio_frames = []

    def callback(indata, frames, time, status):
        if status:
            print("Status:", status, file=sys.stderr)
        q.put(indata.copy())

    def input_thread():
        input("Press ENTER to stop recording...\n")
        stop_event.set()

    stop_event = threading.Event()
    threading.Thread(target=input_thread, daemon=True).start()

    print("Recording... Press ENTER to stop.")
    with sd.InputStream(samplerate=sample_rate, channels=channels, dtype='int16', callback=callback):
        while not stop_event.is_set():
            try:
                data = q.get(timeout=0.1)
                audio_frames.append(data)
            except queue.Empty:
                continue

    print("Recording stopped.")
    return np.concatenate(audio_frames, axis=0)

def transcribe_with_faster_whisper(audio_path, model_path):
    print(f"Loading faster-whisper model from local path: {model_path}")
    model = WhisperModel(model_path, compute_type="int8")

    print(f"Transcribing file: {audio_path}")
    segments, info = model.transcribe(audio_path)

    text = ""
    for segment in segments:
        text += segment.text

    print("Transcription:\n", text)
    return text

if __name__ == "__main__":
    SAMPLE_RATE = 16000
    CHANNELS = 1

    # Download model explicitly with token
    local_model_path = download_model(MODEL_REPO_ID, HUGGINGFACE_TOKEN)

    # Record audio
    audio = record_until_enter(sample_rate=SAMPLE_RATE, channels=CHANNELS)

    # Save audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        write(tmpfile.name, SAMPLE_RATE, audio)
        audio_path = tmpfile.name
        print(f"Saved audio to: {audio_path}")

    # Transcribe with downloaded model path
    transcript = transcribe_with_faster_whisper(audio_path, local_model_path)
    print("Final Transcript:", transcript)

    # Clean up temp audio file
    os.remove(audio_path)
