# Independent Technical Audit: Genuine Model Inference & Hybrid Integration

**Project:** MotherlyPulse Maternal and Infant Health Conversational Assistant  
**Document:** Independent Inference Implementation Audit (`INDEPENDENT_INFERENCE_IMPLEMENTATION_AUDIT.md`)  
**Audit Date:** November 2026  
**Auditor:** Senior Machine Learning Infrastructure Engineer & Backend Auditor  
**Scope:** `motherlypulse_app/eval_models/`, `motherlypulse_app/run_comparative_eval.py`, Hugging Face Checkpoints, Hardware Feasibility, and Memory Profiles  
**Overall Readiness Decision:** **NOT READY FOR GENUINE INFERENCE**  

---

## 1. Executive Summary

This independent audit conducted a comprehensive, line-by-line inspection of the MotherlyPulse codebase to determine whether the genuine model inference adapters (`genuine_adapters.py`) are correctly implemented, whether physical model loading and inference can execute on the target models (**Chewie 1.2** and **MamaBot-Llama**), and whether the comparative evaluation pipeline genuinely invokes these models.

### Primary Audit Determinations:
1. **The Comparative Evaluation Runner Does NOT Invoke Genuine Adapters:**  
   `run_comparative_eval.py` continues to import and instantiate the simulated behavioral models (`ChewieModel` and `MamaBotModel`). The newly authored `genuine_adapters.py` is completely disconnected from the benchmark execution path. All previously reported evaluation tables reflect simulated regex routing, not neural LLM inference.
2. **Physical Execution is Currently Impossible on Local Host:**  
   The local machine operates on `torch 2.9.1+cpu` with `CUDA: False` and only **1.31 GB of free system RAM**. Furthermore, essential machine learning packages (`peft`, `accelerate`, `bitsandbytes`) are **not installed**. Attempting to load either Chewie 1.2 (~4B parameters) or MamaBot-Llama (~8B parameters) would trigger immediate import errors or fatal OS Out-Of-Memory crashes.
3. **Chewie Base Model is Gated:**  
   Chewie 1.2 (`electricsheepafrica/chewie-1.2`) is a PEFT LoRA adapter whose base model is `google/medgemma-4b-it`. This base model is gated on Hugging Face, requiring an authenticated access token (`token=...`), which `genuine_adapters.py` does not pass.
4. **Profiler Metrics are Incomplete:**  
   The adapter claims to measure Time to First Token (TTFT), but invokes synchronous `model.generate()` without token streaming. TTFT is neither measured nor returned. CUDA synchronization is absent.
5. **Zero-Mock Enforcement is Verified:**  
   `genuine_adapters.py` correctly enforces zero-mock behavior: when memory is insufficient, it explicitly raises `ModelUnavailableError` rather than silently returning mock responses.

---

## 2. Model Adapter Audit (Objective 1)

### 2.1. Chewie 1.2 Adapter (`ChewieInferenceAdapter`)
- **Hugging Face Repository ID:** `electricsheepafrica/chewie-1.2` (Verified via HF Hub API).
- **Commit Revision SHA:** `c4c279559be94b84ad50bd90c14e133fec6d485a` (Verified).
- **Checkpoint Structure:** Verified as a pure PEFT LoRA adapter (`adapter_model.safetensors`, 77.1 MB). It contains zero base model weights.
- **Base Architecture:** `google/medgemma-4b-it` (Gemma 4B CausalLM).
- **LoRA Configuration:** `r=16`, `lora_alpha=16`, `target_modules=['fc1', 'k_proj', 'o_proj', 'up_proj', 'out_proj', 'down_proj', 'v_proj', 'gate_proj', 'fc2', 'q_proj']`.
- **Target Modules & Architecture Compatibility:** Compatible with Google Gemma/MedGemma architecture.
- **Tokenizer Compatibility:** Tokenizer files (`tokenizer.json`, `tokenizer.model`, `special_tokens_map.json`) exist in the adapter repo and match the Gemma vocabulary.
- **Chat Formatting:** Uses Gemma chat tokens (`<start_of_turn>user\n...<end_of_turn>\n<start_of_turn>model\n`).
- **Defects Identified:**
  1. `from peft import PeftModel` fails immediately because `peft` is not installed in the environment.
  2. `google/medgemma-4b-it` is a gated repository (`gated: auto`). `AutoModelForCausalLM.from_pretrained()` is called without `token=...`, preventing unauthenticated access.
  3. `device_map="auto"` requires `accelerate`, which is not installed.

### 2.2. MamaBot-Llama Adapter (`MamaBotInferenceAdapter`)
- **Hugging Face Repository ID:** `HelpMumHQ/MamaBot-Llama` (Verified via HF Hub API).
- **Commit Revision SHA:** `aca319cbd66f1f866112e7039ba1f99b6dd8b47f` (Verified).
- **Checkpoint Structure:** Verified as a standalone sharded safetensors model (`model-00001-of-00002.safetensors` [4.98 GB] + `model-00002-of-00002.safetensors` [1.05 GB], total 6.03 GB). Does not require external base weights.
- **Architecture:** `LlamaForCausalLM` based on Meta Llama-3.1-8B-Instruct.
- **Quantization:** Configured natively with bitsandbytes 4-bit (`load_in_4bit: true`, `bnb_4bit_quant_type: nf4`, `bnb_4bit_compute_dtype: bfloat16`).
- **Tokenizer Compatibility:** Bundles full Llama 3.1 tokenizer files (`tokenizer.json`, `tokenizer_config.json`, vocab size 128,256).
- **Chat Formatting:** Uses standard Llama 3.1 instruct tags (`<|begin_of_text|><|start_header_id|>system...`).
- **Defects Identified:**
  1. `load_in_4bit=True` fails on this host because `bitsandbytes` is not installed and CUDA is unavailable.
  2. `device_map="auto"` and `low_cpu_mem_usage=True` fail because `accelerate` is not installed.
  3. Attempting full FP16 loading requires ~16 GB RAM; host has only 1.31 GB free.

---

## 3. Genuine Inference & Zero-Mock Enforcement (Objective 2)

| Verification Dimension | Status | Audit Findings |
| :--- | :---: | :--- |
| **Code Inspection** | **PASSED** | `genuine_adapters.py` contains genuine PyTorch/Transformers generation syntax and zero regex string generators. |
| **Zero-Mock Enforcement** | **PASSED** | When loading fails, `ModelUnavailableError` is explicitly raised. No silent fallback to mock strings or simulation wrappers exists in `genuine_adapters.py`. |
| **Adapter Unit Testing** | **PASSED** | Unit tests confirm that pre-flight checks correctly identify insufficient RAM and raise `ModelUnavailableError` cleanly. |
| **Actual Weight Loading** | **FAILED** | Model weights cannot be loaded due to host RAM constraints (1.31 GB free) and missing packages (`peft`, `accelerate`, `bitsandbytes`). |
| **Actual Token Generation** | **FAILED** | No tokens have been generated by actual neural weights. |

---

## 4. Profiler Audit (Objective 3)

Inspection of `generate()` in `genuine_adapters.py` (lines 160–189 and 271–300):

1. **Time to First Token (TTFT):**  
   **NOT IMPLEMENTED / FALSE CLAIM.**  
   The docstring states that TTFT is measured. However, lines 161–167 invoke `outputs = self.model.generate(**inputs)` as a single blocking synchronous call. No token streaming callback, `TextIteratorStreamer`, or generation hook is used. TTFT is neither measured nor present in the returned dictionary.
2. **Total Generation Latency:**  
   Measured via `elapsed_sec = t_end - t_start`. However, **`torch.cuda.synchronize()` is missing**. If executed on a CUDA GPU, `time.perf_counter()` would measure asynchronous kernel launch time rather than actual generation time.
3. **Generated Token Count:**  
   Correctly computed as `len(gen_tokens)` by slicing `outputs[0][inputs["input_ids"].shape[1]:]`.
4. **Tokens per Second:**  
   Correctly formulated as `token_count / elapsed_sec`.
5. **Memory Measurement:**  
   - For CUDA: Calls `torch.cuda.max_memory_allocated()`. Valid, but lacks baseline reset (`reset_peak_memory_stats()`).
   - For CPU: Calls `psutil.Process(os.getpid()).memory_info().rss`. Measures total process resident set size, which reflects all loaded modules, datasets, and OS buffers, rather than the specific memory consumed by the generation tensor.

---

## 5. Memory Management & Sequential Execution Audit (Objective 4)

Inspection of `SequentialHybridExecutor` in `genuine_adapters.py` (lines 303–331):

1. **Sequential Loading & Unloading:**  
   The executor attempts to prevent co-residency by calling `self.mamabot_adapter.unload()` before loading Chewie, and `self.chewie_adapter.unload()` before loading MamaBot.
2. **Memory Reclamation Defect:**  
   `unload()` executes `del self.model; del self.tokenizer; gc.collect(); torch.cuda.empty_cache()`.  
   *Limitation:* In PyTorch CPU execution, Python's `del` and `gc.collect()` do not guarantee that the C++ memory allocator releases pages back to the operating system immediately. In a constrained environment (e.g. 1.31 GB free RAM), sequential swapping will still crash if unallocated memory fragmentation prevents contiguous allocation for the second model.
3. **Error State Inconsistency:**  
   If an exception occurs during `load_model()` inside `execute_independent()`, `self.active_model_name` is not updated or cleaned up, potentially leaving partial state in memory.

---

## 6. Execution Path Trace: Evaluation Runner to Model Generation (Objective 5)

Tracing the execution call graph in `run_comparative_eval.py`:

```
[run_comparative_eval.py]
  │
  ├── Line 23: from motherlypulse_app.eval_models import ChewieModel, MamaBotModel, HybridRouter, SymmetricPipeline
  │              ▲
  │              └── Imports SIMULATED models from chewie_model.py, mamabot_model.py, hybrid_router.py
  │
  ├── Line 74-76: arms = [
  │                 ("Chewie 1.2", SymmetricPipeline(ChewieModel())),
  │                 ("MamaBot-Llama", SymmetricPipeline(MamaBotModel())),
  │                 ("Hybrid Router", SymmetricPipeline(HybridRouter()))
  │               ]
  │
  ├── Line 86: pipeline.run(query=query, language=lang, topic=topic)
  │              │
  │              ▼ [symmetric_pipeline.py]
  │              ├── Line 67: triage_result = self.classifier.classify(...)
  │              └── Line 77: model_output = self.model.generate_response(...)
  │                             │
  │                             ▼ [chewie_model.py / mamabot_model.py]
  │                             └── Line 42-120: REGEX MATCHING on query_lower
  │                                 Returns hardcoded Assessment/Action/Advice template
  │
  └── MamaBench Execution (Line 206-224):
       model.generate_response(query=narrative, language="en")
       └── Evaluates simulated regexes. ZERO genuine inference invoked.
```

### Direct Answers to Objective 5 Questions:
1. **Does the comparative runner instantiate `genuine_adapters.py`?**  
   **NO.** `genuine_adapters` is neither imported nor referenced anywhere in `run_comparative_eval.py`.
2. **Does it instantiate the previous simulated models?**  
   **YES.** Lines 74–76 explicitly instantiate `ChewieModel()`, `MamaBotModel()`, and `HybridRouter()`.
3. **Does the hybrid router call actual model generation methods?**  
   **NO.** In `hybrid_router.py`, lines 26–27 instantiate `ChewieModel()` and `MamaBotModel()`.
4. **Are genuine adapters used in standalone Chewie evaluation?**  
   **NO.**
5. **Are genuine adapters used in standalone MamaBot evaluation?**  
   **NO.**
6. **Are genuine adapters used in hybrid evaluation?**  
   **NO.**
7. **Are deterministic triage rules authoritative?**  
   **YES.** In `symmetric_pipeline.py` (lines 88–96) and `hybrid_router.py` (lines 209–216), upstream danger sign triage strictly overrides model output.
8. **Can an emergency or priority classification be downgraded by a model?**  
   **NO.** The corrected router guarantees that upstream emergency stays emergency, and priority cannot fall to routine.
9. **Are model failures handled explicitly?**  
   **NO.** Neither `run_comparative_eval.py` nor `hybrid_router.py` wraps model generation calls in `try...except ModelUnavailableError`.
10. **Can evaluation results accidentally mix genuine and simulated outputs?**  
    Currently, 100% of the evaluation results in `COMPARATIVE_EVALUATION_RESULTS.md` are simulated. There is no mixing because genuine adapters are not connected.

---

## 7. Safety Arbitration Audit (Objective 6)

The corrected `hybrid_router.py` was inspected against all clinical safety requirements:

1. **Emergency & Priority Preservation:** Guaranteed. Lines 209–216 strictly enforce that `hint_urgency == "emergency"` cannot be changed, and `hint_urgency == "priority"` cannot fall to `routine`.
2. **Conservative Arbitration:** Guaranteed. Lines 180–190 evaluate `winning_rank = max(c_rank, m_rank, h_rank)`. If either model or the hint signals priority or emergency, the higher-risk category prevails (`Escalate > Defer > Reassure`).
3. **Defect Identified (Failure vs. Safety):**  
   The router lacks exception handling around model generation calls. If a model crashes or throws an exception, the system raises an unhandled error rather than routing safely to emergency escalation.

---

## 8. Hardware Readiness Profile (Objective 8)

| Component | Current State | Required State for Inference | Gap / Feasibility Status |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10.11 (64-bit) | $\ge 3.10$ | Compatible |
| **PyTorch** | 2.9.1+cpu | $\ge 2.2.0$ with CUDA 12.1+ | **INCOMPATIBLE** (CPU only) |
| **Transformers** | 5.14.1 | $\ge 4.45.0$ | Compatible |
| **PEFT** | **NOT INSTALLED** | $\ge 0.12.0$ | **CRITICAL MISSING PACKAGE** |
| **Accelerate** | **NOT INSTALLED** | $\ge 0.30.0$ | **CRITICAL MISSING PACKAGE** |
| **bitsandbytes** | **NOT INSTALLED** | $\ge 0.43.0$ | **CRITICAL MISSING PACKAGE** |
| **Hugging Face Hub** | 1.27.0 | $\ge 0.23.0$ | Compatible |
| **CUDA Available** | **False** | True ($\ge 12.1$) | **INCOMPATIBLE** |
| **GPU Model & VRAM** | None (0.0 GB) | NVIDIA GPU ($\ge 16$ GB VRAM) | **INCOMPATIBLE** |
| **Total System RAM** | 15.61 GB | $\ge 32$ GB (for CPU inference) | Insufficient for CPU execution |
| **Available RAM** | **1.31 GB** | $\ge 8.0$ GB free | **CRITICAL BOTTLENECK** |
| **Free Disk Space** | 24.63 GB | $\ge 30$ GB (for cache & weights) | Marginal (6.0 GB MamaBot + 8.5 GB MedGemma = 14.5 GB) |

### Memory Requirements Analysis:
- **Chewie 1.2:** Requires base model `google/medgemma-4b-it` (8.5 GB FP16 / 2.6 GB INT4) + LoRA adapter (77 MB) + runtime activations (~1.5 GB). Total minimum memory: **4.1 GB (INT4) / 10.0 GB (FP16)**.
- **MamaBot-Llama:** Standalone sharded safetensors (6.03 GB disk footprint) + runtime KV cache (~1.5 GB). Total minimum memory: **6.0 GB (INT4) / 16.5 GB (FP16)**.
- **Verdict:** Neither model can run on the current local host.

---

## 9. Comprehensive Findings & Severity Ledger

| Finding ID | Severity | File & Line | Evidence | Clinical & Technical Impact | Recommended Correction |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **FINDING-01** | **CRITICAL** | `run_comparative_eval.py`: 23, 74–76, 206–208 | Runner imports `ChewieModel`, `MamaBotModel`, `HybridRouter`. `genuine_adapters` is never imported or executed. | Reported evaluation results do not reflect genuine LLM capabilities. | Rewire runner and router to instantiate `genuine_adapters` with explicit execution flags. |
| **FINDING-02** | **CRITICAL** | Host Environment | Available RAM is 1.31 GB; CUDA is False; PyTorch is CPU-only. | Attempting model loading causes fatal system crash. | Provision GPU staging environment ($\ge 16$ GB VRAM) for live inference. |
| **FINDING-03** | **HIGH** | Environment Packages | `peft`, `accelerate`, and `bitsandbytes` are not installed. | Chewie adapter throws `ModuleNotFoundError: peft`; MamaBot throws `ImportError: accelerate`. | Add packages to project dependencies and install compatible versions. |
| **FINDING-04** | **HIGH** | `genuine_adapters.py`: 122–128 | `google/medgemma-4b-it` is a gated repository; adapter calls `from_pretrained` without `token=...`. | Model loading will fail with `GatedRepoError` (401 Unauthorized) even if RAM is available. | Pass `token=os.getenv("HF_TOKEN")` to tokenizer and base model loaders. |
| **FINDING-05** | **HIGH** | `genuine_adapters.py`: 160–188, 271–300 | Docstring claims TTFT measurement; code calls blocking `model.generate()`. TTFT is omitted from outputs. Missing `torch.cuda.synchronize()`. | Profiler metrics are inaccurate and misleading. | Implement `TextIteratorStreamer` for true TTFT measurement and add CUDA synchronization events. |
| **FINDING-06** | **MEDIUM** | `hybrid_router.py`: 148–205 | Router calls `chewie.generate_response()` without `try...except` exception handling. | An inference failure crashes the pipeline rather than triggering a safe fail-soft emergency escalation. | Wrap model calls in `try...except ModelUnavailableError` and enforce safe fallback escalation. |
| **FINDING-07** | **MEDIUM** | `genuine_adapters.py`: 64–79 | `unload()` does not verify memory release before loading the second model in sequential execution. | Memory fragmentation on CPU/GPU can trigger OOM during model swapping. | Monitor actual free memory after `unload()` before attempting the next load. |
| **FINDING-08** | **LOW** | `eval_models/__init__.py`: 1–19 | `genuine_adapters.py` classes are not exported. | Clean package imports are hindered. | Export `ChewieInferenceAdapter`, `MamaBotInferenceAdapter`, `SequentialHybridExecutor`, and `ModelUnavailableError`. |

---

## 10. Final Readiness Decision

### **NOT READY FOR GENUINE INFERENCE**

**Justification:**
1. The physical hardware is completely insufficient (1.31 GB free RAM, no CUDA GPU).
2. Critical dependencies (`peft`, `accelerate`, `bitsandbytes`) are absent from the environment.
3. The evaluation runner and hybrid router are not wired to `genuine_adapters.py`.
4. Chewie's base model requires Hugging Face authentication tokens that are not yet wired into the adapter.
5. The profiler does not measure true Time to First Token (TTFT).

*Audit complete.*

