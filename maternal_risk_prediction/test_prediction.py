"""
Unit & Integration Tests for Maternal Risk Prediction Module
=============================================================
Tests model inference, input validation, clinical biomarker flagging,
and API stub execution.
"""

import unittest
import sys
import os

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maternal_risk_prediction.src.predictor import MaternalRiskPredictor
from maternal_risk_prediction.src.api_stub import assess_maternal_risk

class TestMaternalRiskPredictor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = MaternalRiskPredictor()

    def test_model_loaded(self):
        self.assertIsNotNone(self.predictor.risk_model)
        self.assertIsNotNone(self.predictor.comp_model)
        self.assertEqual(len(self.predictor.risk_classes), 3)
        self.assertTrue('high' in self.predictor.risk_classes)
        self.assertTrue('preeclampsia' in self.predictor.comp_classes)

    def test_low_risk_case(self):
        patient = {
            "age_years": 25, "gravidity": 2, "parity": 1, "gestational_age_weeks": 20.0,
            "bmi_pre_pregnancy": 22.0, "systolic_bp_mmhg": 110, "diastolic_bp_mmhg": 70,
            "hemoglobin_gdl": 12.5, "fasting_glucose_mgdl": 80, "proteinuria": 0,
            "hiv_status": 0, "anc_visits": 3
        }
        res = self.predictor.assess_patient(patient)
        self.assertEqual(res['predicted_risk_level'], 'low')
        self.assertEqual(res['urgency_category'], 'ROUTINE')
        self.assertEqual(res['predicted_primary_complication'], 'none')
        self.assertEqual(len(res['biomarker_flags']), 0)

    def test_severe_hypertension_emergency(self):
        patient = {
            "age_years": 32, "gravidity": 1, "parity": 0, "gestational_age_weeks": 35.0,
            "bmi_pre_pregnancy": 28.0, "systolic_bp_mmhg": 170, "diastolic_bp_mmhg": 115,
            "hemoglobin_gdl": 11.0, "fasting_glucose_mgdl": 85, "proteinuria": 3,
            "hiv_status": 0, "anc_visits": 4
        }
        res = self.predictor.assess_patient(patient)
        self.assertEqual(res['urgency_category'], 'EMERGENCY')
        self.assertTrue(res['predicted_primary_complication'] in ['preeclampsia', 'eclampsia'])
        # Check critical flags
        severities = [f['severity'] for f in res['biomarker_flags']]
        self.assertIn('CRITICAL', severities)

    def test_severe_anemia_detection(self):
        patient = {
            "age_years": 24, "gravidity": 2, "parity": 1, "gestational_age_weeks": 28.0,
            "bmi_pre_pregnancy": 21.0, "systolic_bp_mmhg": 108, "diastolic_bp_mmhg": 68,
            "hemoglobin_gdl": 5.5, "fasting_glucose_mgdl": 80, "proteinuria": 0,
            "hiv_status": 0, "anc_visits": 2
        }
        res = self.predictor.assess_patient(patient)
        self.assertEqual(res['urgency_category'], 'EMERGENCY')
        self.assertEqual(res['predicted_primary_complication'], 'severe_anemia')
        self.assertIn(res['predicted_risk_level'], ['high', 'moderate'])

    def test_gestational_diabetes_detection(self):
        patient = {
            "age_years": 34, "gravidity": 3, "parity": 2, "gestational_age_weeks": 26.0,
            "bmi_pre_pregnancy": 32.0, "systolic_bp_mmhg": 122, "diastolic_bp_mmhg": 78,
            "hemoglobin_gdl": 11.8, "fasting_glucose_mgdl": 125, "proteinuria": 0,
            "hiv_status": 0, "anc_visits": 3
        }
        res = self.predictor.assess_patient(patient)
        self.assertEqual(res['predicted_primary_complication'], 'gestational_diabetes')
        self.assertEqual(res['urgency_category'], 'PRIORITY')

    def test_missing_field_raises(self):
        incomplete = {"age_years": 25, "systolic_bp_mmhg": 120}
        with self.assertRaises(ValueError):
            self.predictor.assess_patient(incomplete)

    def test_invalid_bp_raises(self):
        invalid_bp = {
            "age_years": 25, "gravidity": 1, "parity": 0, "gestational_age_weeks": 20.0,
            "bmi_pre_pregnancy": 22.0, "systolic_bp_mmhg": 80, "diastolic_bp_mmhg": 120, # SBP <= DBP
            "hemoglobin_gdl": 12.0, "fasting_glucose_mgdl": 80, "proteinuria": 0,
            "hiv_status": 0, "anc_visits": 3
        }
        with self.assertRaises(ValueError):
            self.predictor.assess_patient(invalid_bp)

    def test_api_stub(self):
        patient = {
            "age_years": 28, "gravidity": 2, "parity": 1, "gestational_age_weeks": 22.0,
            "bmi_pre_pregnancy": 23.0, "systolic_bp_mmhg": 115, "diastolic_bp_mmhg": 75,
            "hemoglobin_gdl": 11.5, "fasting_glucose_mgdl": 85, "proteinuria": 0,
            "hiv_status": 0, "anc_visits": 3
        }
        res = assess_maternal_risk(patient)
        self.assertIn('predicted_risk_level', res)
        self.assertIn('urgency_category', res)
        self.assertIn('disclaimer', res)

if __name__ == "__main__":
    unittest.main()

