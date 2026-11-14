# Chewie 1.2 Fine-Tuning Methodology & Anti-Overfitting Report

**Model:** `google/gemma-2-2b-it` (pinned revision `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`) + QLoRA Adapter  
**Hardware:** `NVIDIA A100-SXM4-40GB` (`11.098 GB` peak VRAM, `148.34s` total training time)  
**Source Artifacts:** [training_log.json](experiments/chewie_1_2_fresh_experiment/02_finetuning/training_log.json), [adapter_config.json](experiments/chewie_1_2_fresh_experiment/02_finetuning/adapter_config.json), [FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md](experiments/chewie_1_2_fresh_experiment/FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md)

---

## 1. How Fine-Tuning Was Executed

### 1.1 Base Model & 4-Bit QLoRA Setup
- Loaded `google/gemma-2-2b-it` in **4-bit NormalFloat (NF4)** quantization (`bnb_4bit_compute_dtype=bfloat16`, `bnb_4bit_use_double_quant=True`).
- Applied `prepare_model_for_kbit_training` and wrapped the frozen base model with a **LoRA** adapter (`peft 0.21.2`) targeting only the attention projection layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`).
- **Trainable Parameters:** `6,389,760` out of `2,620,731,648` total parameters (**`0.2438%`**).

### 1.2 Data Formatting & Strict Split Isolation
- **Training Set (`420` rows):** `140` English (`data/train_en.jsonl`), `140` Nigerian Pidgin (`data/train_pcm.jsonl`), and `140` Yoruba (`data/train_yo.jsonl`), shuffled with `seed=42`.
- **Validation Set (`60` rows):** `20` English (`data/val_en.jsonl`), `20` Nigerian Pidgin (`data/val_pcm.jsonl`), and `20` Yoruba (`data/val_yo.jsonl`) — used solely for `eval_loss` checks during training.
- **Held-Out Evaluation Set (`135` rows):** `120` test rows (`test_{en,pcm,yo}.jsonl`) + `15` fixed prompts (`fixed_15_evaluation_prompts.json`) — completely isolated from both training and validation.
- **Chat Template & Label Masking:** Each example was formatted with the Gemma-2 chat template (`user` prompt + `assistant` target). All prompt tokens were masked to `-100` in `labels` so the optimizer computed loss **only** on the assistant's clinical response tokens.

### 1.3 Epochs, Batching & Step Count
- **Effective Batch Size:** `8` examples per optimizer step (`per_device_train_batch_size=2`, `gradient_accumulation_steps=4`).
- **Total Optimizer Steps:** `max_steps=80` (`640` example updates).
- **Total Epochs:** **`1.514` epochs** (`~1.51` epochs across the `420` training rows, recorded as `"epoch": 1.5142857142857142` in `training_log.json`).

---

## 2. Strategies Employed to Avoid Overfitting

Because clinical datasets of `420` examples are small relative to a `2.62B`-parameter LLM, six specific safeguards were used to prevent memorization and preserve generalization:

1. **Low-Rank Parameter Isolation (`0.2438%` Trainable Weights):**  
   Freezing the 4-bit base model and training only `r=16`, `lora_alpha=32` adapters on attention projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`)—while leaving MLP/FFN layers frozen—severely limits model capacity to memorize training examples while allowing style, triage-prefix, and safety-boundary adaptation.
2. **LoRA Dropout Regularization (`lora_dropout=0.05`):**  
   Applied 5% dropout inside the LoRA adapter paths during training to regularize updates on the `420`-row dataset.
3. **Conservative Epoch Budget (`1.51` Epochs / `80` Steps):**  
   Training was capped at `80` steps (`~1.51` epochs) instead of multi-epoch repetition (e.g., 3–5+ epochs), stopping once triage formatting and contraindication avoidance converged without over-memorizing training phrasing.
4. **Linear Learning Rate Decay (`2e-4` down to `2.5e-6`):**  
   Starting at `2e-4` and decaying linearly (`1.775e-4` at step 10 -> `1.025e-4` at step 40 -> `2.5e-6` at step 80) ensured early steps adapted formatting/safety behavior while late steps made small, stabilizing refinements.
5. **Prompt-Token Loss Masking (`labels = -100`):**  
   Masking user prompt tokens prevented the model from spending capacity memorizing input prompt templates instead of learning clinical response structure.
6. **Zero-Leakage Validation Monitoring (`eval_strategy="steps"`, `eval_steps=20`):**  
   Evaluated `eval_loss` every `20` steps on the separate `60`-row validation split (`val_{en,pcm,yo}.jsonl`) to verify that generalization loss kept decreasing alongside training loss.

---

## 3. Observed Training & Validation Curve (Overfitting Check)

| Step | Epoch | Learning Rate | Training Loss | Validation Loss (`n=60`) |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 0.19 | `1.775e-4` | `3.1089` | — |
| 20 | 0.38 | `1.525e-4` | `2.4856` | `2.2055` |
| 30 | 0.57 | `1.275e-4` | `2.6175` | — |
| 40 | 0.76 | `1.025e-4` | `2.3473` | `2.0849` |
| 50 | 0.95 | `7.750e-5` | `2.2812` | — |
| 60 | 1.13 | `5.250e-5` | `2.1570` | `2.0383` |
| 70 | 1.32 | `2.750e-5` | `2.1277` | — |
| 80 | 1.51 | `2.500e-6` | `2.2454` | **`2.0151`** |

- **No Overfitting Divergence:** Validation loss decreased monotonically at every evaluation checkpoint (`2.2055` -> `2.0849` -> `2.0383` -> `2.0151`) and remained below overall training loss (`2.4213`).
- **Held-Out Generalization (`n=135` unseen prompts):**
  - Contraindication violations dropped from `1.48%` (`2/135`) to **`0.00%`** (`0/135`).
  - Nigerian Pidgin (`pcm`) clinical safety improved from `91.11%` to **`100.00%`**.
  - `test_*.jsonl` triage-prefix compliance rose from `0.00%` (`0/120`) to **`100.00%`** (`120/120`).
- **Observed Limitations (Under-Generalization, Not Over-Memorization):**
  - Raw un-wrapped `fixed_15` prompts scored `0/15` on prefix emission because they lacked the training prompt wrapper (confirming the wrapper must be applied at inference time).
  - Yoruba (`yo`) Emergency `112` escalation slipped from `75.56%` to `68.89%` (`3` Yoruba Emergency regressions), showing that `140` Yoruba examples over `1.51` epochs is not enough by itself—which is why production inference keeps `EmergencyRulesEngine` and `ClinicalInvariantValidator` active as deterministic guardrails.

