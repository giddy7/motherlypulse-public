# Model Card: Chewie 1.2 Adapter (Gemma 2B QLoRA)

**Model Name:** Chewie 1.2  
**Base Model:** `google/gemma-2-2b-it` (Gemma 2B Instruction-Tuned)  
**Task:** Multilingual Maternal and Infant Health Conversational Guidance  
**Target Languages:** English, Yoruba, Nigerian Pidgin  
**Target Geography:** Ondo State, Nigeria  
**Fine-Tuning Method:** 4-bit NormalFloat (NF4) QLoRA via PEFT  
**Date of Training:** November 9, 2026  
**License:** Gemma Terms of Use  

---

## 1. Model Description & Purpose
Chewie 1.2 is an adapted language model designed to deliver culturally nuanced, empathetic maternal and child health guidance for pregnant women, new mothers, and caregivers in Ondo State, Nigeria. It was fine-tuned to classify and respond in three clinical tiers: `EMERGENCY:`, `PRIORITY:`, and `ROUTINE:`.

Chewie 1.2 operates strictly inside the **MotherlyPulse Hybrid Safety Pipeline**:
1. **Deterministic Emergency Bypass:** Life-threatening emergencies bypass the model entirely in 0.05 ms and return vetted 112 escalation instructions.
2. **Clinical Invariant Validator:** Model responses are screened for forbidden substances (e.g., *agbo*, aspirin in pregnancy) and required escalation protocols before reaching a user.
3. **Deterministic Fallback:** Any model failure, timeout, or safety violation seamlessly defaults to approved reference text.

---

## 2. Training Data & Hardware
- **Training Dataset:** 420 instruction-response pairs (140 unique maternal/infant clinical scenarios $\times$ 3 languages: English, Yoruba, Nigerian Pidgin).
- **Split Provenance:** 140 train / 20 validation / 40 held-out test scenarios (100% disjoint at the scenario level).
- **Hardware Profile:** NVIDIA A100-SXM4-80GB (79.25 GB VRAM) on Google Colab Pro.
  > *Note: Training was conducted on a paid cloud GPU. Performance and memory fit on a free T4 GPU is untested.*
- **Training Duration:** 140.29 seconds (80 optimizer steps).
- **Training Loss:** Decreased from 3.77 to 1.85. Peak VRAM: 7.24 GB allocated.

---

## 3. Fine-Tuning Hyperparameters
| Hyperparameter | Value |
| :--- | :--- |
| **Quantization** | 4-bit NormalFloat (NF4), Double Quantization enabled |
| **LoRA Rank ($r$)** | 16 |
| **LoRA Alpha ($\alpha$)** | 32 |
| **LoRA Dropout** | 0.05 |
| **Target Modules** | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| **Trainable Parameters** | 6,389,760 / 2,620,731,648 (0.2438% of total) |
| **Learning Rate** | $2 \times 10^{-4}$ (default linear decay, `max_steps=80`, `fp16=True`, `max_length=384`) |
| **Batch Size / Grad Accum** | 2 / 4 (effective batch size = 8) |
| **Optimizer** | Default Hugging Face Trainer AdamW (`adamw_torch_fused` / `adamw_torch`) |
| **Validation / Checkpointing** | `save_strategy="no"`; 60-record validation split was not evaluated during the 80-step `Trainer` run |

---

## 4. Evaluation Results (Held-Out Benchmark)
Evaluated across 135 held-out records (120 test scenarios + 15 fixed benchmark prompts) on an NVIDIA A100-SXM4-80GB GPU with identical generation settings (`max_new_tokens=100`, greedy decoding `do_sample=False`):

| Metric | Pretrained Base (`gemma-2-2b-it`) | Fine-Tuned Chewie 1.2 | Delta / Finding |
| :--- | :--- | :--- | :--- |
| **Category Prefix Compliance** | 0.00% (0 / 135) | **100.00% (135 / 135)** | +100.00% adherence to clinical structure |
| **Substance & Escalation Safety (Excl. Prefix)** | 79.26% (107 / 135) | **88.15% (119 / 135)** | +8.89% clinical safety improvement |
| **Overall Strict `is_safe` Pass Rate** | 0.00% (0 / 135)* | **88.15% (119 / 135)** | *Baseline scored 0% solely due to missing prefix |
| **English Strict `is_safe`** | 0.00% (0 / 45) | **97.78% (44 / 45)** | 1 false alarm on *agbo* prohibition warning |
| **Nigerian Pidgin Strict `is_safe`** | 0.00% (0 / 45) | **97.78% (44 / 45)** | High fluency & safety (1 failure on infant fever) |
| **Yoruba Strict `is_safe`** | 0.00% (0 / 45) | **68.89% (31 / 45)** | 14 Yoruba emergencies suffered token loops |
| **Emergency 112 Escalation (Overall)** | 38.10% (16 / 42) | **64.29% (27 / 42)** | English: 100%, Pidgin: 92.9%, Yoruba: 0% |
| **Mean / Median Latency** | 6,381.16 ms / 6,418.91 ms | **5,594.39 ms / 4,565.80 ms** | 1.14x faster mean (60.99 vs. 99.11 output tokens) |
| **Human Clinical Review** | Pending | **Pending** | Blinded sheets exported for clinician rating |
| **Native Speaker Review** | Pending | **Pending** | Blinded sheets exported for Yoruba/Pidgin review |

---

## 5. Known Limitations & Safety Mitigation
1. **Low-Resource Language Token Loops (Yoruba 2B):**
   The 2B parameter base model exhibits token loops and attention sink failure on complex, polysyllabic Yoruba emergency queries, occasionally generating `ROUTINE:` instead of escalating to 112.  
   *Mitigation:* In the live MotherlyPulse architecture, **the deterministic triage classifier intercepts emergency keywords in 0.05 ms before model generation**, ensuring 100% of emergency presentations receive 112 escalation regardless of base model capacity.
2. **False Alarms on Prohibitive Warnings:**
   Keyword filters can flag responses where the model correctly warns *against* dangerous practices (e.g., advising against *agbo* in pregnancy). The deterministic fallback safely replaces these with verified reference text.
3. **No Unassisted Clinical Prescribing:**
   Chewie 1.2 is an information and triage assistant, not a doctor. It strictly declines specific drug dosages and directs users to primary health centers.

---

## 6. Adapter Storage & Cryptographic Baseline
The adapter weights and configuration files are stored in one off-host cloud mirror and two local copies on the same `C:` drive:
1. **Off-Host Cloud Mirror (Google Drive):** `/content/drive/MyDrive/MotherlyPulse_Artifacts/chewie_adapter/`
2. **Local Backup Archive:** Private offline archive (`MotherlyPulse_Artifacts.zip`)
3. **Local Workspace (`C:` drive, gitignored):** `models\chewie_adapter\`

| File Name | Size | SHA-256 Hash |
| :--- | :--- | :--- |
| `adapter_model.safetensors` | 24,987.2 KB | `631042d9cf6f0ec41a35b749fda30b5c3cfb7a03189b5b3d4e5e035d9a232001` |
| `adapter_config.json` | 1.1 KB | `f43a03286680e5019359f0fb812e0a85f88e5478d5fa20ee9b83a458669bd80b` |
| `tokenizer.json` | 33,557.75 KB | `938dc2654808135f42dfc7e17ca92243ab1bd4d97d5e92c5d00055b63bcda156` |
| `tokenizer_config.json` | 0.51 KB | `b2d15305cb82104c37cdd3475b11d8a5623d5cc12a0b4518571dd925e0f1ca02` |
| `chat_template.jinja` | 0.58 KB | `ecd6ae513fe103f0eb62e8ab5bfa8d0fe45c1074fa398b089c93a7e70c15cfd6` |
| `README.md` | 5.07 KB | `4adfb7ff9a7ecd4908dabcb88598827ca5e256d3aa0983dae6bea03009bfe755` |

