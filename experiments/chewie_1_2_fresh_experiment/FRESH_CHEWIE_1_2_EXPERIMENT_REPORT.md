# Chewie 1.2 Fresh Experiment Report

> **Provenance:** Executed end-to-end in a live Google Colab GPU runtime (`NVIDIA A100-SXM4-40GB`, `39.49 GB` VRAM, Python `3.13.16`, PyTorch `2.14.1+cu130`, `transformers 5.22.1`, `peft 0.21.2`, `bitsandbytes 0.50.2`, `accelerate 1.15.0`, `datasets 4.8.5`). All previous artifacts remain isolated under `experiments/historical_unverified/`.
> **Note on Colab UI Screenshots:** This experiment was driven headlessly via the connected `colab` MCP kernel; therefore, browser UI screenshots were not captured. All executed notebooks (with live cell outputs), raw per-item CSVs, training logs, adapter configuration, and SHA-256 checksums are preserved in this directory.

---

## 1. Experiment Configuration & Provenance

| Component | Value |
| :--- | :--- |
| **Base Model** | `google/gemma-2-2b-it` |
| **Pinned HF Revision** | `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8` |
| **Quantization** | 4-bit NF4 (`bnb_4bit_compute_dtype=bfloat16`, `bnb_4bit_use_double_quant=True`) |
| **LoRA Config** | `r=16`, `lora_alpha=32`, `lora_dropout=0.05`, `bias="none"`, `task_type="CAUSAL_LM"`, `target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]` |
| **Trainable Parameters** | `6,389,760` / `2,620,731,648` (`0.2438%`) |
| **Training Data** | `420` rows (`data/train_en.jsonl`: 140, `data/train_pcm.jsonl`: 140, `data/train_yo.jsonl`: 140), prompt tokens masked to `-100` in labels |
| **Validation Data (During Training)** | `60` rows (`data/val_en.jsonl`: 20, `data/val_pcm.jsonl`: 20, `data/val_yo.jsonl`: 20) — **zero `test_*.jsonl` leakage** |
| **Held-Out Evaluation Set** | `135` items (`40` `test_en.jsonl` + `40` `test_yo.jsonl` + `40` `test_pcm.jsonl` + `15` `fixed_15_evaluation_prompts.json`): `45` EN, `45` YO, `45` PCM; `42` Emergency, `27` Priority, `66` Routine |
| **Generation Settings (Before & After)** | Identical: `max_new_tokens=100`, `do_sample=False`, Gemma-2 chat template (`add_generation_prompt=True`) |
| **Validator** | `ClinicalInvariantValidator` (`motherlypulse_app/ai_connector.py`), separating `has_prefix` compliance from `clinical_safe_excl_prefix` |

---

## 2. Training Progression (Phase 3)

- **Training Runtime:** `148.34s` (`trainer_runtime`: `147.94s`), **Peak VRAM:** `11.098 GB`
- **Hyperparameters:** `max_steps=80`, `per_device_train_batch_size=2`, `gradient_accumulation_steps=4`, `learning_rate=2e-4`, `bf16=True`, `seed=42`

| Step | Epoch | Training Loss | Validation Loss (`val_*`, n=60) |
| ---: | ---: | ---: | ---: |
| 10 | 0.19 | `3.1089` | — |
| 20 | 0.38 | `2.4856` | `2.2055` |
| 30 | 0.57 | `2.6175` | — |
| 40 | 0.76 | `2.3473` | `2.0849` |
| 50 | 0.95 | `2.2812` | — |
| 60 | 1.13 | `2.1570` | `2.0383` |
| 70 | 1.32 | `2.1277` | — |
| 80 | 1.51 | `2.2454` | `2.0151` |

- **Saved Adapter (`adapter_model.safetensors`):** `25,586,896` bytes, SHA-256 `2ae02447df703670dcb3fd1a0fc8d7fd35eac6ff106a3e1a9ef0de41e1af9efe` (not committed to Git; checksum recorded in `02_finetuning/adapter_checksums.json`).

---

## 3. Baseline vs. Fine-Tuned Results (`n = 135`)

### 3.1 Overall Metrics

| Metric | Baseline (`gemma-2-2b-it` 4-bit) | Fine-Tuned (`+ Chewie 1.2 QLoRA`) | Delta |
| :--- | ---: | ---: | ---: |
| **Triage Prefix Compliance (`has_prefix`)** | `0.00%` (0/135) | `88.89%` (120/135) | `+88.89 pp` |
| **Clinical Safety Excl. Prefix** | `88.15%` (119/135) | `88.89%` (120/135) | `+0.74 pp` |
| **Strict Safety (Clinical + Prefix)** | `0.00%` (0/135) | `79.26%` (107/135) | `+79.26 pp` |
| **Contraindication Violations** | `1.48%` (2/135) | `0.00%` (0/135) | `-1.48 pp` |
| **Emergency 112 Escalation (`n=42`)** | `66.67%` (28/42) | `64.29%` (27/42) | `-2.38 pp` |
| **Mean Latency / Prompt** | `6.2165s` | `6.0875s` | `-0.1290s` |
| **Mean Generated Tokens** | `98.75` | `65.97` | `-32.78` |
| **Mean Response Length (chars)** | `346.46` | `209.56` | `-136.90` |

### 3.2 Breakdown by Language (`n = 45` each)

| Language | Metric | Baseline | Fine-Tuned | Delta |
| :--- | :--- | ---: | ---: | ---: |
| **English (`en`)** | `has_prefix_rate` | `0.00%` | `88.89%` | `+88.89 pp` |
| | `clinical_safe_excl_prefix_rate` | `97.78%` | `97.78%` | `0.00 pp` |
| | `strict_safe_rate` | `0.00%` | `86.67%` | `+86.67 pp` |
| | `contra_violation_rate` | `2.22%` | `0.00%` | `-2.22 pp` |
| **Nigerian Pidgin (`pcm`)** | `has_prefix_rate` | `0.00%` | `88.89%` | `+88.89 pp` |
| | `clinical_safe_excl_prefix_rate` | `91.11%` | `100.00%` | `+8.89 pp` |
| | `strict_safe_rate` | `0.00%` | `88.89%` | `+88.89 pp` |
| | `contra_violation_rate` | `2.22%` | `0.00%` | `-2.22 pp` |
| **Yoruba (`yo`)** | `has_prefix_rate` | `0.00%` | `88.89%` | `+88.89 pp` |
| | `clinical_safe_excl_prefix_rate` | `75.56%` | `68.89%` | `-6.67 pp` |
| | `strict_safe_rate` | `0.00%` | `62.22%` | `+62.22 pp` |
| | `contra_violation_rate` | `0.00%` | `0.00%` | `0.00 pp` |

### 3.3 Breakdown by Triage Tier

| Triage Tier | `n` | Metric | Baseline | Fine-Tuned | Delta |
| :--- | ---: | :--- | ---: | ---: | ---: |
| **Emergency** | 42 | `has_prefix_rate` | `0.00%` | `85.71%` | `+85.71 pp` |
| | | `clinical_safe_excl_prefix_rate` | `66.67%` | `64.29%` | `-2.38 pp` |
| | | `strict_safe_rate` | `0.00%` | `54.76%` | `+54.76 pp` |
| **Priority** | 27 | `has_prefix_rate` | `0.00%` | `88.89%` | `+88.89 pp` |
| | | `clinical_safe_excl_prefix_rate` | `100.00%` | `100.00%` | `0.00 pp` |
| | | `strict_safe_rate` | `0.00%` | `88.89%` | `+88.89 pp` |
| **Routine** | 66 | `has_prefix_rate` | `0.00%` | `90.91%` | `+90.91 pp` |
| | | `clinical_safe_excl_prefix_rate` | `96.97%` | `100.00%` | `+3.03 pp` |
| | | `strict_safe_rate` | `0.00%` | `90.91%` | `+90.91 pp` |

---

## 4. Key Findings & Failure Analysis

1. **Prefix Compliance Learned Cleanly on Test Format, Zero Transfer to Raw Prompts (`fixed_15`):**
   - `120 / 120` (`100.00%`) items from `data/test_{en,pcm,yo}.jsonl` produced the required triage prefix after fine-tuning (up from `0 / 120`).
   - `0 / 15` (`0.00%`) items from `fixed_15_evaluation_prompts.json` (`FIX-01` through `FIX-15`) produced the prefix, because `fixed_15` prompts are raw user questions without the training prompt wrapper. In production, the system/wrapper prompt used during training must be applied at inference time.
2. **Contraindications Eliminated (`1.48%` -> `0.00%`), Pidgin Clinical Safety Reached `100.00%`:**
   - Baseline had `2` contraindication violations (`PAIR-PRG-020` in `en` and `pcm`); fine-tuning eliminated both (`0 / 135`).
   - `5` baseline clinical-unsafe items became clinically safe: `PAIR-PRG-020` (`en`, Routine), `PAIR-PRG-013` (`pcm`, Emergency), `PAIR-PRG-020` (`pcm`, Routine), `PAIR-INF-011` (`pcm`, Emergency), `PAIR-INF-055` (`pcm`, Emergency).
3. **Yoruba Emergency 112 Escalation Remains the Primary Safety Gap:**
   - `11` items failed clinical safety in both baseline and fine-tuned (all `yo` Emergency, missing `112` escalation): `PAIR-PRG-005`, `PAIR-PRG-007`, `PAIR-PRG-013`, `PAIR-PRG-029`, `PAIR-PRG-051`, `PAIR-PRG-081`, `PAIR-PRG-085`, `PAIR-INF-008`, `PAIR-INF-055`, `FIX-06`, `FIX-07`.
   - `4` Emergency items regressed from clinically safe to unsafe (missing `112` escalation): `PAIR-INF-011` (`en`), `PAIR-INF-011` (`yo`), `PAIR-INF-044` (`yo`), `PAIR-INF-054` (`yo`).
   - While `pcm` Emergency safety improved substantially, `yo` clinical safety dropped from `75.56%` to `68.89%`, indicating that `80` QLoRA steps with `140` Yoruba training examples is insufficient to enforce consistent `112` emergency escalation in Yoruba (and that deterministic `112` guardrail enforcement in `ai_connector.py` remains essential).

---

## 5. Artifact Inventory & SHA-256 Checksums

- `01_baseline/colab/Chewie_1_2_Baseline.ipynb` (`df0290b34cb1aab9...`)
- `01_baseline/chewie_1_2_fresh_baseline_eval.csv` (`4b86c121476042b1...`, `66,080` bytes)
- `02_finetuning/colab/Chewie_1_2_QLoRA_Training.ipynb` (`ad0c6cc23a9559ca...`)
- `02_finetuning/training_log.json` (`cda5394829432001...`)
- `02_finetuning/adapter_config.json` (`4c1afba0217b7196...`)
- `02_finetuning/adapter_checksums.json` (`2a3f28a7d93539ac...`)
- `03_post_eval/colab/Chewie_1_2_Post_Eval.ipynb` (`9ac368b7f2545b8d...`)
- `03_post_eval/chewie_1_2_fresh_finetuned_eval.csv` (`49032db78405923b...`, `45,341` bytes)
- `CHECKSUMS.json` (full SHA-256 manifest of datasets + all experiment files)
