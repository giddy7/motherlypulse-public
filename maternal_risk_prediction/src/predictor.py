"""
Maternal Risk Predictor Module
==============================
Standalone clinical risk assessment engine for pregnant patients presenting for Antenatal Care (ANC).
Utilizes trained Random Forest models to evaluate:
1. Overall Maternal Risk Level ('low', 'moderate', 'high')
2. Primary Pregnancy Complication ('none', 'preeclampsia', 'gestational_diabetes',
                                  'severe_anemia', 'hemorrhage', 'eclampsia')
3. Clinical Biomarker Flags & WHO ANC grounded triage recommendations.
"""

import os
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
ROOT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")

class MaternalRiskPredictor:
    def __init__(self, model_dir=None):
        if model_dir is None:
            # Check default maternal_risk_prediction/models then root models/
            if os.path.exists(os.path.join(MODEL_DIR, "risk_level_model.joblib")):
                model_dir = MODEL_DIR
            elif os.path.exists(os.path.join(ROOT_MODEL_DIR, "risk_level_model.joblib")):
                model_dir = ROOT_MODEL_DIR
            else:
                model_dir = MODEL_DIR

        self.risk_path = os.path.join(model_dir, "risk_level_model.joblib")
        self.comp_path = os.path.join(model_dir, "complication_model.joblib")
        
        if not os.path.exists(self.risk_path) or not os.path.exists(self.comp_path):
            raise FileNotFoundError(
                f"Model files not found in {model_dir}. Please run train_model.py first."
            )
            
        self.risk_bundle = joblib.load(self.risk_path)
        self.comp_bundle = joblib.load(self.comp_path)
        
        self.risk_model = self.risk_bundle['model']
        self.risk_classes = self.risk_bundle['classes']
        
        self.comp_model = self.comp_bundle['model']
        self.comp_classes = self.comp_bundle['classes']
        
        self.feature_cols = self.risk_bundle['feature_cols']

    def validate_and_prepare_input(self, data: dict) -> pd.DataFrame:
        """Validate input values and compute derived clinical features."""
        required = [
            'age_years', 'gravidity', 'parity', 'gestational_age_weeks',
            'bmi_pre_pregnancy', 'systolic_bp_mmhg', 'diastolic_bp_mmhg',
            'hemoglobin_gdl', 'fasting_glucose_mgdl', 'proteinuria',
            'hiv_status', 'anc_visits'
        ]
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Missing required clinical parameters: {missing}")
            
        # Parse inputs
        age = float(data['age_years'])
        grav = int(data['gravidity'])
        par = int(data['parity'])
        ga = float(data['gestational_age_weeks'])
        bmi = float(data['bmi_pre_pregnancy'])
        sbp = float(data['systolic_bp_mmhg'])
        dbp = float(data['diastolic_bp_mmhg'])
        hb = float(data['hemoglobin_gdl'])
        glu = float(data['fasting_glucose_mgdl'])
        prot = int(data['proteinuria'])
        hiv = int(data['hiv_status'])
        anc = int(data['anc_visits'])
        
        # Clinical plausibility checks
        if not (10 <= age <= 60):
            raise ValueError(f"Age {age} outside plausible obstetric range (10-60).")
        if not (40 <= sbp <= 260) or not (30 <= dbp <= 160):
            raise ValueError(f"Blood pressure {sbp}/{dbp} outside physiological range.")
        if sbp <= dbp:
            raise ValueError(f"Systolic BP ({sbp}) must be greater than diastolic BP ({dbp}).")
        if not (2.0 <= hb <= 20.0):
            raise ValueError(f"Hemoglobin {hb} g/dL outside plausible range (2.0-20.0).")
            
        # Derived features
        map_val = np.round((2 * dbp + sbp) / 3.0, 1)
        pulse_press = sbp - dbp
        is_primigravida = int(grav == 1)
        is_advanced_age = int(age >= 35)
        is_adolescent = int(age < 18)
        is_hypertensive = int(sbp >= 140 or dbp >= 90)
        is_severe_hypertension = int(sbp >= 160 or dbp >= 110)
        
        row = {
            'age_years': age,
            'gravidity': grav,
            'parity': par,
            'gestational_age_weeks': ga,
            'bmi_pre_pregnancy': bmi,
            'systolic_bp_mmhg': sbp,
            'diastolic_bp_mmhg': dbp,
            'hemoglobin_gdl': hb,
            'fasting_glucose_mgdl': glu,
            'proteinuria': prot,
            'hiv_status': hiv,
            'anc_visits': anc,
            'mean_arterial_pressure': map_val,
            'pulse_pressure': pulse_press,
            'is_primigravida': is_primigravida,
            'is_advanced_maternal_age': is_advanced_age,
            'is_adolescent': is_adolescent,
            'is_hypertensive': is_hypertensive,
            'is_severe_hypertension': is_severe_hypertension
        }
        return pd.DataFrame([row])[self.feature_cols]

    def flag_biomarkers(self, data: dict) -> list:
        """Identify abnormal clinical biomarkers according to WHO ANC guidelines."""
        flags = []
        sbp = float(data['systolic_bp_mmhg'])
        dbp = float(data['diastolic_bp_mmhg'])
        hb = float(data['hemoglobin_gdl'])
        glu = float(data['fasting_glucose_mgdl'])
        prot = int(data['proteinuria'])
        age = float(data['age_years'])
        bmi = float(data['bmi_pre_pregnancy'])
        hiv = int(data['hiv_status'])
        
        # Blood pressure
        if sbp >= 160 or dbp >= 110:
            flags.append({
                'biomarker': 'Blood Pressure',
                'severity': 'CRITICAL',
                'value': f"{sbp:.0f}/{dbp:.0f} mmHg",
                'guideline': 'Severe Hypertension (SBP >=160 or DBP >=110 mmHg). High risk for eclampsia/stroke.'
            })
        elif sbp >= 140 or dbp >= 90:
            flags.append({
                'biomarker': 'Blood Pressure',
                'severity': 'WARNING',
                'value': f"{sbp:.0f}/{dbp:.0f} mmHg",
                'guideline': 'Gestational Hypertension (SBP >=140 or DBP >=90 mmHg).'
            })

        # Proteinuria
        if prot >= 2:
            flags.append({
                'biomarker': 'Proteinuria',
                'severity': 'CRITICAL' if (sbp >= 140 or dbp >= 90) else 'WARNING',
                'value': f"{prot}+ on dipstick",
                'guideline': 'Significant proteinuria. Combined with elevated BP indicates preeclampsia.'
            })
        elif prot == 1:
            flags.append({
                'biomarker': 'Proteinuria',
                'severity': 'NOTE',
                'value': 'Trace / 1+',
                'guideline': 'Mild proteinuria detected; repeat test and monitor symptoms.'
            })

        # Hemoglobin
        if hb < 7.0:
            flags.append({
                'biomarker': 'Hemoglobin',
                'severity': 'CRITICAL',
                'value': f"{hb:.1f} g/dL",
                'guideline': 'Severe Anemia (Hb < 7.0 g/dL). Urgently evaluate for blood transfusion / IV iron.'
            })
        elif hb < 10.0:
            flags.append({
                'biomarker': 'Hemoglobin',
                'severity': 'WARNING',
                'value': f"{hb:.1f} g/dL",
                'guideline': 'Moderate Anemia (Hb 7.0 - 9.9 g/dL). Requires therapeutic oral iron and nutrition counseling.'
            })
        elif hb < 11.0:
            flags.append({
                'biomarker': 'Hemoglobin',
                'severity': 'NOTE',
                'value': f"{hb:.1f} g/dL",
                'guideline': 'Mild Anemia (Hb 10.0 - 10.9 g/dL). Ensure daily iron-folic acid supplementation.'
            })

        # Fasting Glucose
        if glu >= 92:
            flags.append({
                'biomarker': 'Fasting Blood Glucose',
                'severity': 'WARNING',
                'value': f"{glu:.0f} mg/dL",
                'guideline': 'Elevated fasting glucose (>= 92 mg/dL). Diagnostic for Gestational Diabetes Mellitus (WHO/IADPSG).'
            })

        # Demographics & Co-morbidities
        if age >= 35:
            flags.append({
                'biomarker': 'Maternal Age',
                'severity': 'NOTE',
                'value': f"{age:.0f} years",
                'guideline': 'Advanced maternal age (>= 35). Increased baseline risk of hypertension and chromosomal abnormalities.'
            })
        elif age < 18:
            flags.append({
                'biomarker': 'Maternal Age',
                'severity': 'NOTE',
                'value': f"{age:.0f} years",
                'guideline': 'Adolescent pregnancy (< 18). Elevated risk of cephalopelvic disproportion and preeclampsia.'
            })
            
        if bmi >= 35.0:
            flags.append({
                'biomarker': 'Pre-pregnancy BMI',
                'severity': 'NOTE',
                'value': f"{bmi:.1f} kg/m²",
                'guideline': 'Class II/III Obesity (BMI >= 35.0). Associated with macrosomia, GDM, and C-section risk.'
            })
            
        if hiv == 1:
            flags.append({
                'biomarker': 'HIV Status',
                'severity': 'WARNING',
                'value': 'Reactive (Positive)',
                'guideline': 'Requires Antiretroviral Therapy (ART) adherence and PMTCT protocol to prevent vertical transmission.'
            })

        return flags

    def determine_triage_action(self, risk_level: str, complication: str, flags: list) -> dict:
        """Determine triage urgency category and grounded clinical guidance."""
        critical_flags = [f for f in flags if f['severity'] == 'CRITICAL']
        warning_flags = [f for f in flags if f['severity'] == 'WARNING']
        
        if risk_level == 'high' or complication in ('eclampsia', 'severe_anemia', 'hemorrhage') or len(critical_flags) > 0:
            urgency = 'EMERGENCY'
            action = (
                "EMERGENCY: Immediate clinical assessment and referral to a Comprehensive Emergency "
                "Obstetric and Newborn Care (CEmONC) facility is required. "
                "Stabilize vital signs, secure IV access, administer magnesium sulfate if severe preeclampsia/eclampsia is suspected, "
                "and prepare for immediate emergency management."
            )
        elif risk_level == 'moderate' or complication in ('preeclampsia', 'gestational_diabetes') or len(warning_flags) > 0:
            urgency = 'PRIORITY'
            action = (
                "PRIORITY: Close medical follow-up required within 24-48 hours. "
                "Initiate confirmatory diagnostic testing (repeat BP monitoring, oral glucose tolerance test, complete blood count). "
                "Consult an obstetrician/certified healthcare provider and provide targeted clinical management."
            )
        else:
            urgency = 'ROUTINE'
            action = (
                "ROUTINE: Patient presentation is within standard low-risk antenatal parameters. "
                "Continue routine WHO Antenatal Care (ANC) schedule (minimum 8 contacts), maintain daily iron-folic acid supplementation, "
                "monitor fetal movement, and review maternal danger signs."
            )
            
        return {'urgency_level': urgency, 'clinical_action': action}

    def assess_patient(self, patient_data: dict) -> dict:
        """Full end-to-end clinical assessment combining ML prediction with WHO guideline triage."""
        X = self.validate_and_prepare_input(patient_data)
        
        # Risk prediction
        risk_pred_idx = self.risk_model.predict(X)[0]
        risk_probs = self.risk_model.predict_proba(X)[0]
        predicted_risk = self.risk_classes[risk_pred_idx]
        risk_prob_dict = {
            cls: float(np.round(prob, 4)) for cls, prob in zip(self.risk_classes, risk_probs)
        }
        
        # Complication prediction
        comp_pred_idx = self.comp_model.predict(X)[0]
        comp_probs = self.comp_model.predict_proba(X)[0]
        predicted_comp = self.comp_classes[comp_pred_idx]
        comp_prob_dict = {
            cls: float(np.round(prob, 4)) for cls, prob in zip(self.comp_classes, comp_probs)
        }
        
        # Biomarker flags & triage
        biomarker_flags = self.flag_biomarkers(patient_data)
        triage = self.determine_triage_action(predicted_risk, predicted_comp, biomarker_flags)
        
        return {
            'predicted_risk_level': predicted_risk,
            'risk_confidence': float(np.round(max(risk_probs), 4)),
            'risk_probabilities': risk_prob_dict,
            'predicted_primary_complication': predicted_comp,
            'complication_confidence': float(np.round(max(comp_probs), 4)),
            'complication_probabilities': comp_prob_dict,
            'biomarker_flags': biomarker_flags,
            'urgency_category': triage['urgency_level'],
            'recommended_clinical_action': triage['action'] if 'action' in triage else triage['clinical_action'],
            'disclaimer': (
                "DISCLAIMER: This assessment is an AI-assisted decision-support tool trained on synthetic ANC data "
                "informed by WHO guidelines. It does NOT replace professional medical diagnosis or clinical judgment."
            )
        }

