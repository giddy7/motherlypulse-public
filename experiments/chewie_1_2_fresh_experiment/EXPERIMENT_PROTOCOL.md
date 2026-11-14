# Fresh Experiment Protocol: Chewie 1.2 (`google/gemma-2-2b-it`)

**Experiment Directory:** `experiments/chewie_1_2_fresh_experiment/`  
**Date Initiated:** November 12, 2026  
**Status:** Phase 0/1 Active (Colab A100-SXM4-40GB Connected)

---

## 1. Research Objective
Conduct a clean, independently inspectable, reproducible **before-and-after** experiment on the original pretrained Chewie 1.2 base model (`google/gemma-2-2b-it`) to measure the exact effect of 4-bit QLoRA fine-tuning on the MotherlyPulse maternal and infant health dataset across English, Yoruba, and Nigerian Pidgin.

---

## 2. Base Model & Immutable Provenance
- **Model Identifier:** `google/gemma-2-2b-it` (verified in `models/chewie_adapter/adapter_config.json` and `MotherlyPulse_Stage2_Colab_Evaluation.ipynb`)
- **Immutable Hugging Face Commit Revision:** `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8` (verified live in Google Colab via `HfApi().model_info("google/gemma-2-2b-it").sha`)
- **Quantization at Load:** 4-bit NormalFloat (`nf4`), `bnb_4bit_compute_dtype=torch.bfloat16`, `bnb_4bit_use_double_quant=True` (`bitsandbytes==0.50.2`)

---

## 3. Dataset Version & SHA-256 Checksums
| Split | File Path | Records | SHA-256 Hash |
| :--- | :--- | :---: | :--- |
| Train (EN) | `data/train_en.jsonl` | 140 | `d40d8ad441f4d356107db32938d720c8a878069de3e9a6d26843442becf90160` |
| Train (YO) | `data/train_yo.jsonl` | 140 | `961e0c8541a2e3b2994fa75e843591637d8d19e8a882d44862d0b2dcbe38af34` |
| Train (PCM) | `data/train_pcm.jsonl` | 140 | `58cf1a5689f4580b2182c2418751620c83f35bbbf04f90666a7b7554eb8f9cd7` |
| Val (EN) | `data/val_en.jsonl` | 20 | `c5666c21a1bc8bcbd8cef33ac80d7e9bdb60a256e46657d7a978b83a7e840d58` |
| Val (YO) | `data/val_yo.jsonl` | 20 | `9ca0df0cca58565782f551957f12eb3ace58b2a595e2a89c57920bc135b10daa` |
| Val (PCM) | `data/val_pcm.jsonl` | 20 | `5c141e499e4f62f9dd29d7596cddcd018f5a0de17fd7196fd8b02df263f4789b` |
| Test (EN) | `data/test_en.jsonl` | 40 | `276f076f19d84600f840b05bb5e7cf583b7815ee11b39981ac6612950741b739` |
| Test (YO) | `data/test_yo.jsonl` | 40 | `c69cf9d77dc473148e6e6c4222aa0a4551c374bd93b2756d3bd0ed3f6ab64764` |
| Test (PCM) | `data/test_pcm.jsonl` | 40 | `fffdea0494d3f384264bf26527cf0c39d5ac97f8385b48ae61337d2a3720829f` |
| Fixed-15 | `MotherlyPulse_Data/04_Conversation_Data/fixed_15_evaluation_prompts.json` | 15 | `7830ab3d7b8b0f601a464af34387675a53a279d59688e26592321f5b9529e7bc` |

- **Split Isolation:** `140` train / `20` val / `40` test unique scenarios (`420 / 60 / 120` language records), `0` cross-split leakage.
- **Held-Out Evaluation Set:** `135` records (`120` test + `15` fixed prompts: `45` EN, `45` YO, `45` PCM). Never used in training or hyperparameter selection.

---

## 4. Experimental Hardware & Generation Settings
- **Hardware:** Google Colab `NVIDIA A100-SXM4-40GB` (`39.49 GB` VRAM), Python `3.13.16`, PyTorch `2.14.1+cu130`, `transformers==5.22.1`, `peft==0.21.2`, `bitsandbytes==0.50.2`, `accelerate==1.15.0`, `datasets==4.8.5`.
- **Identical Generation Settings (Before & After):** `max_new_tokens=100`, `do_sample=False` (greedy decoding), identical chat template prompt.

---

## 5. Evaluation Criteria (Separated Metrics)
1. **Triage-Prefix Compliance (`has_prefix`)** — reported separately from clinical safety.
2. **Clinical Safety Invariant Compliance (excl. prefix)** — contraindicated substances + emergency escalation.
3. **Contraindicated Recommendation Rate** (`agbo`, `aspirin`, etc.).
4. **Emergency 112 Escalation Performance** (overall and by language).
5. **Language-Specific & Urgency-Specific Breakdowns** (EN, YO, PCM; Emergency, Priority, Routine).
6. **Latency (Mean & Median ms)**, **Response Length (tokens/chars)**, and **Failed/Malformed Responses**.

---

## 6. Planned QLoRA Training Configuration
- **LoRA:** `r=16`, `lora_alpha=32`, `lora_dropout=0.05`, `target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]`, `bias="none"`, `task_type="CAUSAL_LM"`.
- **Training:** `420` train records, `60` validation records evaluated during training (`eval_strategy="steps"`, `eval_steps=20`), `per_device_train_batch_size=2`, `gradient_accumulation_steps=4`, `max_steps=80`, `learning_rate=2e-4`, `logging_steps=10`, `bf16=True`.
- **Fresh Artifact Storage:** `/content/drive/MyDrive/MotherlyPulse_Fresh_Chewie_1_2/` (separate from historical artifacts).

