# MotherlyPulse: Genuine Model Inference & Hybrid Integration Remediation Plan

**Project:** MotherlyPulse Maternal and Infant Health Conversational Assistant  
**Document:** Inference Remediation Plan (`INFERENCE_REMEDIATION_PLAN.md`)  
**Audit Reference:** `INDEPENDENT_INFERENCE_IMPLEMENTATION_AUDIT.md`  
**Date:** November 2026  
**Status:** PROPOSED — PENDING APPROVAL (DO NOT IMPLEMENT UNTIL APPROVED)  

---

## 1. Overview & Remediation Objectives

This document establishes a prioritized, step-by-step engineering plan to resolve the 8 findings identified in the Independent Technical Audit. 

The remediation is structured into six technical domains:
1. **Critical Fixes (Execution Path & Pipeline Decoupling)**
2. **Model Loading & Authentication Fixes**
3. **Hybrid Router Exception Handling & Fail-Safe Routing**
4. **Profiler Modernization (True TTFT & CUDA Sync)**
5. **Hardware & Environment Staging Plan**
6. **Final Genuine Inference Verification Procedure**

---

## 2. Prioritized Remediation Actions

### Domain 1: Critical Fixes (Evaluation Path Wiring)

#### Action 1.1: Connect `run_comparative_eval.py` to Genuine Inference Adapters
- **Finding ID:** `FINDING-01` (CRITICAL)
- **Affected File:** [`motherlypulse_app/run_comparative_eval.py`](motherlypulse_app/run_comparative_eval.py)
- **Problem:** Runner instantiates `ChewieModel` and `MamaBotModel` from simulation files.
- **Proposed Solution:**
  1. Add an explicit execution mode flag: `--mode [simulated|genuine]`.
  2. In `--mode genuine`, instantiate `ChewieInferenceAdapter`, `MamaBotInferenceAdapter`, and a genuinely wired `HybridRouter`.
  3. If genuine models are selected but cannot run, cleanly halt execution with `ModelUnavailableError` rather than falling back.
  4. Save genuine outputs to distinct files: `comparative_eval_genuine_raw.csv` and `mamabench_genuine_raw.csv`.
- **Verification Test:** Run with `--mode genuine` on un-provisioned host; verify that `ModelUnavailableError` is caught and logged with hardware diagnostics, and zero mock outputs are written.

---

### Domain 2: Model Loading & Authentication Fixes

#### Action 2.1: Add Hugging Face Token Authentication to `ChewieInferenceAdapter`
- **Finding ID:** `FINDING-04` (HIGH)
- **Affected File:** [`motherlypulse_app/eval_models/genuine_adapters.py`](motherlypulse_app/eval_models/genuine_adapters.py) (Lines 116–128)
- **Problem:** `google/medgemma-4b-it` is a gated repository; loading without an authentication token causes HTTP 401 Unauthorized errors.
- **Proposed Solution:**
  1. Read token from environment: `token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")`.
  2. Pass `token=token` to both `AutoTokenizer.from_pretrained()` and `AutoModelForCausalLM.from_pretrained()`.
  3. Provide an explicit error message instructing the user to accept Google Gemma terms and run `huggingface-cli login` if the token is missing.
- **Verification Test:** Unit test checking that missing `HF_TOKEN` raises a clear `ModelUnavailableError` specifying gated model acceptance.

#### Action 2.2: Add Dependencies to Project Requirements
- **Finding ID:** `FINDING-03` (HIGH)
- **Affected File:** Project dependencies / `requirements.txt`
- **Problem:** `peft`, `accelerate`, and `bitsandbytes` are missing.
- **Proposed Solution:**
  - Define exact compatible versions:
    ```text
    peft>=0.12.0
    accelerate>=0.33.0
    bitsandbytes>=0.43.0
    ```
- **Verification Test:** Import test in Python verifying that `peft.PeftModel`, `accelerate.init_empty_weights`, and `bitsandbytes` load without import errors.

---

### Domain 3: Hybrid Router Exception Handling & Fail-Safe Routing

#### Action 3.1: Implement Fail-Safe Exception Handling in `HybridRouter`
- **Finding ID:** `FINDING-06` (MEDIUM)
- **Affected File:** [`motherlypulse_app/eval_models/hybrid_router.py`](motherlypulse_app/eval_models/hybrid_router.py) (Lines 145–205)
- **Problem:** Unhandled exceptions during model generation cause pipeline crashes; unclassified model responses risk defaulting to routine.
- **Proposed Solution:**
  1. Wrap all model generation invocations in `try...except Exception as e:`.
  2. Clinical Invariant: **A technical failure must never be interpreted as evidence that a patient is safe.**
  3. If a model fails on an emergency or priority query, fail-safe to deterministic emergency escalation with appropriate hotlines (National 112 / ODEMSA).
  4. Log model failure status in returned metadata: `{"error_occurred": True, "error_type": str(e)}`.
- **Verification Test:** Unit test with a fault-injected model wrapper throwing `RuntimeError("CUDA OOM")`; verify the router safely escalates to `emergency` without crashing.

#### Action 3.2: Export Genuine Adapters in Package Init
- **Finding ID:** `FINDING-08` (LOW)
- **Affected File:** [`motherlypulse_app/eval_models/__init__.py`](motherlypulse_app/eval_models/__init__.py)
- **Proposed Solution:** Export `ChewieInferenceAdapter`, `MamaBotInferenceAdapter`, `SequentialHybridExecutor`, and `ModelUnavailableError`.
- **Verification Test:** Verify `from motherlypulse_app.eval_models import ChewieInferenceAdapter, MamaBotInferenceAdapter` succeeds.

---

### Domain 4: Profiler Modernization

#### Action 4.1: Implement True Time to First Token (TTFT) via Streaming
- **Finding ID:** `FINDING-05` (HIGH)
- **Affected File:** [`motherlypulse_app/eval_models/genuine_adapters.py`](motherlypulse_app/eval_models/genuine_adapters.py) (Lines 160–189, 271–300)
- **Problem:** Blocking `model.generate()` cannot measure TTFT.
- **Proposed Solution:**
  1. Use a separate background thread with `transformers.TextIteratorStreamer`.
  2. Record `t_first_token = time.perf_counter()` when the first token is yielded by the streamer iterator.
  3. Compute `ttft_ms = (t_first_token - t_start) * 1000.0`.
  4. Return `time_to_first_token_ms` in the output dictionary.
- **Verification Test:** Unit test measuring streaming generation on a lightweight dummy model; verify `ttft_ms > 0` and `ttft_ms < total_latency_ms`.

#### Action 4.2: Add CUDA Synchronization to Latency Timing
- **Finding ID:** `FINDING-05` (HIGH)
- **Affected File:** [`motherlypulse_app/eval_models/genuine_adapters.py`](motherlypulse_app/eval_models/genuine_adapters.py)
- **Proposed Solution:**
  - Before timing: `if torch.cuda.is_available(): torch.cuda.synchronize()`
  - After generation: `if torch.cuda.is_available(): torch.cuda.synchronize()`
  - Alternatively, use `torch.cuda.Event(enable_timing=True)` for GPU execution.
- **Verification Test:** Profile GPU execution; confirm GPU kernel time is fully captured.

---

### Domain 5: Hardware & Environment Staging Requirements

#### Action 5.1: Minimum Deployment Environment Provisioning
- **Finding ID:** `FINDING-02` (CRITICAL)
- **Target Specification:**
  - **Option A (Cloud GPU VM - Recommended):** Single NVIDIA GPU with $\ge 16$ GB VRAM (e.g. AWS `g5.xlarge` with A10G 24GB, or Google Cloud `g2-standard-4` with L4 24GB).
  - **Option B (High-RAM CPU Staging):** Linux/Windows host with $\ge 32$ GB physical RAM for INT4 quantized CPU execution via `llama.cpp` or CTranslate2.
- **Storage Requirement:** Minimum 40 GB free SSD disk space for Hugging Face cache (`~15 GB` total weight footprint).

---

### Domain 6: Final Genuine Inference Verification Procedure

Once the fixes are implemented in a staged environment:
1. **Step 1:** Run `HardwareProfile.get_profile()` to verify CUDA and VRAM availability.
2. **Step 2:** Execute standalone Chewie test on a single emergency query (`PAIR-PRG-081`); verify real token output, TTFT, and CUDA memory.
3. **Step 3:** Execute standalone MamaBot test on a single routine query (`PAIR-PRG-095`); verify real token output, TTFT, and CUDA memory.
4. **Step 4:** Execute `SequentialHybridExecutor` swapping test; verify memory drops to zero between model unloads.
5. **Step 5:** Execute the full 120 MotherlyPulse multilingual test runs with genuine inference.
6. **Step 6:** Execute MamaBench 434-case counterfactual evaluation with genuine inference.
7. **Step 7:** Compile verified, genuine clinical results into `GENUINE_EVALUATION_RESULTS.md`.

---
*Remediation plan formulated. Awaiting supervisor/user approval before applying code changes.*

