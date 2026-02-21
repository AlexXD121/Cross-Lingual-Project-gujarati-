import os
import torch
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
CHUNKED_AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio", "chunked")
LABELED_DATASET_CSV = os.path.join(BASE_DIR, "data", "audio", "training_dataset.csv")
CLASSIFIER_PATH = os.path.join(BASE_DIR, "models", "nlu", "dialect_classifier")

def load_models():
    """Load Whisper Turbo for transcription and MuRIL for dialect verification."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"⚙️ Running on {device.upper()}")

    print("🧠 Loading Whisper-Large-V3-Turbo (Transcription)...")
    # Using pipeline for easy audio transcription. FP16 on GPU speeds this up immensely.
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    transcriber = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v3-turbo",
        device=device,
        torch_dtype=torch_dtype
    )

    print("🧠 Loading MuRIL Dialect Classifier (Verification)...")
    # Load our Phase 2 trained model
    tokenizer = AutoTokenizer.from_pretrained(CLASSIFIER_PATH)
    classifier = AutoModelForSequenceClassification.from_pretrained(CLASSIFIER_PATH)
    
    # HuggingFace pipeline for classification
    verifier = pipeline("text-classification", model=classifier, tokenizer=tokenizer, device=device)

    return transcriber, verifier

def transcribe_and_verify(audio_path, target_dialect, transcriber, verifier, confidence_threshold=0.85):
    """
    1. Transcribes audio chunk to Gujarati text.
    2. Runs text through classifier.
    3. Keeps it ONLY if classifier agrees with the target_dialect folder name.
    """
    try:
        # 1. Transcribe (Force Gujarati language output)
        result = transcriber(audio_path, generate_kwargs={"language": "gujarati"})
        transcript = result["text"].strip()
        
        if not transcript or len(transcript) < 5:
            return None, None # Skip silence or noise
            
        # 2. Verify with our MuRIL Dialect Model
        classification = verifier(transcript)[0]
        detected_dialect = classification["label"]
        confidence = classification["score"]
        
        # 3. Decision
        if detected_dialect == target_dialect and confidence >= confidence_threshold:
            print(f"  ✅ [KEEP] {transcript} (Conf: {confidence:.2f})")
            return transcript, confidence
        else:
            print(f"  ❌ [DISCARD] Missmatch. Target: {target_dialect}, Detected: {detected_dialect} ({confidence:.2f})")
            return None, None
            
    except Exception as e:
        print(f"  ⚠️ Transcription failed for {audio_path}: {e}")
        return None, None

def main():
    print("="*50)
    print("  AUTO-LABELING PIPELINE (AI Building AI)  ")
    print("="*50)
    
    if not os.path.exists(CHUNKED_AUDIO_DIR):
        print(f"❌ Chunked audio folder missing: {CHUNKED_AUDIO_DIR}")
        return

    transcriber, verifier = load_models()
    
    dataset_records = []
    
    # Walk through each dialect folder
    for dialect_folder in os.listdir(CHUNKED_AUDIO_DIR):
        dialect_path = os.path.join(CHUNKED_AUDIO_DIR, dialect_folder)
        if not os.path.isdir(dialect_path):
            continue
            
        print(f"\n📂 Processing folder: {dialect_folder.upper()}")
        
        audio_files = [f for f in os.listdir(dialect_path) if f.endswith(".wav")]
        for audio_file in audio_files:
            audio_path = os.path.join(dialect_path, audio_file)
            
            # Run the AI verification
            transcript, conf = transcribe_and_verify(audio_path, dialect_folder, transcriber, verifier)
            
            if transcript:
                dataset_records.append({
                    "audio_path": audio_path,
                    "transcript": transcript,
                    "dialect": dialect_folder,
                    "confidence": conf
                })
                
    # Save the new training ground truth dataset
    if dataset_records:
        df = pd.DataFrame(dataset_records)
        df.to_csv(LABELED_DATASET_CSV, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Auto-labeling complete! Created highly-accurate dataset with {len(df)} clips.")
        print(f"💾 Saved to: {LABELED_DATASET_CSV}")
    else:
        print("\n⚠️ Pipeline finished but no audio clips passed the >85% confidence verification check.")

if __name__ == "__main__":
    main()
