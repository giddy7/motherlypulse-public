---
license: cc-by-4.0
task_categories:
- question-answering
- text-classification
language:
- en
tags:
- medical
- healthcare
- clinical-nlp
- benchmark
- counterfactual
- llm-evaluation
- maternal-health
- child-health
- robustness
pretty_name: MamaBench
size_categories:
- n<1K
---

# Dataset Card for MamaBench

## Dataset Description

- **Paper:** https://arxiv.org/abs/2607.14385
- **Organization:** HelpMum Africa
- **Bucket Source:** https://huggingface.co/buckets/gidey7/MamaBench-bucket

### Dataset Summary

MamaBench is a counterfactual clinical benchmark for evaluating the robustness of large language models on maternal and child health diagnostic reasoning. It consists of **217 counterfactual case pairs**, each pairing an original clinical vignette with a systematically perturbed counterfactual variant, designed to test whether a model's diagnostic reasoning is sensitive to clinically meaningful changes rather than relying on surface-level pattern matching.

MamaBench is released as a **single, unsplit evaluation set**. It is intended exclusively for **zero-shot evaluation**.

### Data Fields

- `case_id`: `string` — unique identifier for an individual case
- `pair_id`: `string` — shared identifier linking a case to its counterfactual partner (217 pairs = 434 cases)
- `narrative`: `string` — first-person clinical presentation narrative
- `ground_truth`: `string` — the correct diagnosis for that specific narrative

