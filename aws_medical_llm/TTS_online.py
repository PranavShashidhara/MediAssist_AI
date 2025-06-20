import boto3
from pydub import AudioSegment
from pydub.playback import play
import io

def play_speech(text, voice_id="Aditi", region="us-east-1"):
    polly = boto3.client("polly", region_name=region)

    response = polly.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId=voice_id
    )

    audio_stream = response["AudioStream"].read()
    audio = AudioSegment.from_file(io.BytesIO(audio_stream), format="mp3")
    play(audio)

if __name__ == "__main__":
    print("Playing English...")
    play_speech("Hello, this is the voice of AWS Polly.", voice_id="Joanna")

    print("Playing Hindi...")
    play_speech("नमस्ते, यह AWS पॉली की आवाज़ है।", voice_id="Aditi")

    print("Playing Mandarin Chinese...")
    play_speech("你好，这是AWS Polly的声音。", voice_id="Zhiyu")
