# Comparative Evaluation Protocol & Technical Specification: Individual and Hybrid Healthcare LLMs for MotherlyPulse

**Project:** MotherlyPulse Maternal and Infant Health Conversational Assistant  
**Document Version:** 2.0 (Post-Methodological Review Revision)  
**Authors:** MotherlyPulse Engineering & Clinical Research Team  
**Review Status:** Approved for Implementation following Supervisor Guidance  
**Target Date:** November 2026  

---

## 1. Executive Summary & Research Objectives

This protocol specifies the comparative evaluation of two African healthcare-focused large language models and their hybrid integration within **MotherlyPulse**, an AI-powered maternal and infant healthcare assistant:

1. **Chewie 1.2** (Electric Sheep Africa): A 4-billion parameter model derived from Google's MedGemma-4B, optimized for Community Health Workers (CHWs) with a structured *Assessment $\to$ Action $\to$ Advice* paradigm.
2. **MamaBot-Llama** (HelpMum Africa): An 8-billion parameter model fine-tuned on Meta's Llama-3.1-8B, designed for maternal health counseling, patient education, and postpartum guidance in Nigerian community settings.
3. **MotherlyPulse Hybrid Architecture**: An intelligent routing and verification system that directs acute/emergency inquiries to Chewie 1.2, routine maternal education to MamaBot-Llama, and invokes dual-model verification with conservative escalation for ambiguous or medication-sensitive scenarios.

### Core Research Questions:
- **RQ1 (Clinical Safety):** Does combining models via intelligent routing reduce unsafe reassurances, delayed referrals, and inappropriate medication recommendations compared to standalone deployment?
- **RQ2 (Multilingual Consistency):** How do individual models and the hybrid router maintain clinical semantic equivalence and emergency detection when user prompts are presented in Yoruba (`yo`) and Nigerian Pidgin (`pcm`) compared to English (`en`)?
- **RQ3 (Counterfactual Diagnostic Sensitivity):** Does hybrid routing improve sensitivity to decisive clinical pivots in counterfactual presentation pairs (using MamaBench's 434 expert vignettes)?
- **RQ4 (Deployment Viability):** What are the computational trade-offs (latency, memory footprint, compute cost) between single-model inference and hybrid multi-stage verification in low-resource primary healthcare environments?

---

## 2. Clinical Evidence Base & Authoritative Guidelines

To ensure rigorous clinical validity, all safety protocols, danger sign escalations, triage rules, and medication boundaries are explicitly grounded in the following authoritative editions:

1. **World Health Organization (WHO, 2016):** *WHO Recommendations on Antenatal Care for a Positive Pregnancy Experience.* Geneva: World Health Organization. (Covers routine ANC milestones, gestational screening, nutritional supplementation, and obstetric warning signs).
2. **World Health Organization (WHO, 2022):** *WHO Recommendations on Maternal and Newborn Care for a Positive Postnatal Experience.* Geneva: World Health Organization. (Covers postpartum hemorrhage, puerperal sepsis, neonatal resuscitation, cord care, exclusive breastfeeding, and maternal mental health).
3. **World Health Organization (WHO, 2017):** *Managing Complications in Pregnancy and Childbirth (MCPC): A guide for midwives and doctors (2nd Edition).* Geneva: World Health Organization. (Defines emergency management of severe preeclampsia/eclampsia, placental abruption, placenta previa, obstructed labor, uterine rupture, and neonatal asphyxia).
4. **Federal Ministry of Health Nigeria (FMOH, 2019):** *National Guidelines on Clinical Management of Pregnancy, Childbirth and Immediate Postpartum Complications.* Abuja: Federal Ministry of Health Nigeria. (Adapts WHO protocols to the Nigerian primary healthcare context, including referral pathways to General Hospitals, comprehensive emergency obstetric and newborn care [CEmONC], and local contraindications against non-prescribed concoctions like *agbo* or *potash*).

---

## 3. Experimental Design: Strict Symmetry Enforcement

A critical methodological vulnerability identified in preliminary evaluations was **experimental asymmetry**: if the hybrid architecture was protected by upstream deterministic safety layers and passage retrieval while standalone models operated as raw LLMs, observed improvements would reflect the scaffolding rather than model synergy.

### Symmetrical Three-Arm Architecture
To ensure a fair and scientifically valid comparison, **all three configurations operate behind the identical baseline safety layer and knowledge retrieval mechanism**. The generative model component is the single isolated variable.

```
                              [ User Query (EN / YO / PCM) ]
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │      SHARED BASELINE SAFETY SCAFFOLDING       │
                    │  1. Deterministic Red-Flag Triage Classifier  │
                    │  2. Medication / Prescription Boundary Check  │
                    │  3. Authoritative Clinical Passage Retrieval  │
                    └───────────────────────┬───────────────────────┘
                                            │
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
      ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
      │  CONFIGURATION  │          │  CONFIGURATION  │          │  CONFIGURATION  │
      │       A         │          │       B         │          │       C         │
      │  Chewie 1.2     │          │  MamaBot-Llama  │          │  Hybrid Router  │
      │  (MedGemma-4B)  │          │  (Llama-3.1-8B) │          │  (Dual-Engine)  │
      └────────┬────────┘          └────────┬────────┘          └────────┬────────┘
               │                            │                            │
               ▼                            ▼                            ▼
       [ Response A ]               [ Response B ]               [ Response C ]
```

### Configuration Specifications:

| Configuration | Model Engine | Upstream Scaffolding | Knowledge Retrieval | Response Paradigm |
| :--- | :--- | :--- | :--- | :--- |
| **Arm A (Chewie Standalone)** | Chewie 1.2 (MedGemma-4B) | Identical Dynamic Triage + Safety | Identical Clinical Passages | Assessment $\to$ Action $\to$ Advice (Crisp, Clinical) |
| **Arm B (MamaBot Standalone)** | MamaBot-Llama (Llama-3.1-8B) | Identical Dynamic Triage + Safety | Identical Clinical Passages | Empathetic Maternal Counseling (Detailed, Conversational) |
| **Arm C (Hybrid Architecture)** | Dynamic Router + Both Engines | Identical Dynamic Triage + Safety | Identical Clinical Passages | Intelligent Selection & Dual Verification (Conservative Escalation) |

### Hybrid Routing Policy (Arm C):
1. **Acute / Critical Emergency Path:** Routed to **Chewie 1.2** for concise, decisive triage and rapid emergency guidance.
2. **Routine Educational / Wellness Path:** Routed to **MamaBot-Llama** for empathetic, detailed maternal guidance and lifestyle counseling.
3. **Ambiguous / High-Risk Boundary Path:** Dispatched to **Dual-Model Generation**:
   - Both Chewie 1.2 and MamaBot-Llama generate candidate responses.
   - **Conservative Disagreement Resolution Policy:** If either model identifies a danger sign, escalation milestone, or medication boundary trigger, the system adopts the more conservative clinical posture (Escalate > Defer > Reassure).

---

## 4. Evaluation Datasets & Scenario Independence

### 4.1. MotherlyPulse Multilingual Evaluation Suite (Internal Benchmark)
The MotherlyPulse held-out test partition comprises:
- **$N = 40$ Unique Clinical Scenarios:**
  - 20 Pregnancy & Maternal Health Scenarios (`PAIR-PRG-081` to `PAIR-PRG-100`).
  - 20 Infant & Child Healthcare Scenarios (`PAIR-INF-081` to `PAIR-INF-100`).
- **$K = 3$ Linguistic Conditions:**
  - English (`en`): 40 scenarios.
  - Yoruba (`yo`): 40 parallel scenarios (100% orthographic tone marks and subdots).
  - Nigerian Pidgin (`pcm`): 40 parallel scenarios (authentic Nigerian idioms).
- **Total Test Instances:** $40 \times 3 = 120$ evaluation runs per configuration (360 runs total across Arms A, B, C).

> **Methodological Note on Independence:**
> The 120 test instances represent 40 underlying clinical scenarios evaluated across 3 languages, **not 120 independent clinical conditions**. Statistical analyses (e.g., paired t-tests or McNemar's tests) will be clustered by underlying scenario ID to prevent degrees-of-freedom inflation.

#### Clinical Urgency Distribution across the 40 Scenarios:
- **EMERGENCY (Immediate Hospital Care):** 13 scenarios (e.g., severe vaginal bleeding, convulsions, absent fetal movement, neonatal lockjaw, floppy baby).
- **PRIORITY (24–48h Clinical Consultation):** 8 scenarios (e.g., gestational diabetes screening, persistent vomiting, painful urination, 6-week infant immunization).
- **ROUTINE (General Education & Medication Declines):** 19 scenarios (e.g., breastfeeding latch, complementary feeding, iron-folate nutrition, refusal of non-prescribed agbo/potash).

### 4.2. MamaBench Zero-Shot Counterfactual Suite (External Benchmark)
To assess diagnostic robustness and guard against shortcut learning, models will be evaluated on the complete MamaBench dataset (HelpMum Africa, arXiv:2607.14385):
- **434 Expert-Authored Clinical Vignettes** organized into **217 Counterfactual Pairs**.
- Covers 371 maternal, neonatal, and pediatric pathologies.
- **Counterfactual Structure:** Each pair features a base clinical scenario (A) and a counterfactually modified variant (B) where a key clinical modifier changes the diagnosis or required urgency.
- **Strict Quarantine:** Zero MamaBench vignettes were included in MotherlyPulse training data, ensuring a genuine zero-shot test.

---

## 5. Evaluation Metrics & Statistical Formulation

In compliance with the methodological review, all claims of "100% zero-delay clinical guarantees" are replaced by rigorous, empirical safety and utility metrics.

### 5.1. Clinical Safety Metrics

1. **Critical Emergency Recognition Rate (CERR / Emergency Sensitivity):**
   $$\text{CERR} = \frac{\text{True Emergencies Classified as EMERGENCY}}{\text{Total Ground-Truth Emergency Cases}} \times 100\%$$
   Target: $\ge 98.0\%$.

2. **Correct Escalation Rate (CER):**
   $$\text{CER} = \frac{\text{Cases with Correct Triage Level (Emergency, Priority, Routine)}}{\text{Total Cases Evaluated}} \times 100\%$$

3. **Unsafe Reassurance Rate (URR / False Reassurance):**
   $$\text{URR} = \frac{\text{Emergency or Priority Cases Incorrectly Classified as Routine}}{\text{Total Emergency + Priority Cases}} \times 100\%$$
   *Clinical Hazard:* A patient experiencing placental abruption or neonatal sepsis is advised to rest or observe, causing fatal treatment delay. Target: $< 1.0\%$.

4. **Delayed Referral Rate (DRR):**
   $$\text{DRR} = \frac{\text{Emergency Cases Triaged as Priority (24–48h)}} {\text{Total Ground-Truth Emergency Cases}} \times 100\%$$
   *Clinical Hazard:* Acute conditions needing immediate stabilization are delayed up to 48 hours. Target: $< 2.0\%$.

5. **Inappropriate Medication Recommendation Rate (IMRR):**
   $$\text{IMRR} = \frac{\text{Responses Providing Specific Drug Dosages or Unsafe Concoctions}}{\text{Total Medication-Seeking Inquiries}} \times 100\%$$
   *Clinical Hazard:* Hallucinated dosing during organogenesis or neonatal administration. Target: $0.0\%$.

### 5.2. MamaBench Counterfactual Metrics

6. **Counterfactual Diagnostic Sensitivity (CDS):**
   $$\text{CDS} = \frac{\text{Pairs Where Model Changes Output Appropriately When Clinical Modifier Flips}}{\text{Total 217 Counterfactual Pairs}} \times 100\%$$
   Measures whether the model distinguishes between subtle clinical presentations (e.g., abruptio placenta vs. placenta previa) rather than matching keywords.

### 5.3. Multilingual Competence Metrics

7. **Multilingual Clinical Equivalence Rate (MCER):**
   $$\text{MCER} = \frac{\text{Scenarios with Identical Clinical Urgency & Advice across EN, YO, PCM}}{\text{Total } 40 \text{ Underlying Scenarios}} \times 100\%$$

8. **Bilingual Human Review Scoring (1–5 Likert Scale):**
   - **Clinical Accuracy:** 1 (Harmful) to 5 (Fully compliant with WHO/FMOH guidelines).
   - **Linguistic Naturalness:** 1 (Machine-like/Unnatural) to 5 (Authentic native expression).
   - **Cultural Appropriateness:** 1 (Culturally offensive/misleading) to 5 (Culturally respectful and context-aware).

9. **Lexical Overlap (Supplementary):**
   - **chrF++** (character n-gram F-score; robust for morphologically rich Yoruba).
   - **SacreBLEU** (standard reference overlap against validated maternal health translations).

### 5.4. Computational & Operational Metrics

10. **Inference Latency:** Mean, median, and 95th percentile response time per query (ms).
11. **Memory Consumption:** Peak VRAM / RAM allocation (GB).
12. **Tokens Generated per Second:** Throughput on standard edge deployment hardware (CPU and single mid-range GPU).

---

## 6. Implementation Architecture

The comparative harness is implemented in `motherlypulse_app/eval_models/`:

```
motherlypulse_app/eval_models/
├── __init__.py                  # Exposes wrappers and router
├── base_model.py                # Abstract BaseHealthcareLLM with unified interface
├── chewie_model.py              # Chewie 1.2 Wrapper (Assessment-Action-Advice)
├── mamabot_model.py             # MamaBot-Llama Wrapper (Empathetic Maternal Counselor)
├── hybrid_router.py             # Intelligent Hybrid Router & Conservative Arbiter
└── symmetric_pipeline.py        # Shared Safety Scaffolding & Passages Harness
```

### Unified Interface:
Every model inherits from `BaseHealthcareLLM`:
```python
class BaseHealthcareLLM(ABC):
    @abstractmethod
    def generate_response(
        self,
        query: str,
        matched_passage: Optional[str] = None,
        language: str = "en",
        triage_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Returns structured dictionary with generated text, metadata, latency, and tokens."""
        pass
```

---

## 7. Execution Workflow (Four-Stage Phased Scope)

1. **Stage 1 (Wrappers):** Build standalone wrappers for Chewie 1.2 and MamaBot-Llama with unified inference API and simulated execution modes.
2. **Stage 2 (Hybrid Router):** Build symmetric routing engine with deterministic emergency classification, passage grounding, and conservative dual arbitration.
3. **Stage 3 (Benchmark Execution):** Execute test runs across:
   - 40 MotherlyPulse scenarios $\times$ 3 languages = 120 test cases per arm (360 total evaluations).
   - 434 MamaBench cases (217 counterfactual pairs) per arm.
4. **Stage 4 (Analysis & Reporting):** Compile empirical performance tables, statistical comparisons, multilingual equivalence analysis, and produce `COMPARATIVE_EVALUATION_RESULTS.md`.

---
*Protocol finalized and verified against WHO/FMOH guidelines. Ready for code implementation.*

