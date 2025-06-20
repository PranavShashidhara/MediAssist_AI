import numpy as np
import sounddevice as sd
from TTS.api import TTS

# ✅ Load once at start with GPU disabled for speed on CPU
print("🔄 Loading Glow-TTS (CPU-only)...")
tts = TTS("tts_models/en/ljspeech/glow-tts", gpu=False)
sample_rate = tts.synthesizer.output_sample_rate

def speak_text(text: str):
    if not text.strip():
        print("⚠️ Empty input. Skipping synthesis.")
        return

    print("🧠 Synthesizing audio...")
    audio = tts.tts(text)

    # Ensure it's float32 between -1.0 and 1.0
    audio_np = np.array(audio, dtype=np.float32)

    print(f"🔊 Playing audio at {sample_rate} Hz...")
    sd.play(audio_np, samplerate=sample_rate)
    sd.wait()
    print("✅ Playback complete.")

if __name__ == "__main__":
    sample_text = "Hello, this is a test of the English TTS model using Glow-TTS."
    speak_text(sample_text)
