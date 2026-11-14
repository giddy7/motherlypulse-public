"""
Maternal Risk & Pregnancy Complication Training Pipeline
=========================================================
Trains machine learning classifiers on the 30,000 maternal health records
from the literature-informed Antenatal Care (ANC) dataset (low, moderate, high burden settings).

Target Models:
1. Risk Level Classifier: Predicts risk_level ('low', 'moderate', 'high')
2. Complication Classifier: Predicts primary_complication
   ('none', 'preeclampsia', 'gestational_diabetes', 'severe_anemia', 'hemorrhage', 'eclampsia')
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, balanced_accuracy_score, confusion_matrix
import joblib

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def load_combined_dataset():
    files = {
        'low_burden': os.path.join(DATA_DIR, 'maternal_low_burden.csv'),
        'moderate_burden': os.path.join(DATA_DIR, 'maternal_moderate_burden.csv'),
        'high_burden': os.path.join(DATA_DIR, 'maternal_high_burden.csv'),
    }
    dfs = []
    for scenario, filepath in files.items():
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['scenario'] = scenario
            dfs.append(df)
            print(f"Loaded {scenario}: {len(df):,} records")
        else:
            raise FileNotFoundError(f"Missing expected data file: {filepath}")
    combined = pd.concat(dfs, ignore_index=True)
    print(f"Total combined dataset: {len(combined):,} records\n")
    return combined

def engineer_features(df):
    """Derive standard obstetric and clinical features from presentation measurements."""
    X = pd.DataFrame()
    X['age_years'] = df['age_years']
    X['gravidity'] = df['gravidity']
    X['parity'] = df['parity']
    X['gestational_age_weeks'] = df['gestational_age_weeks']
    X['bmi_pre_pregnancy'] = df['bmi_pre_pregnancy']
    X['systolic_bp_mmhg'] = df['systolic_bp_mmhg']
    X['diastolic_bp_mmhg'] = df['diastolic_bp_mmhg']
    X['hemoglobin_gdl'] = df['hemoglobin_gdl']
    X['fasting_glucose_mgdl'] = df['fasting_glucose_mgdl']
    X['proteinuria'] = df['proteinuria']
    X['hiv_status'] = df['hiv_status']
    X['anc_visits'] = df['anc_visits']
    
    # Clinically established derived parameters
    # Mean Arterial Pressure (MAP) = (2 * DBP + SBP) / 3
    X['mean_arterial_pressure'] = np.round((2 * df['diastolic_bp_mmhg'] + df['systolic_bp_mmhg']) / 3.0, 1)
    # Pulse pressure = SBP - DBP
    X['pulse_pressure'] = df['systolic_bp_mmhg'] - df['diastolic_bp_mmhg']
    # Primigravida flag (1st pregnancy has elevated preeclampsia risk)
    X['is_primigravida'] = (df['gravidity'] == 1).astype(int)
    # Advanced maternal age flag (>=35 years)
    X['is_advanced_maternal_age'] = (df['age_years'] >= 35).astype(int)
    # Adolescent pregnancy flag (<18 years)
    X['is_adolescent'] = (df['age_years'] < 18).astype(int)
    # Hypertension stage flags
    X['is_hypertensive'] = ((df['systolic_bp_mmhg'] >= 140) | (df['diastolic_bp_mmhg'] >= 90)).astype(int)
    X['is_severe_hypertension'] = ((df['systolic_bp_mmhg'] >= 160) | (df['diastolic_bp_mmhg'] >= 110)).astype(int)
    
    return X

def train_and_evaluate():
    df = load_combined_dataset()
    X = engineer_features(df)
    feature_cols = list(X.columns)
    
    # -------------------------------------------------------------
    # 1. Train Risk Level Classifier
    # -------------------------------------------------------------
    print("=" * 60)
    print("1. TRAINING RISK LEVEL CLASSIFIER ('low', 'moderate', 'high')")
    print("=" * 60)
    y_risk = df['risk_level']
    risk_encoder = LabelEncoder()
    y_risk_enc = risk_encoder.fit_transform(y_risk)
    
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X, y_risk_enc, test_size=0.20, random_state=42, stratify=y_risk_enc
    )
    
    risk_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    risk_model.fit(X_train_r, y_train_r)
    
    y_pred_r = risk_model.predict(X_test_r)
    risk_acc = balanced_accuracy_score(y_test_r, y_pred_r)
    print(f"Balanced Accuracy: {risk_acc:.4f}")
    report_r = classification_report(
        y_test_r, y_pred_r, target_names=risk_encoder.classes_, output_dict=True
    )
    print(classification_report(y_test_r, y_pred_r, target_names=risk_encoder.classes_))
    
    # -------------------------------------------------------------
    # 2. Train Primary Complication Classifier
    # -------------------------------------------------------------
    print("=" * 60)
    print("2. TRAINING PRIMARY COMPLICATION CLASSIFIER")
    print("=" * 60)
    y_comp = df['primary_complication']
    comp_encoder = LabelEncoder()
    y_comp_enc = comp_encoder.fit_transform(y_comp)
    
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X, y_comp_enc, test_size=0.20, random_state=42, stratify=y_comp_enc
    )
    
    comp_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=14,
        min_samples_split=4,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    comp_model.fit(X_train_c, y_train_c)
    
    y_pred_c = comp_model.predict(X_test_c)
    comp_acc = balanced_accuracy_score(y_test_c, y_pred_c)
    print(f"Balanced Accuracy: {comp_acc:.4f}")
    report_c = classification_report(
        y_test_c, y_pred_c, target_names=comp_encoder.classes_, output_dict=True
    )
    print(classification_report(y_test_c, y_pred_c, target_names=comp_encoder.classes_))
    
    # -------------------------------------------------------------
    # 3. Feature Importance Analysis
    # -------------------------------------------------------------
    print("=" * 60)
    print("FEATURE IMPORTANCE (Risk Level Model):")
    print("=" * 60)
    importances = risk_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    for idx in sorted_idx:
        print(f"  {feature_cols[idx]:<25}: {importances[idx]:.4f}")
        
    # -------------------------------------------------------------
    # 4. Save Artifacts
    # -------------------------------------------------------------
    print("\nSaving trained models and preprocessor bundle...")
    risk_bundle = {
        'model': risk_model,
        'label_encoder': risk_encoder,
        'feature_cols': feature_cols,
        'classes': list(risk_encoder.classes_),
        'balanced_accuracy': float(risk_acc)
    }
    joblib.dump(risk_bundle, os.path.join(MODEL_DIR, "risk_level_model.joblib"))
    
    comp_bundle = {
        'model': comp_model,
        'label_encoder': comp_encoder,
        'feature_cols': feature_cols,
        'classes': list(comp_encoder.classes_),
        'balanced_accuracy': float(comp_acc)
    }
    joblib.dump(comp_bundle, os.path.join(MODEL_DIR, "complication_model.joblib"))
    
    metadata = {
        'total_training_records': len(df),
        'features': feature_cols,
        'risk_level': {
            'classes': list(risk_encoder.classes_),
            'balanced_accuracy': float(risk_acc),
            'metrics': report_r
        },
        'primary_complication': {
            'classes': list(comp_encoder.classes_),
            'balanced_accuracy': float(comp_acc),
            'metrics': report_c
        }
    }
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"SUCCESS: Models and metadata successfully saved in {MODEL_DIR}")

if __name__ == "__main__":
    train_and_evaluate()

