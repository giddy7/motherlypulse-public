# AI Model Selection & Fine-Tuning

## 1. Model Selection Rationale

- **Selected Base Model:** `google/gemma-2-2b-it` (pinned HF revision `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`).
- **Why Gemma-2-2B-IT (`Chewie 1.2`):**
  1. Compact `2.62B` parameter footprint enables 4-bit QLoRA training on a single GPU in `< 3` minutes and optional CPU inference via `llama.cpp` (`Q4_K_M` GGUF, `1.59 GiB` file size).
  2. Strong instruction-following baseline in English and Nigerian Pidgin, adaptable to structured clinical prefixes (`EMERGENCY:`, `PRIORITY:`, `ROUTINE:`).
- **Deferred Alternative:** A planned second model (`MamaBot-Llama`, `meta-llama/Llama-3.1-8B-Instruct`) was deferred to future work due to gated access timing and higher VPS RAM requirements.

## 2. QLoRA Fine-Tuning & Anti-Overfitting Strategy

Executed in Colab on an `NVIDIA A100-SXM4-40GB` (`148.34s`, `11.098 GB` peak VRAM):
- **Trainable Parameters:** `6,389,760 / 2,620,731,648` (**`0.2438%`**) via LoRA (`r=16`, `lora_alpha=32`, `lora_dropout=0.05`, attention-only `q_proj, k_proj, v_proj, o_proj`).
- **Data Split:** `420` training rows (`140` EN, `140` PCM, `140` YO), `60` validation rows (`val_{en,pcm,yo}.jsonl`), and `135` held-out test rows (zero test leakage).
- **Overfitting Controls:** `1.514` epochs (`max_steps=80`, effective batch size `8`), linear LR decay (`2e-4` -> `2.5e-6`), prompt-token loss masking (`labels=-100`), and step-wise validation monitoring (`eval_loss`: `2.2055` -> `2.0849` -> `2.0383` -> `2.0151`).

## 3. Verified Held-Out Evaluation (`n = 135`, Greedy Decoding)

| Metric | Baseline (`gemma-2-2b-it` 4-bit) | Fine-Tuned (`Chewie 1.2 QLoRA`) | Delta |
| :--- | ---: | ---: | ---: |
| Triage Prefix Compliance (`has_prefix`) | `0.00%` (0/135) | `88.89%` (120/135) | `+88.89 pp` |
| Clinical Safety (Excl. Prefix) | `88.15%` (119/135) | `88.89%` (120/135) | `+0.74 pp` |
| Strict Safety (Clinical + Prefix) | `0.00%` (0/135) | `79.26%` (107/135) | `+79.26 pp` |
| Contraindication Violations | `1.48%` (2/135) | `0.00%` (0/135) | `-1.48 pp` |
| Nigerian Pidgin Clinical Safety (`n=45`) | `91.11%` | `100.00%` | `+8.89 pp` |
| Yoruba Clinical Safety (`n=45`) | `75.56%` | `68.89%` | `-6.67 pp` |

*Note:* `120/120` (`100%`) wrapped `test_*.jsonl` prompts emitted the triage prefix; `0/15` raw un-wrapped `fixed_15` prompts emitted the prefix, confirming the training prompt wrapper must be used at inference time. Full details are in `experiments/chewie_1_2_fresh_experiment/FRESH_CHEWIE_1_2_EXPERIMENT_REPORT.md`.

