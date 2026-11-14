# MotherlyPulse: Large Language Model Deployment Readiness Assessment

**Project:** MotherlyPulse Maternal and Infant Health Conversational Assistant  
**Target Models:** Chewie 1.2 & MamaBot-Llama  
**Document Version:** 2.0 (Post-Audit Technical Review)  
**Date:** November 2026  
**Auditor:** MotherlyPulse Systems & Infrastructure Engineering  

---

## 1. Executive Summary

This document provides a technical readiness assessment for deploying genuine large language model checkpoints within MotherlyPulse, evaluating:
1. **Chewie 1.2** (Electric Sheep Africa)
2. **MamaBot-Llama** (HelpMum Africa)
3. **MotherlyPulse Hybrid Architecture** (Composite Dynamic Routing)

Both models have been verified on the Hugging Face Hub. Their weights, configurations, tokenizer files, and architecture specifications were retrieved directly via the Hugging Face API.

---

## 2. Model Specifications & Hugging Face Checkpoints

| Parameter | Configuration A: Chewie 1.2 | Configuration B: MamaBot-Llama |
| :--- | :--- | :--- |
| **Hugging Face Repository ID** | `electricsheepafrica/chewie-1.2` | `HelpMumHQ/MamaBot-Llama` |
| **Commit Revision SHA** | `c4c279559be94b84ad50bd90c14e133fec6d485a` | `aca319cbd66f1f866112e7039ba1f99b6dd8b47f` |
| **Gated / Access Restriction** | **False (Publicly Accessible)** | **False (Publicly Accessible)** |
| **Base Architecture** | Google MedGemma-4B (`google/medgemma-4b-it`) | Meta Llama-3.1-8B-Instruct (`meta-llama/Llama-3.1-8B-Instruct`) |
| **Model Type** | Causal Language Model via PEFT LoRA Adapter | Standalone Causal Language Model (`LlamaForCausalLM`) |
| **Weight Format** | `adapter_model.safetensors` | Sharded Safetensors (`model-00001-of-00002.safetensors`, `model-00002-of-00002.safetensors`) |
| **Tokenizer Components** | `tokenizer.json`, `tokenizer.model`, `special_tokens_map.json` | `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json` |
| **Chat Template** | Gemma-style (`<start_of_turn>user ... <start_of_turn>model`) | Llama-3.1-style (`<|begin_of_text|><|start_header_id|>system ...`) |
| **Quantization Config** | Standard LoRA adapter (can load with base in 4-bit) | Configured with `load_in_4bit: true`, `quant_method: bitsandbytes` |
| **Primary Target Domain** | Community Health Workers (CHWs) Clinical Decision Support | Patient Maternal Counseling, Health Literacy, and Education |

---

## 3. Physical Hardware Requirements & Memory Profiles

Because large language models place heavy demands on system memory and compute, the memory requirements of each model were evaluated independently rather than assuming both can remain co-resident in memory.

### 3.1. Standalone Execution Requirements

| Model | Precision | Minimum GPU VRAM | Minimum CPU RAM (Fallback) | Target Storage Footprint |
| :--- | :--- | :---: | :---: | :---: |
| **Chewie 1.2 (4B)** | FP16 | 9.0 GB | 12.0 GB | ~8.5 GB |
| **Chewie 1.2 (4B)** | INT4 (bitsandbytes / AWQ) | **3.0 GB** | **5.0 GB** | ~2.6 GB |
| **MamaBot-Llama (8B)** | FP16 | 16.0 GB | 20.0 GB | ~16.5 GB |
| **MamaBot-Llama (8B)** | INT4 (bitsandbytes / AWQ) | **5.5 GB** | **8.0 GB** | ~4.9 GB |

### 3.2. Hybrid Execution Strategies

Hosting both Chewie 1.2 (4B) and MamaBot-Llama (8B) simultaneously in FP16 requires over **25 GB VRAM**, which exceeds standard consumer edge hardware. To achieve cost-effective and reliable deployment in Nigerian healthcare clinics, three operational modes are defined:

1. **Sequential Model Swapping (Edge Mode):**
   - Implemented in `motherlypulse_app/eval_models/genuine_adapters.py` via `SequentialHybridExecutor`.
   - Only one model resides in RAM/VRAM at any instant.
   - When switching between Chewie (emergency) and MamaBot (routine), the inactive model is unmapped (`torch.cuda.empty_cache()`, `gc.collect()`), allowing execution within **8 GB VRAM**.
2. **Dual-Model INT4 Co-residency (Facility Server Mode):**
   - Both models loaded in 4-bit quantization (bitsandbytes NF4 or AWQ).
   - Chewie (4B INT4) = 2.6 GB + MamaBot (8B INT4) = 4.9 GB + KV Cache = **~8.2 GB Peak VRAM**.
   - Deployable on a single mid-range GPU (e.g. NVIDIA RTX 3060 12GB or RTX 4070 12GB).
3. **Decoupled Microservice Architecture (Cloud / Regional PHC Mode):**
   - Chewie 1.2 deployed as a high-speed emergency endpoint.
   - MamaBot-Llama deployed as an empathetic conversational endpoint.
   - The Hybrid Router dispatches HTTP/gRPC requests according to triage severity.

---

## 4. Current Host Environment Diagnostics

An inspection of the current execution environment was conducted using `HardwareProfile.get_profile()`:

```json
{
  "cuda_available": false,
  "gpu_name": null,
  "gpu_vram_gb": 0.0,
  "total_ram_gb": 15.61,
  "available_ram_gb": 2.16,
  "cpu_count": 8,
  "os_platform": "win32"
}
```

### Deployment Bottleneck Analysis:
1. **CUDA Acceleration is Absent:** The active Python environment uses `torch 2.9.1+cpu`. Token generation on CPU for an 8B model would incur high latency (estimated 15–45 seconds per response).
2. **Available RAM Constraint:** While total RAM is 15.61 GB, currently available RAM is **2.16 GB**. Attempting to load an unquantized 8B or 4B model into 2.16 GB would cause an Out-Of-Memory (OOM) operating system crash.
3. **Guard Implemented:** `ChewieInferenceAdapter` and `MamaBotInferenceAdapter` enforce pre-flight memory checks and raise an explicit `ModelUnavailableError` rather than crashing the operating system or silently falling back to mock strings.

---

## 5. Licensing, Ethics, and Regulatory Compliance

1. **Chewie 1.2:**
   - Governed by Google's Gemma Terms of Use.
   - Prohibits fully autonomous clinical decision-making; designed for Community Health Worker decision support.
2. **MamaBot-Llama:**
   - Governed by the Meta Llama 3.1 Community License Agreement.
   - Prohibits generating autonomous medical prescriptions or drug dosages.
   - Adheres to HelpMum Africa's ethical guidelines requiring clinical supervision and escalation to human healthcare workers.
3. **MotherlyPulse Safety Invariants:**
   - Deterministic safety overrides (`DynamicTriageClassifier`) take precedence over all LLM outputs.
   - Strict category prefixes (`EMERGENCY:`, `PRIORITY:`, `ROUTINE:`) must be prepended to all generated patient advice.
   - Inappropriate medication requests must be refused with 0.0% leakage.

---

## 6. Action Plan for Live Model Benchmarking

To execute the full comparative evaluation using genuine neural weights:
1. Provision a GPU-accelerated staging environment with $\ge 16$ GB VRAM (e.g., Google Cloud A10G, AWS g5.xlarge, or RunPod RTX 4090).
2. Install GPU-accelerated PyTorch: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`.
3. Install quantization drivers: `pip install bitsandbytes accelerate peft`.
4. Run `python -m motherlypulse_app.eval_models.genuine_adapters` to benchmark actual inference latency (TTFT), real token generation rates (tokens/sec), and true peak VRAM.

