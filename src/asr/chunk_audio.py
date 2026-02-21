import os
import torch
import torchaudio
import warnings

BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
RAW_AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio", "raw")
CHUNKED_AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio", "chunked")

os.makedirs(CHUNKED_AUDIO_DIR, exist_ok=True)

def load_vad_model():
    print("Loading Silero VAD model...")
    warnings.filterwarnings("ignore")
    try:
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
    except Exception as e:
        # Fallback for CVE-2025-32434 torch restriction load issues
        torch.serialization.add_safe_globals(['torch.nn.modules.container.Sequential', 'torch.nn.modules.linear.Linear'])
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )

    return model, utils

def split_audio(file_path, model, utils):
    get_speech_timestamps, save_audio, read_audio = utils[0], utils[1], utils[2]
    
    filename = os.path.basename(file_path)
    dialect = filename.split("_")[0]
    out_dir = os.path.join(CHUNKED_AUDIO_DIR, dialect)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Chunking {filename}...")
    try:
        wav = read_audio(file_path, sampling_rate=16000)
    except Exception as e:
        print(f"Couldn't read {filename}: {e}")
        return

    timestamps = get_speech_timestamps(
        wav, model, sampling_rate=16000, 
        threshold=0.5, min_speech_duration_ms=2000, 
        min_silence_duration_ms=500
    )

    if not timestamps:
        print(f"No speech found in {filename}.")
        return

    for i, ts in enumerate(timestamps):
        dur = (ts['end'] - ts['start']) / 16000.0
        if dur > 15.0: continue # 15s limit to save 4GB VRAM limits
        
        chunk_name = f"{filename.replace('.wav', '')}_{i:04d}.wav"
        save_audio(os.path.join(out_dir, chunk_name), wav[ts['start']:ts['end']], sampling_rate=16000)

    print(f"Created {len(timestamps)} chunks for {filename}")

if __name__ == "__main__":
    if not os.path.exists(RAW_AUDIO_DIR):
        print(f"Directory not found: {RAW_AUDIO_DIR}")
        exit()

    files = [os.path.join(RAW_AUDIO_DIR, f) for f in os.listdir(RAW_AUDIO_DIR) if f.endswith('.wav')]
    if not files:
        print("No raw .wav files to parse.")
        exit()
    
    model, utils = load_vad_model()
    for f in files:
        split_audio(f, model, utils)
