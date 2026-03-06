import whisper
import os

# Tell Whisper exactly where ffmpeg is.
os.environ["PATH"] += os.pathsep + r"C:/ffmpeg/ffmpeg-master-latest-win64-gpl/bin"

model = whisper.load_model("base")

audio_path = "audio1975518882.mp3"

print("Transcribing... this may take a few minutes.")
result = model.transcribe(audio_path)

os.makedirs("data/transcripts", exist_ok=True)

with open("data/transcripts/account_001_demo.txt", "w") as f:
    f.write(result["text"])

print("Done! Transcript saved to data/transcripts/account_001_demo.txt")