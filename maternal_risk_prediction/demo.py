"""
Standalone Maternal Risk Prediction Demonstration & CLI
=======================================================
Demonstrates clinical risk prediction on synthetic antenatal profiles
and provides an interactive testing CLI.
"""

import sys
import os
import json

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maternal_risk_prediction.src.predictor import MaternalRiskPredictor

BENCHMARK_PROFILES = [
    {
        "name": "Case 1: Low-Risk Primigravida (Routine ANC)",
        "description": "Healthy 24-year-old in 2nd trimester, normal BP, Hb 12.0, fasting glucose 82 mg/dL.",
        "data": {
            "age_years": 24,
            "gravidity": 1,
            "parity": 0,
            "gestational_age_weeks": 24.0,
            "bmi_pre_pregnancy": 22.5,
            "systolic_bp_mmhg": 112,
            "diastolic_bp_mmhg": 72,
            "hemoglobin_gdl": 12.0,
            "fasting_glucose_mgdl": 82,
            "proteinuria": 0,
            "hiv_status": 0,
            "anc_visits": 3
        }
    },
    {
        "name": "Case 2: Preeclampsia Risk Profile (Priority/Emergency)",
        "description": "29-year-old at 34 weeks with BP 154/98 mmHg, 2+ proteinuria, normal glucose & Hb.",
        "data": {
            "age_years": 29,
            "gravidity": 2,
            "parity": 1,
            "gestational_age_weeks": 34.0,
            "bmi_pre_pregnancy": 27.0,
            "systolic_bp_mmhg": 154,
            "diastolic_bp_mmhg": 98,
            "hemoglobin_gdl": 11.2,
            "fasting_glucose_mgdl": 85,
            "proteinuria": 2,
            "hiv_status": 0,
            "anc_visits": 5
        }
    },
    {
        "name": "Case 3: Severe Maternal Anemia (Emergency)",
        "description": "22-year-old at 30 weeks with critical hemoglobin of 5.8 g/dL, normal BP.",
        "data": {
            "age_years": 22,
            "gravidity": 3,
            "parity": 2,
            "gestational_age_weeks": 30.0,
            "bmi_pre_pregnancy": 20.1,
            "systolic_bp_mmhg": 105,
            "diastolic_bp_mmhg": 65,
            "hemoglobin_gdl": 5.8,
            "fasting_glucose_mgdl": 78,
            "proteinuria": 0,
            "hiv_status": 0,
            "anc_visits": 2
        }
    },
    {
        "name": "Case 4: Gestational Diabetes Mellitus (Priority)",
        "description": "36-year-old, BMI 31.5, fasting blood glucose 118 mg/dL at 28 weeks.",
        "data": {
            "age_years": 36,
            "gravidity": 3,
            "parity": 2,
            "gestational_age_weeks": 28.0,
            "bmi_pre_pregnancy": 31.5,
            "systolic_bp_mmhg": 125,
            "diastolic_bp_mmhg": 80,
            "hemoglobin_gdl": 11.5,
            "fasting_glucose_mgdl": 118,
            "proteinuria": 0,
            "hiv_status": 0,
            "anc_visits": 4
        }
    },
    {
        "name": "Case 5: Critical Eclampsia Danger Sign (Emergency)",
        "description": "17-year-old adolescent primigravida with severe hypertension 175/115 mmHg, proteinuria 3+.",
        "data": {
            "age_years": 17,
            "gravidity": 1,
            "parity": 0,
            "gestational_age_weeks": 36.5,
            "bmi_pre_pregnancy": 24.0,
            "systolic_bp_mmhg": 175,
            "diastolic_bp_mmhg": 115,
            "hemoglobin_gdl": 10.2,
            "fasting_glucose_mgdl": 84,
            "proteinuria": 3,
            "hiv_status": 0,
            "anc_visits": 1
        }
    }
]

def format_output(result: dict):
    print("\n" + "=" * 70)
    print(f"TRIAGE URGENCY: [{result['urgency_category']}]")
    print(f"PREDICTED RISK LEVEL: {result['predicted_risk_level'].upper()} (Confidence: {result['risk_confidence'] * 100:.1f}%)")
    print(f"PREDICTED COMPLICATION: {result['predicted_primary_complication'].replace('_', ' ').upper()} (Confidence: {result['complication_confidence'] * 100:.1f}%)")
    print("=" * 70)
    
    print("\nRisk Probabilities:")
    for k, v in result['risk_probabilities'].items():
        print(f"  - {k:<10}: {v * 100:5.1f}%")
        
    print("\nComplication Probabilities:")
    for k, v in result['complication_probabilities'].items():
        print(f"  - {k:<22}: {v * 100:5.1f}%")
        
    print("\nFlagged Biomarkers & Risk Factors:")
    if result['biomarker_flags']:
        for flag in result['biomarker_flags']:
            print(f"  [{flag['severity']}] {flag['biomarker']}: {flag['value']} -> {flag['guideline']}")
    else:
        print("  None. All clinical parameters within expected normal range.")
        
    print("\nClinical Action & Recommendation:")
    print(f"  {result['recommended_clinical_action']}")
    print("\n" + "-" * 70)
    print(result['disclaimer'])
    print("=" * 70 + "\n")

def run_benchmarks():
    print("=" * 70)
    print("MOTHERLYPULSE - STANDALONE MATERNAL RISK PREDICTION DEMO")
    print("Literature-informed ANC models trained on 30,000 synthetic patient records")
    print("=" * 70)
    predictor = MaternalRiskPredictor()
    
    for case in BENCHMARK_PROFILES:
        print(f"\n>>> Running {case['name']} <<<")
        print(f"Context: {case['description']}")
        print(f"Parameters: {json.dumps(case['data'], indent=2)}")
        res = predictor.assess_patient(case['data'])
        format_output(res)

if __name__ == "__main__":
    run_benchmarks()

