# Technical Audit: Model Execution & Inference Verification Evidence

**Project:** MotherlyPulse Maternal and Infant Health Conversational Assistant  
**Document:** Model Execution Evidence (`MODEL_EXECUTION_EVIDENCE.md`)  
**Audit Date:** November 2026  
**Auditor:** MotherlyPulse Quality Assurance & Clinical Evaluation Unit  
**Status:** COMPLETE — TECHNICAL AUDIT DELIVERABLE  

---

## 1. Executive Summary & Verification Classification

This technical audit investigates whether the comparative evaluation of **Chewie 1.2** (Electric Sheep Africa, MedGemma-4B), **MamaBot-Llama** (HelpMum Africa, Llama-3.1-8B), and the **MotherlyPulse Hybrid Router** was executed using live autoregressive neural network inference or simulated behavioral logic.

### Verification Classification:
- **Actual LLM Weights Loaded:** **INVALID / UNVERIFIED** (No live PyTorch, Hugging Face `transformers`, or ONNX model checkpoints were loaded into host RAM or GPU VRAM).
- **Inference Nature:** **SIMULATED BEHAVIORAL LOGIC** (Deterministic pattern-matching engines returning structured clinical templates based on WHO/FMOH guidelines).
- **Latency & Memory Measurements:** **SYNTHETIC CONSTANTS** (Hardcoded baseline estimates in model wrappers; not measured via CUDA events or OS process profilers).
- **Upstream Safety Scaffolding:** **VERIFIED** (The `DynamicTriageClassifier` and passage retrieval executed real algorithmic processing across the 120 MotherlyPulse instances and 434 MamaBench cases).

---

## 2. Model Repository & Checkpoint Identifiers

The models targeted for this comparative study represent specialized African healthcare AI implementations:

| Attribute | Configuration A (Chewie 1.2) | Configuration B (MamaBot-Llama) | Configuration C (Hybrid Router) |
| :--- | :--- | :--- | :--- |
| **Developer Organization** | Electric Sheep Africa | HelpMum Africa | MotherlyPulse Systems |
| **Foundation Architecture** | Google MedGemma-4B (`google/medgemma-4b`) | Meta Llama-3.1-8B-Instruct (`meta-llama/Llama-3.1-8B-Instruct`) | Dual-Engine Composite (MedGemma-4B + Llama-3.1-8B) |
| **Parameter Scale** | 4.0 Billion Parameters | 8.0 Billion Parameters | 12.0 Billion Parameters (Dynamic Routing) |
| **Target Deployment** | Android Edge / CHW Field Tablets | Primary Healthcare Facility Servers | Maternal Health Cloud / Regional PHC Server |
| **Target Quantization** | INT4 (AWQ / GPTQ) | INT4 (AWQ / GPTQ) | INT4 Dynamic Allocation |
| **Reported Checkpoint ID** | `electricsheep/chewie-1.2-medgemma-4b` | `helpmum/mamabot-llama-3.1-8b-instruct` | Internal Composite Orchestrator |

---

## 3. Code Inspection & Loading Verification

An inspection of the codebase confirms that **no live machine learning framework loaded tensor weights during the evaluation run**.

### A. Dependency & Import Audit
In `motherlypulse_app/eval_models/base_model.py`, `chewie_model.py`, and `mamabot_model.py`:
- `import torch` is **absent**.
- `import transformers` or `from transformers import AutoModelForCausalLM, AutoTokenizer` is **absent**.
- `import onnxruntime` or `import ctranslate2` is **absent**.
- The only imported libraries are Python built-ins: `os`, `sys`, `time`, `re`, `unicodedata`, `math`, and `pandas`.

### B. Instantiation Audit
Inspection of `ChewieModel.__init__()` in [`eval_models/chewie_model.py`](motherlypulse_app/eval_models/chewie_model.py):
```python
class ChewieModel(BaseHealthcareLLM):
    def __init__(self, device: str = "cpu"):
        super().__init__(
            name="Chewie 1.2",
            model_family="MedGemma-4B",
            parameter_size="4B",
            developer="Electric Sheep Africa",
            paradigm="Assessment -> Action -> Advice (CHW Triage)",
            device=device
        )
        self.base_latency_ms = 185.0
        self.memory_footprint_mb = 2450.0  # Synthetic constant
```
**Finding:** No model initialization occurs. The wrapper sets static metadata variables and synthetic constants (`self.base_latency_ms = 185.0`, `self.memory_footprint_mb = 2450.0`).

### C. Instantiation Audit
Inspection of `MamaBotModel.__init__()` in [`eval_models/mamabot_model.py`](motherlypulse_app/eval_models/mamabot_model.py):
```python
class MamaBotModel(BaseHealthcareLLM):
    def __init__(self, device: str = "cpu"):
        super().__init__(
            name="MamaBot-Llama",
            model_family="Llama-3.1-8B",
            parameter_size="8B",
            developer="HelpMum Africa",
            paradigm="Empathetic Maternal Counseling & Community Education",
            device=device
        )
        self.base_latency_ms = 460.0
        self.memory_footprint_mb = 4850.0  # Synthetic constant
```
**Finding:** Identical pattern. No tokenizer is initialized; no weights are downloaded from Hugging Face or loaded from disk.

---

## 4. Inference Mechanism Audit: Why Chewie and MamaBot Produced Identical Metrics

Audit review observed that **Chewie 1.2 and MamaBot-Llama produced identical values across almost every clinical metric**:
- CER: 81.67%
- CERR: 74.36%
- URR: 6.35%
- DRR: 17.95%
- IMRR: 0.0%
- MCER: 57.50%
- MamaBench Critical Recall: 68.18%
- MamaBench Counterfactual Sensitivity: 14.29%

### Root Cause Analysis:
Both wrappers (`chewie_model.py` and `mamabot_model.py`) contained **verbatim duplicate regex classification logic**:

```python
# Both chewie_model.py and mamabot_model.py contain:
emergency_indicators = [
    "bleed", "blood", "haemorrhage", "hemorrhage", "convuls", "seiz", "fit", "faint", "unconscious",
    "severe headache", "blur", "vision", "epigastric", "cannot breathe", "struggling to breathe",
    "gasping", "not breathing", "cyanosis", "blue lips", "floppy", "not feeding", "cannot suck",
    "lockjaw", "trismus", "rigid", "abruptio", "previa", "cord", "water broke", "projectile vomiting", ...
]
is_emergency = any(ind in query_lower for ind in emergency_indicators) or (triage_hint == "emergency")

priority_indicators = [
    "vomit", "fever", "pain", "urine", "burn", "sugar", "glucose", "appointment", "vaccine", ...
]
is_priority = any(ind in query_lower for ind in priority_indicators) or (triage_hint == "priority")
```

### The Determination Chain:
1. When queries passed through `SymmetricPipeline.run()`, both models received the **exact same `triage_hint`** from the upstream `DynamicTriageClassifier`.
2. When evaluating MamaBench narratives (where `triage_hint` was None), both models evaluated the **identical regex indicator lists**.
3. Therefore:
   - For every single query in MotherlyPulse (120/120 instances), `chewie.generate_response()` and `mamabot.generate_response()` assigned the **exact same `urgency_category`**!
   - For every single narrative in MamaBench (434/434 cases), `chewie` and `mamabot` assigned the **exact same `urgency_category`** (168 emergency, 187 priority, 79 routine)!
4. The generated textual responses differed in styling (Chewie generated *Assessment $\to$ Action $\to$ Advice*; MamaBot generated empathetic paragraphs), but because the clinical metrics evaluate the **urgency category** (`predicted_urgency`), the resulting statistics were mathematically identical!

---

## 5. Audit of Latency and Memory Measurements

The reported hardware benchmarking figures must be classified as **INVALID**:

| Metric | Reported Value | Audit Source | Physical Reality |
| :--- | :--- | :--- | :--- |
| **Chewie Latency** | `185.0 ms` | `elapsed_ms = (time.perf_counter() - start_time) * 1000.0 + self.base_latency_ms` | In simulated mode, `perf_counter` took 0.02 ms. The reported 185 ms is simply the hardcoded constant `185.0`. |
| **MamaBot Latency** | `460.0 ms` | Hardcoded constant `460.0` in `self.base_latency_ms`. | Constant synthetic baseline. |
| **Hybrid Latency** | `398.5 ms` | Linear synthetic formula: `max(chewie, mamabot) + 18.0 + 25.0` on dual paths; `single + 18.0` on routed paths. | Computed synthetic calculation. |
| **Chewie Memory** | `2,450.0 MB` | Hardcoded constant `self.memory_footprint_mb = 2450.0`. | No GPU VRAM was allocated or queried (`torch.cuda.max_memory_allocated()` was not called). |
| **MamaBot Memory** | `4,850.0 MB` | Hardcoded constant `self.memory_footprint_mb = 4850.0`. | Constant synthetic baseline. |

---

## 6. Prerequisites for Genuine Live LLM Benchmarking

To transition from this structural and behavioral evaluation to genuine neural model benchmarking, the following technical environment must be established:

1. **Hardware Infrastructure:**
   - Single NVIDIA GPU with $\ge 16$ GB VRAM (e.g., RTX 4080/4090, A4000/A5000, or cloud T4/A10G).
   - Alternatively, 8-bit or 4-bit CPU quantization via `llama.cpp` / `ctransformers` / `ctranslate2` (requires $\ge 16$ GB system RAM).
2. **Access Credentials & Weights:**
   - Hugging Face access token authorized for `meta-llama/Llama-3.1-8B-Instruct`.
   - Access to Electric Sheep Africa's MedGemma-4B weights (`electricsheep/chewie-1.2-medgemma-4b`).
3. **Benchmarking Profiler Implementation:**
   - Real PyTorch CUDA event timing:
     ```python
     torch.cuda.synchronize()
     start_event = torch.cuda.Event(enable_timing=True)
     end_event = torch.cuda.Event(enable_timing=True)
     start_event.record()
     outputs = model.generate(**inputs, max_new_tokens=256)
     end_event.record()
     torch.cuda.synchronize()
     real_latency_ms = start_event.elapsed_time(end_event)
     peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
     ```
   - Time-to-first-token (TTFT) tracking via custom streaming iterator.

---

## 7. Audit Conclusion

The comparative evaluation was conducted using a **behavioral simulation harness** rather than live model weight execution. While this harness successfully validates the routing architecture, the symmetrical baseline scaffolding, and the metric calculation pipeline, the numerical outputs reflect **rule-based simulation rather than live neural model capabilities**.

*All findings in this document have been verified directly against the codebase.*

