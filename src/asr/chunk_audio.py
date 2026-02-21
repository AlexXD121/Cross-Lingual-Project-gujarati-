import os
import torch
import torchaudio
from pathlib import Path

# Adjust paths to the project
BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
RAW_AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio", "raw")
CHUNKED_AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio", "chunked")

os.makedirs(CHUNKED_AUDIO_DIR, exist_ok=True)

def load_silero_vad():
    """Load the Silero VAD model from PyTorch Hub."""
    print("🧠 Loading Silero VAD model...")
    
    # Check if we have torch > 2.6 or not for safety
    try:
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
    except Exception as e:
        print(f"⚠️ Standard load failed, trying with safe load bypassed: {e}")
        # Workaround for torch.load CVE-2025-32434 restriction if caught
        import warnings
        warnings.filterwarnings("ignore")
        torch.serialization.add_safe_globals(['torch.nn.modules.container.Sequential', 'torch.nn.modules.linear.Linear'])
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )

    (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
    return model, get_speech_timestamps, read_audio, save_audio

def chunk_audio_file(file_path, model, get_speech_timestamps, read_audio, save_audio):
    """
    Reads a 16kHz WAV file and splits it into small chunks
    based on voice activity detection.
    """
    filename = os.path.basename(file_path)
    dialect_name = filename.split("_")[0] # e.g. 'surti'
    
    dialect_out_dir = os.path.join(CHUNKED_AUDIO_DIR, dialect_name)
    os.makedirs(dialect_out_dir, exist_ok=True)

    print(f"\n🎧 Processing: {filename}")
    
    try:
        wav = read_audio(file_path, sampling_rate=16000)
    except Exception as e:
        print(f"❌ Failed to read {filename}. Ensure it is a valid 16kHz WAV. Error: {e}")
        return

    # Get timestamps of speech (returns list of dicts: {'start': 1234, 'end': 5678})
    # threshold=0.5 is strict enough to exclude pure noise
    # min_speech_duration_ms=2000 (We want at least 2 seconds per clip to be useful for ASR)
    speech_timestamps = get_speech_timestamps(
        wav, 
        model, 
        sampling_rate=16000, 
        threshold=0.5,
        min_speech_duration_ms=2000,
        min_silence_duration_ms=500  # Split if there's a 0.5s pause
    )

    if not speech_timestamps:
        print(f"⚠️ No active speech detected in {filename}.")
        return

    print(f"✂️ Found {len(speech_timestamps)} valid speech chunks.")

    for i, ts in enumerate(speech_timestamps):
        start_sample = ts['start']
        end_sample = ts['end']
        
        # Calculate duration in seconds
        duration_s = (end_sample - start_sample) / 16000.0
        
        # Skip chunks that are extremely long (Whisper expects <30s)
        if duration_s > 30.0:
            print(f"  ⏭️ Skipping chunk {i} ({duration_s:.1f}s) - too long.")
            continue

        chunk_filename = f"{filename.replace('.wav', '')}_chunk_{i:04d}.wav"
        chunk_path = os.path.join(dialect_out_dir, chunk_filename)
        
        # Save the isolated audio chunk
        save_audio(chunk_path, wav[start_sample:end_sample], sampling_rate=16000)

    print(f"✅ Saved chunks for {filename} to {dialect_out_dir}")

def main():
    print("="*50)
    print("  SILERO VAD AUDIO CHUNKING  ")
    print("="*50)
    
    if not os.path.exists(RAW_AUDIO_DIR):
        print(f"❌ Raw audio directory not found: {RAW_AUDIO_DIR}")
        return

    raw_files = [os.path.join(RAW_AUDIO_DIR, f) for f in os.listdir(RAW_AUDIO_DIR) if f.endswith('.wav')]
    if not raw_files:
        print("🤷 No raw .wav files found to process.")
        return

    print(f"📁 Found {len(raw_files)} raw audio files.")
    
    model, get_speech_timestamps, read_audio, save_audio = load_silero_vad()
    
    for file_path in raw_files:
        chunk_audio_file(file_path, model, get_speech_timestamps, read_audio, save_audio)

if __name__ == "__main__":
    main()
