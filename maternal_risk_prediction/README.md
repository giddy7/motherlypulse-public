# Maternal Health & Pregnancy Risk Prediction Module

This module is an isolated, literature-informed machine learning and clinical triage component for Antenatal Care (ANC) risk assessment. It was developed using data from the [gidey7/maternal-health-pregnancy-bucket](https://huggingface.co/buckets/gidey7/maternal-health-pregnancy-bucket) Hugging Face repository.

> **Isolation Notice:** All code, data, models, and tests reside entirely in this directory (`maternal_risk_prediction/`). The existing MotherlyPulse conversational dataset (`MotherlyPulse_Data/`) and runtime application (`motherlypulse_app/`) remain completely untouched to preserve operational stability.

---

## 1. Directory Structure

```text
maternal_risk_prediction/
├── data/
│   ├── DATASET_README.md               # Original Hugging Face dataset documentation
│   ├── maternal_low_burden.csv         # 10,000 records (urban LMIC setting)
│   ├── maternal_moderate_burden.csv    # 10,000 records (district LMIC setting)
│   ├── maternal_high_burden.csv        # 10,000 records (under-resourced setting)
│   ├── generate_dataset.py             # Data generator script
│   ├── validate_dataset.py             # Data validation script
│   └── requirements.txt                # Upstream dependencies
├── models/
│   ├── risk_level_model.joblib         # Trained Random Forest risk level classifier
│   ├── complication_model.joblib       # Trained Random Forest complication classifier
│   └── model_metadata.json             # Model metrics, feature lists, and class mappings
├── src/
│   ├── __init__.py
│   ├── train_model.py                  # Model training and evaluation pipeline
│   ├── predictor.py                    # MaternalRiskPredictor with WHO triage rules
│   └── api_stub.py                     # Clean entry point for future application integration
├── demo.py                             # Standalone interactive CLI & clinical test suite
├── test_prediction.py                  # Automated unit and integration tests
├── download_data.py                    # Dataset downloader utility
└── README.md                           # This documentation
```

---

## 2. Dataset Overview

The dataset contains **30,000 synthetic patient records** modeled after WHO antenatal care guidelines and global maternal health epidemiology across three burden tiers:
- **Low-Burden Setting** (10,000 records): Urban LMIC with functional ANC infrastructure.
- **Moderate-Burden Setting** (10,000 records): Average LMIC district health center.
- **High-Burden Setting** (10,000 records): Under-resourced facility with higher prevalence of anemia and HIV.

### Clinical Parameters (Input Features)
1. Demographics & Obstetric History: `age_years`, `gravidity`, `parity`, `gestational_age_weeks`, `bmi_pre_pregnancy`.
2. Physiological & Laboratory Biomarkers:
   - `systolic_bp_mmhg` (Systolic Blood Pressure, mmHg)
   - `diastolic_bp_mmhg` (Diastolic Blood Pressure, mmHg)
   - `hemoglobin_gdl` (Hemoglobin, g/dL)
   - `fasting_glucose_mgdl` (Fasting Blood Glucose, mg/dL)
   - `proteinuria` (Dipstick protein: 0=none, 1=trace, 2=1+, 3=2+, 4=3+)
   - `hiv_status` (0=negative, 1=positive)
   - `anc_visits` (Number of antenatal visits attended)
3. Derived Obstetric Indicators:
   - Mean Arterial Pressure (MAP) = $(2 \times \text{DBP} + \text{SBP}) / 3$
   - Pulse Pressure = $\text{SBP} - \text{DBP}$
   - Clinically flagged risk indicators: adolescent pregnancy ($<18$), advanced maternal age ($\ge 35$), primigravida, gestational hypertension, and severe hypertension.

---

## 3. Model Architecture & Performance

Trained using balanced Random Forest classifiers on a 80/20 stratified train-test split (24,000 training records, 6,000 holdout test records).

### A. Risk Level Classifier (`risk_level`)
- **Overall Accuracy:** `94.0%`
- **Balanced Accuracy:** `92.7%`

| Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **High** | 1.00 | 0.84 | 0.91 | 1,468 |
| **Low** | 0.96 | 0.99 | 0.97 | 2,420 |
| **Moderate** | 0.89 | 0.95 | 0.92 | 2,112 |

### B. Complication Classifier (`primary_complication`)
- **Balanced Accuracy:** `77.6%`
- **Preeclampsia F1:** `0.95` (Precision 0.93, Recall 0.96)
- **Severe Anemia F1:** `0.89` (Precision 0.84, Recall 0.95)
- **Gestational Diabetes F1:** `0.76` (Precision 0.77, Recall 0.75)
- **Hemorrhage Recall:** `0.71`
- **Eclampsia F1:** `0.59` (Precision 0.67, Recall 0.52)

---

## 4. Clinical Triage Integration Logic

The `MaternalRiskPredictor` couples machine learning probability scores with WHO Antenatal Care clinical triage rules:

1. **EMERGENCY Priority:**
   - Triggered if predicted risk is `high`, predicted complication is `eclampsia`, `severe_anemia`, or `hemorrhage`, or if critical danger signs are detected (SBP $\ge 160$, DBP $\ge 110$ mmHg, or $\text{Hb} < 7.0$ g/dL).
   - *Clinical Action:* Immediate stabilization, magnesium sulfate protocol if severe preeclampsia/eclampsia, and urgent referral to a Comprehensive Emergency Obstetric and Newborn Care (CEmONC) facility.

2. **PRIORITY Assessment:**
   - Triggered if predicted risk is `moderate` or complications include `preeclampsia` or `gestational_diabetes` (fasting glucose $\ge 92$ mg/dL).
   - *Clinical Action:* Medical evaluation within 24–48 hours, confirmatory laboratory tests (repeat BP monitoring, OGTT, full blood count), and targeted treatment.

3. **ROUTINE Guidance:**
   - Triggered for low-risk presentations within standard physiological thresholds.
   - *Clinical Action:* Continue WHO 8-contact ANC schedule, iron-folic acid supplementation, maternal danger sign counseling, and routine fetal movement tracking.

---

## 5. Usage & Verification

### Running the Demonstration CLI
To execute the automated benchmark cases covering Routine, Preeclampsia, Severe Anemia, Gestational Diabetes, and Eclampsia danger signs:

```powershell
python maternal_risk_prediction/demo.py
```

### Running Unit & Integration Tests
To verify input validation, model loading, biomarker extraction, and triage logic:

```powershell
python maternal_risk_prediction/test_prediction.py
```

### Retraining the Models
To retrain the classifiers and re-generate `models/` artifacts:

```powershell
python maternal_risk_prediction/src/train_model.py
```

---

## 6. Future Integration Interface

When ready to integrate with the main MotherlyPulse assistant (`motherlypulse_app`), simply import and call `assess_maternal_risk`:

```python
from maternal_risk_prediction.src.api_stub import assess_maternal_risk

patient_data = {
    "age_years": 28,
    "gravidity": 2,
    "parity": 1,
    "gestational_age_weeks": 32.0,
    "bmi_pre_pregnancy": 26.5,
    "systolic_bp_mmhg": 145,
    "diastolic_bp_mmhg": 92,
    "hemoglobin_gdl": 10.5,
    "fasting_glucose_mgdl": 88,
    "proteinuria": 2,
    "hiv_status": 0,
    "anc_visits": 4
}

assessment = assess_maternal_risk(patient_data)
# assessment contains:
# - predicted_risk_level ('low' | 'moderate' | 'high')
# - predicted_primary_complication ('none' | 'preeclampsia' | 'gestational_diabetes' | ...)
# - risk_probabilities & complication_probabilities
# - biomarker_flags (list of flagged clinical anomalies)
# - urgency_category ('EMERGENCY' | 'PRIORITY' | 'ROUTINE')
# - recommended_clinical_action (grounded WHO guidance)
```

