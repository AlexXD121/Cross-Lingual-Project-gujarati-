import os
import torch
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
CHUNKED_AUDIO_DIR = os.path.join(BASE_DIR, "data", "audio", "chunked")
LABELED_DATASET_CSV = os.path.join(BASE_DIR, "data", "audio", "training_dataset.csv")
CLASSIFIER_PATH = os.path.join(BASE_DIR, "models", "nlu", "dialect_classifier")

def load_models():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading models on {device}...")

    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    transcriber = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-large-v3-turbo",
        device=device,
        torch_dtype=torch_dtype
    )

    tokenizer = AutoTokenizer.from_pretrained(CLASSIFIER_PATH)
    classifier = AutoModelForSequenceClassification.from_pretrained(CLASSIFIER_PATH)
    verifier = pipeline("text-classification", model=classifier, tokenizer=tokenizer, device=device)

    return transcriber, verifier

def transcribe_and_verify(audio_path, target_dialect, transcriber, verifier, confidence_threshold=0.75):
    try:
        result = transcriber(audio_path, generate_kwargs={"language": "gujarati"})
        transcript = result["text"].strip()
        
        if not transcript or len(transcript) < 5:
            return None, None
            
        classification = verifier(transcript)[0]
        detected_dialect = classification["label"]
        confidence = classification["score"]
        
        if detected_dialect == target_dialect and confidence >= confidence_threshold:
            print(f"  [+] KEEP: {transcript} ({confidence:.2f})")
            return transcript, confidence
        else:
            print(f"  [-] DISCARD: Expected {target_dialect}, got {detected_dialect} ({confidence:.2f})")
            return None, None
            
    except Exception as e:
        print(f"  Error on {audio_path}: {e}")
        return None, None

def main():
    if not os.path.exists(CHUNKED_AUDIO_DIR):
        print(f"Dir not found: {CHUNKED_AUDIO_DIR}")
        return

    transcriber, verifier = load_models()
    dataset_records = []
    
    for dialect_folder in os.listdir(CHUNKED_AUDIO_DIR):
        dialect_path = os.path.join(CHUNKED_AUDIO_DIR, dialect_folder)
        if not os.path.isdir(dialect_path): continue
            
        print(f"\nProcessing {dialect_folder}:")
        audio_files = [f for f in os.listdir(dialect_path) if f.endswith(".wav")]
        
        for audio_file in audio_files:
            audio_path = os.path.join(dialect_path, audio_file)
            transcript, conf = transcribe_and_verify(audio_path, dialect_folder, transcriber, verifier)
            
            # Crucial optimization for 4GB VRAM to prevent memory leaks from heavy models
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            if transcript:
                dataset_records.append({
                    "audio_path": audio_path,
                    "transcript": transcript,
                    "dialect": dialect_folder,
                    "confidence": conf
                })
                
    if dataset_records:
        df = pd.DataFrame(dataset_records)
        df.to_csv(LABELED_DATASET_CSV, index=False, encoding="utf-8-sig")
        print(f"\nSaved labeled dataset to {LABELED_DATASET_CSV} ({len(df)} samples)")
    else:
        print("\nNo samples passed confidence checks.")

if __name__ == "__main__":
    main()
