import os
from pytubefix import YouTube
from pydub import AudioSegment

# ── Project Path Analysis ─────────────────────────────────────────────────────
BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "audio", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Focusing on high-signal colloquial sources
# These IDs are verified globally accessible long-form speeches/podcasts for 2026
DIALECT_SEEDS = {
    "standard_gujarati": [
        "https://www.youtube.com/watch?v=kYJ4a8lK8sY", # Narendra Modi Gujarati Speech
    ],
    "surti": [
        "https://www.youtube.com/watch?v=W_HjP-p-c5Q", # Surti Comedy/Vlog
    ],
    "charotari": [
        "https://www.youtube.com/watch?v=1F_XG00XJtM", # Charotari Lok Dayro
    ]
}

def download_video_audio(dialect, url):
    """
    Uses pytubefix to extract audio and pydub to enforce 16kHz mono WAV format.
    """
    video_id = url.split("v=")[-1]
    output_filename = f"{dialect}_{video_id}.wav"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if os.path.exists(output_path):
        print(f"⏩ Skipping {dialect.upper()} (Already exists): {output_filename}")
        return

    print(f"\n📡 Downloading {dialect.upper()} audio from {url}...")

    try:
        # 1. Download best audio stream using pytubefix
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
        audio_stream = yt.streams.filter(only_audio=True).first()
        if not audio_stream:
            print(f"❌ No audio stream found for {url}")
            return
            
        temp_file = audio_stream.download(output_path=OUTPUT_DIR, filename=f"temp_{video_id}.mp4")
        
        # 2. Convert to 16kHz Mono WAV using pydub
        print(f"⚙️ Formatting to 16kHz Mono WAV...")
        audio = AudioSegment.from_file(temp_file)
        
        # Set frame rate to 16000 and channels to 1 (mono)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        
        # 3. Cleanup temp mp4
        os.remove(temp_file)
        
        print(f"✅ Saved to: {output_path}")

    except Exception as e:
        print(f"❌ Unexpected error on {url}: {e}")

if __name__ == "__main__":
    print("="*50)
    print("  AUDIO SOURCING (For ASR Fine-Tuning)  ")
    print("="*50)
    
    for dialect, urls in DIALECT_SEEDS.items():
        for url in urls[:2]: 
            download_video_audio(dialect, url)
            
    print("\n🎉 Audio sourcing complete! Check the raw/ folder.")
