"""
Maternal Risk Assessment API Stub
=================================
Provides a clean, standalone interface function for integrating maternal risk prediction
into higher-level services or assistant modules without tight coupling.
"""

from typing import Dict, Any
from maternal_risk_prediction.src.predictor import MaternalRiskPredictor

_predictor_instance = None

def get_predictor() -> MaternalRiskPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = MaternalRiskPredictor()
    return _predictor_instance

def assess_maternal_risk(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main evaluation entry point.
    
    Accepts patient parameters dictionary:
      - age_years (float/int)
      - gravidity (int)
      - parity (int)
      - gestational_age_weeks (float)
      - bmi_pre_pregnancy (float)
      - systolic_bp_mmhg (float/int)
      - diastolic_bp_mmhg (float/int)
      - hemoglobin_gdl (float)
      - fasting_glucose_mgdl (float/int)
      - proteinuria (int: 0=none, 1=trace, 2=1+, 3=2+, 4=3+)
      - hiv_status (int: 0=negative, 1=positive)
      - anc_visits (int)

    Returns dictionary containing predicted_risk_level, predicted_primary_complication,
    probabilities, biomarker flags, urgency category (EMERGENCY, PRIORITY, ROUTINE),
    and evidence-based clinical recommendations.
    """
    predictor = get_predictor()
    return predictor.assess_patient(patient_dict)

