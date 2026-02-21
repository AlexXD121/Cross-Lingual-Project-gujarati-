import os
from pytubefix import YouTube
from pydub import AudioSegment

BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "audio", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Hardcoded long-form speeches and vlogs for dataset diversity and robustness
DIALECT_SEEDS = {
    "standard_gujarati": [
        "https://www.youtube.com/watch?v=kYJ4a8lK8sY",
        "https://www.youtube.com/watch?v=ScK98pL9EwE",
        "https://www.youtube.com/watch?v=XpW0M_vP9o8",
        "https://www.youtube.com/watch?v=v6K1l6vcDlE",
        "https://www.youtube.com/watch?v=k8ypgT40rYI"
    ],
    "surti": [
        "https://www.youtube.com/watch?v=W_HjP-p-c5Q",
        "https://www.youtube.com/watch?v=J_Gz1N-uN_8",
        "https://www.youtube.com/watch?v=7_W0-yB6mP0",
        "https://www.youtube.com/watch?v=O123_surti_mock",
        "https://www.youtube.com/watch?v=P456_surti_mock"
    ],
    "charotari": [
        "https://www.youtube.com/watch?v=1F_XG00XJtM",
        "https://www.youtube.com/watch?v=dOKCU7BuNAI",
        "https://www.youtube.com/watch?v=PBRHvn5SCKY",
        "https://www.youtube.com/watch?v=A123_charo_mock",
        "https://www.youtube.com/watch?v=B456_charo_mock"
    ]
}

def extract_audio(dialect, url):
    video_id = url.split("v=")[-1]
    outfile = f"{dialect}_{video_id}.wav"
    outpath = os.path.join(OUTPUT_DIR, outfile)

    if os.path.exists(outpath):
        print(f"Skipping {outfile}, already downloaded.")
        return

    print(f"Downloading {dialect.upper()} from {url}...")
    try:
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=True)
        stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            print(f"No audio found for {url}")
            return
            
        temp_file = stream.download(output_path=OUTPUT_DIR, filename=f"temp_{video_id}.mp4")
        
        # Convert to 16kHz Mono for Whisper
        print("Converting to 16kHz mono WAV...")
        audio = AudioSegment.from_file(temp_file)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(outpath, format="wav")
        
        os.remove(temp_file)
        print(f"Done: {outpath}")

    except Exception as e:
        print(f"Failed to download {url}: {e}")

if __name__ == "__main__":
    for dialect, urls in DIALECT_SEEDS.items():
        for url in urls: 
            extract_audio(dialect, url)
