import os
import torch
import pandas as pd
from datasets import Dataset, Audio
from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DefaultDataCollator
)
from peft import LoraConfig, get_peft_model

BASE_DIR = r"d:\Cross Lingual Project(gujarati)"
DATASET_CSV = os.path.join(BASE_DIR, "data", "audio", "training_dataset.csv")
MODEL_OUT = os.path.join(BASE_DIR, "models", "asr", "whisper_gujarati_lora")

os.makedirs(MODEL_OUT, exist_ok=True)

def load_data():
    if not os.path.exists(DATASET_CSV):
        raise FileNotFoundError(f"{DATASET_CSV} missing. Run auto_label.py.")
        
    df = pd.read_csv(DATASET_CSV)
    hf_dataset = Dataset.from_pandas(df[["audio_path", "transcript"]])
    hf_dataset = hf_dataset.cast_column("audio_path", Audio(sampling_rate=16000))
    
    splits = hf_dataset.train_test_split(test_size=0.1)
    return splits["train"], splits["test"]

def prepare_dataset(batch, processor):
    audio = batch["audio_path"]
    batch["input_features"] = processor.feature_extractor(audio["array"], sampling_rate=audio["sampling_rate"]).input_features[0]
    batch["labels"] = processor.tokenizer(batch["transcript"]).input_ids
    return batch

def main():
    model_id = "openai/whisper-small"
    processor = WhisperProcessor.from_pretrained(model_id, language="Gujarati", task="transcribe")
    
    print("Preparing dataset...")
    train_data, test_data = load_data()
    train_data = train_data.map(lambda b: prepare_dataset(b, processor), remove_columns=train_data.column_names)
    test_data = test_data.map(lambda b: prepare_dataset(b, processor), remove_columns=test_data.column_names)
    
    print("Loading base model...")
    model = WhisperForConditionalGeneration.from_pretrained(model_id)
    
    print("Applying LoRA config...")
    config = LoraConfig(
        r=32,
        lora_alpha=64,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none"
    )
    model = get_peft_model(model, config)
    model.print_trainable_parameters()
    
    training_args = Seq2SeqTrainingArguments(
        output_dir=MODEL_OUT,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        learning_rate=1e-3,
        warmup_steps=50,
        max_steps=500,
        eval_strategy="steps",
        gradient_checkpointing=True,
        fp16=True,
        per_device_eval_batch_size=2,
        predict_with_generate=True,
        generation_max_length=225,
        save_steps=100,
        eval_steps=100,
        logging_steps=25,
        remove_unused_columns=False,
    )
    
    data_collator = DefaultDataCollator()

    print("Starting trainer...")
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_data,
        eval_dataset=test_data,
        data_collator=data_collator,
        tokenizer=processor.feature_extractor,
    )
    
    try:
        trainer.train()
        print(f"Saved LoRA weights to {MODEL_OUT}")
        model.save_pretrained(MODEL_OUT)
        processor.save_pretrained(MODEL_OUT)
    except Exception as e:
        print(f"Training failed: {e}")

if __name__ == "__main__":
    main()
