"""
train_classifier.py
===================
Dialect classifier for 4 Gujarati dialects using google/muril-base-cased.

Steps:
  1. GPU check
  2. Load data, encode labels, 80/10/10 split
  3. Tokenize with MuRIL tokenizer (max_length=128)
  4. Fine-tune with HuggingFace Trainer (fp16, batch=8)
  5. Evaluate — F1 per dialect + confusion matrix
  6. Save model + tokenizer to models/nlu/dialect_classifier/
"""

# Suppress harmless pynvml / OrderedVocab warnings before any imports
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*pynvml.*")
warnings.filterwarnings("ignore", message=".*OrderedVocab.*")
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # avoid tokenizer fork warning

import json
import numpy as np
import pandas as pd
import torch

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
)
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE        = r"d:\Cross Lingual Project(gujarati)"
DATA_FILE   = os.path.join(BASE, "data", "combined", "gujarati_dialects.csv")
PROC_DIR    = os.path.join(BASE, "data", "processed")
MODEL_OUT   = os.path.join(BASE, "models", "nlu", "dialect_classifier")
CKPT_DIR    = os.path.join(BASE, "models", "nlu", "checkpoints")

MODEL_NAME  = "google/muril-base-cased"
MAX_LEN     = 128
BATCH_SIZE  = 8       # safe for RTX 3050 4GB VRAM
EPOCHS      = 5
LR          = 2e-5
SEED        = 42

os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(MODEL_OUT, exist_ok=True)
os.makedirs(CKPT_DIR,  exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 — GPU CHECK
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("  STEP 1 — Environment Check")
print("=" * 60)

print(f"  PyTorch: {torch.__version__}")

if "+cpu" in torch.__version__:
    print("\n  WARNING: You have the CPU-only version of PyTorch.")
    print("  Your RTX 3050 will sit idle. Install the CUDA version:")
    print("\n  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121\n")
    print("  Training will continue on CPU — expect 30-60 min instead of 5-10 min.")
    DEVICE = "cpu"
    FP16   = False
elif torch.cuda.is_available():
    gpu  = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"  GPU    : {gpu}")
    print(f"  VRAM   : {vram:.1f} GB")
    print(f"  fp16   : enabled")
    DEVICE = "cuda"
    FP16   = True
else:
    print("  GPU not detected — running on CPU")
    DEVICE = "cpu"
    FP16   = False

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 2 — LOAD DATA, ENCODE LABELS, SPLIT 80/10/10
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 2 — Data Loading & Splitting")
print("=" * 60)

df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
print(f"  Loaded  : {len(df)} rows")
print(f"  Dialects: {df['dialect'].unique().tolist()}")

# Shuffle before splitting (CSV is ordered by dialect)
df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

# Encode labels: string → integer
le = LabelEncoder()
df["label"] = le.fit_transform(df["dialect"])

label_map = {i: name for i, name in enumerate(le.classes_)}
print(f"  Labels  : {label_map}")

# Save label map for inference later
with open(os.path.join(MODEL_OUT, "label_map.json"), "w") as f:
    json.dump(label_map, f, indent=2)

# 80 / 10 / 10 split
train_df, temp_df = train_test_split(df, test_size=0.2, stratify=df["label"], random_state=SEED)
val_df,   test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df["label"], random_state=SEED)

print(f"  Train   : {len(train_df)} rows")
print(f"  Val     : {len(val_df)} rows")
print(f"  Test    : {len(test_df)} rows")

# Save splits
train_df.to_csv(os.path.join(PROC_DIR, "train.csv"), index=False, encoding="utf-8-sig")
val_df.to_csv(os.path.join(PROC_DIR,   "val.csv"),   index=False, encoding="utf-8-sig")
test_df.to_csv(os.path.join(PROC_DIR,  "test.csv"),  index=False, encoding="utf-8-sig")
print(f"  Splits saved to data/processed/")

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 3 — TOKENIZATION (MuRIL)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 3 — Tokenization with MuRIL")
print("=" * 60)
print(f"  Downloading tokenizer: {MODEL_NAME}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(
        batch["sentence"],
        max_length=MAX_LEN,
        padding="max_length",
        truncation=True,
    )

# Convert to HuggingFace Dataset
def make_hf_dataset(dataframe):
    ds = Dataset.from_pandas(
        dataframe[["sentence", "label"]].reset_index(drop=True)
    )
    ds = ds.map(tokenize, batched=True)
    ds = ds.rename_column("label", "labels")
    ds.set_format("torch", columns=["input_ids", "attention_mask", "labels"])
    return ds

train_ds = make_hf_dataset(train_df)
val_ds   = make_hf_dataset(val_df)
test_ds  = make_hf_dataset(test_df)

print(f"  Tokenized: train={len(train_ds)}, val={len(val_ds)}, test={len(test_ds)}")
print(f"  Max length: {MAX_LEN} tokens")

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 4 — FINE-TUNING WITH TRAINER API
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 4 — Fine-tuning MuRIL")
print("=" * 60)
print(f"  Loading model: {MODEL_NAME} (num_labels={len(label_map)})")

num_dialects = len(label_map)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=num_dialects,
    id2label=label_map,
    label2id={v: k for k, v in label_map.items()},
    use_safetensors=True,   # avoids CVE-2025-32434 torch.load restriction in PyTorch 2.5.x
)

# Metric function for Trainer
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    f1  = f1_score(labels, preds, average="weighted")
    acc = (preds == labels).mean()
    return {"f1": f1, "accuracy": acc}

training_args = TrainingArguments(
    output_dir                   = CKPT_DIR,
    num_train_epochs             = EPOCHS,
    per_device_train_batch_size  = BATCH_SIZE,
    per_device_eval_batch_size   = BATCH_SIZE * 2,
    gradient_accumulation_steps  = 2,        # effective batch = 8x2 = 16, low VRAM
    learning_rate                = LR,
    weight_decay                 = 0.01,
    warmup_ratio                 = 0.1,
    fp16                         = FP16,
    eval_strategy                = "epoch",  # renamed from evaluation_strategy in v4.41+
    save_strategy                = "epoch",
    load_best_model_at_end       = True,
    metric_for_best_model        = "f1",
    greater_is_better            = True,
    logging_steps                = 50,
    save_total_limit             = 2,
    dataloader_num_workers       = 0,        # Windows fix — avoids thread lock crash
    seed                         = SEED,
    report_to                    = "none",   # no W&B / MLflow
)

trainer = Trainer(
    model           = model,
    args            = training_args,
    train_dataset   = train_ds,
    eval_dataset    = val_ds,
    compute_metrics = compute_metrics,
    callbacks       = [EarlyStoppingCallback(early_stopping_patience=2)],
)

print(f"  Batch size : {BATCH_SIZE}")
print(f"  Epochs     : {EPOCHS} (early stop patience=2)")
print(f"  LR         : {LR}")
print(f"  fp16       : {FP16}")
print(f"\n  Training started ...")

trainer.train()

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 5 — EVALUATION (F1 per dialect + Confusion Matrix)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 5 — Evaluation on Test Set")
print("=" * 60)

predictions = trainer.predict(test_ds)
preds       = np.argmax(predictions.predictions, axis=1)
true_labels = predictions.label_ids

# Classification report — F1 per dialect
target_names = [label_map[i] for i in range(len(label_map))]
report = classification_report(true_labels, preds, target_names=target_names, digits=4)
print(report)

# Confusion matrix
cm = confusion_matrix(true_labels, preds)
print("  Confusion Matrix:")
print(f"  {'':20}", "  ".join(f"{n[:8]:>8}" for n in target_names))
for i, row in enumerate(cm):
    print(f"  {target_names[i]:<20}", "  ".join(f"{v:>8}" for v in row))

# Overall F1
overall_f1 = f1_score(true_labels, preds, average="weighted")
target_met = overall_f1 >= 0.85
print(f"\n  Weighted F1 : {overall_f1:.4f}  {'(target met)' if target_met else '(below 0.85 target)'}"
      f"  [{len(label_map)} dialects]")

# Save eval results
results = {
    "weighted_f1" : round(float(overall_f1), 4),
    "target_met"  : target_met,
    "per_dialect" : {},
}
f1_per = f1_score(true_labels, preds, average=None)
for i, name in enumerate(target_names):
    results["per_dialect"][name] = round(float(f1_per[i]), 4)
results["num_dialects"] = len(label_map)

with open(os.path.join(MODEL_OUT, "eval_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print(f"  Results saved to models/nlu/dialect_classifier/eval_results.json")

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 6 — SAVE MODEL + TOKENIZER
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  STEP 6 — Saving Model")
print("=" * 60)

trainer.save_model(MODEL_OUT)
tokenizer.save_pretrained(MODEL_OUT)
print(f"  Model saved     : {MODEL_OUT}")
print(f"  Tokenizer saved : {MODEL_OUT}")
print(f"  Label map saved : {MODEL_OUT}/label_map.json")

print("\n" + "=" * 60)
print("  TRAINING COMPLETE")
print(f"  Weighted F1: {overall_f1:.4f}")
print(f"  Model at: models/nlu/dialect_classifier/")
print("=" * 60)
