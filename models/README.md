# Trained Machine Learning Models Directory

This directory stores the trained machine learning model artifacts for the MotherlyPulse project.

## Models Included

1. **`risk_level_model.joblib`**
   - **Task:** Multi-class maternal risk level prediction (`low`, `moderate`, `high`).
   - **Architecture:** Balanced Random Forest Classifier (150 estimators, max depth 12).
   - **Accuracy:** `94.0%` (Balanced Accuracy: `92.7%`).
   - **Trained on:** 30,000 WHO literature-grounded synthetic ANC patient records.

2. **`complication_model.joblib`**
   - **Task:** Primary pregnancy complication prediction (`none`, `preeclampsia`, `gestational_diabetes`, `severe_anemia`, `hemorrhage`, `eclampsia`).
   - **Architecture:** Balanced Random Forest Classifier (150 estimators, max depth 14).
   - **Key Metrics:** Preeclampsia F1 `0.95`, Severe Anemia F1 `0.89`, Gestational Diabetes F1 `0.76`.

3. **`model_metadata.json`**
   - Full evaluation metrics, feature names, class distributions, and training parameters.

## Usage in Python

```python
import joblib
import os

# Load Risk Level Model Bundle
risk_bundle = joblib.load(os.path.join("models", "risk_level_model.joblib"))
risk_model = risk_bundle['model']
classes = risk_bundle['classes']

# Predict
# risk_probs = risk_model.predict_proba(patient_feature_dataframe)
```

