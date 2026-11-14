#!/usr/bin/env python3
"""
Literature-Informed Synthetic Maternal Health & Pregnancy Complications Dataset
===============================================================================

Generates realistic synthetic datasets of pregnant women attending antenatal
care (ANC) in LMIC settings, with demographics, clinical measurements, risk
factors, and pregnancy complications/outcomes.

Target population: Pregnant women presenting for ANC or delivery in LMIC
facility settings, aged 15-49.

DAG (Sampling Order):
  1. age (root)
  2. parity, gravidity (conditional on age)
  3. bmi_pre_pregnancy (root, age-adjusted)
  4. hiv_status (scenario-dependent)
  5. gestational_age_at_visit (root)
  6. hemoglobin (conditional on scenario, GA)
  7. blood_pressure (conditional on age, BMI, complication)
  8. blood_glucose (conditional on BMI, age, complication)
  9. proteinuria (conditional on BP, complication)
  10. complication (from prevalence, conditional on risk factors)
  11. risk_level (derived)

References:
-----------
[1] WHO (2016). WHO Recommendations on Antenatal Care for a Positive
    Pregnancy Experience. Geneva.
[2] Say L, et al. (2014). Global causes of maternal death: a WHO systematic
    analysis. Lancet Global Health, 2(6):e323-333.
[3] Abalos E, et al. (2013). Global and regional estimates of preeclampsia
    and eclampsia. Hypertension in Pregnancy, 32(sup1):36.
[4] IDF (2021). IDF Diabetes Atlas, 10th edition. International Diabetes
    Federation.
[5] Stevens GA, et al. (2013). Global, regional, and national trends in
    haemoglobin concentration and prevalence of anaemia. Lancet Global
    Health, 1(1):e16-25.
[6] UNAIDS (2023). Global HIV & AIDS statistics fact sheet.
[7] WHO (2023). Trends in maternal mortality 2000-2020. Geneva.
[8] DHS Program. Demographic and Health Surveys, multiple countries.
[9] Vogel JP, et al. (2014). Use of the Robson classification to assess
    caesarean section trends. Lancet Global Health, 2(5):e260-270.
[10] Souza JP, et al. (2013). Moving beyond essential interventions for
     reduction of maternal mortality. Lancet, 381(9879):1747-1755.
"""

import numpy as np
import pandas as pd
from scipy.stats import truncnorm
import argparse
import os

# ============================================================
# SECTION 1: Literature-Informed Parameters
# ============================================================

SCENARIOS = {
    'low_burden': {
        'description': 'Urban LMIC with functional ANC (e.g., urban Ghana, Kenya)',
        'preeclampsia_rate': 0.035,    # Abalos 2013: 2-5% globally
        'eclampsia_rate': 0.003,       # Abalos 2013: 0.1-0.5% in good care
        'gdm_rate': 0.04,             # IDF 2021: 3-5% in LMIC
        'hemorrhage_rate': 0.025,      # Say 2014: 2-3% in facility
        'severe_anemia_rate': 0.03,    # Stevens 2013: 2-5% with ANC
        'moderate_anemia_rate': 0.18,  # Stevens 2013: 15-25%
        'hiv_prevalence': 0.04,        # UNAIDS 2023: varies widely
        'cs_rate': 0.18,
        'maternal_age_mean': 27, 'maternal_age_sd': 5.5,
    },
    'moderate_burden': {
        'description': 'Average LMIC district (e.g., rural Uganda, Bangladesh)',
        'preeclampsia_rate': 0.06,     # Abalos 2013: 4-8% in LMIC
        'eclampsia_rate': 0.008,       # Abalos 2013: 0.5-1% in LMIC
        'gdm_rate': 0.06,             # IDF 2021: 5-8% in South Asia
        'hemorrhage_rate': 0.04,       # Say 2014: 3-5%
        'severe_anemia_rate': 0.06,    # Stevens 2013: 5-8%
        'moderate_anemia_rate': 0.28,  # Stevens 2013: 25-35%
        'hiv_prevalence': 0.08,        # UNAIDS: moderate prevalence setting
        'cs_rate': 0.10,
        'maternal_age_mean': 26, 'maternal_age_sd': 6.0,
    },
    'high_burden': {
        'description': 'Under-resourced / high-HIV setting (e.g., rural DRC, Malawi)',
        'preeclampsia_rate': 0.09,     # Abalos 2013: up to 10% in SSA
        'eclampsia_rate': 0.015,       # Higher where ANC access poor
        'gdm_rate': 0.08,             # IDF 2021: rising in SSA
        'hemorrhage_rate': 0.06,       # Say 2014: 5-8% low-resource
        'severe_anemia_rate': 0.10,    # Stevens 2013: 8-15%
        'moderate_anemia_rate': 0.35,  # Stevens 2013: 30-45%
        'hiv_prevalence': 0.18,        # UNAIDS: high prevalence SSA
        'cs_rate': 0.05,
        'maternal_age_mean': 25, 'maternal_age_sd': 6.5,
    },
}

# --- BMI Parameters (pre-pregnancy) ---
# Source: DHS anthropometry data, LMIC women of reproductive age
BMI_PARAMS = {'mean': 23.5, 'sd': 4.5, 'min': 14.0, 'max': 48.0}

# --- Hemoglobin (g/dL) ---
# Source: Stevens et al. (2013), WHO anemia thresholds in pregnancy
# Normal ≥11.0, Mild 10.0-10.9, Moderate 7.0-9.9, Severe <7.0
HB_NORMAL = {'mean': 11.8, 'sd': 1.0}
HB_MILD_ANEMIA = {'mean': 10.4, 'sd': 0.3}
HB_MODERATE_ANEMIA = {'mean': 8.5, 'sd': 0.8}
HB_SEVERE_ANEMIA = {'mean': 5.8, 'sd': 0.8}

# --- Blood Pressure (mmHg) ---
# Source: WHO ANC guidelines (2016)
# Normal: SBP <120, DBP <80
# Elevated: SBP 120-139, DBP 80-89
# Hypertension: SBP ≥140 or DBP ≥90
# Severe: SBP ≥160 or DBP ≥110
BP_NORMAL = {'sbp_mean': 112, 'sbp_sd': 10, 'dbp_mean': 70, 'dbp_sd': 7}
BP_PREECLAMPSIA = {'sbp_mean': 152, 'sbp_sd': 12, 'dbp_mean': 98, 'dbp_sd': 8}
BP_ECLAMPSIA = {'sbp_mean': 170, 'sbp_sd': 15, 'dbp_mean': 108, 'dbp_sd': 10}

# --- Blood Glucose (mg/dL) --- fasting
# Source: WHO/IADPSG criteria for GDM
# Normal fasting: 70-95 mg/dL
# GDM: fasting ≥92 mg/dL (IADPSG) or ≥95 mg/dL (WHO)
GLUCOSE_NORMAL = {'mean': 82, 'sd': 8}
GLUCOSE_GDM = {'mean': 108, 'sd': 15}


# ============================================================
# SECTION 2: Utility Functions
# ============================================================

def trunc_normal(mean, sd, lo, hi, size, rng):
    a, b = (lo - mean) / sd, (hi - mean) / sd
    return truncnorm.rvs(a, b, loc=mean, scale=sd, size=size,
                         random_state=rng.integers(0, 2**31))


# ============================================================
# SECTION 3: Main Generator
# ============================================================

def generate_maternal_dataset(n=10000, seed=42, scenario='moderate_burden'):
    rng = np.random.default_rng(seed)
    sc = SCENARIOS[scenario]

    # ── Step 1: Age (root) ──
    age = trunc_normal(sc['maternal_age_mean'], sc['maternal_age_sd'],
                       15, 49, n, rng).astype(int)

    # ── Step 2: Gravidity & Parity ──
    gravidity_lambda = np.clip((age - 16) * 0.30, 0.1, 10)
    gravidity = rng.poisson(gravidity_lambda)
    gravidity = np.clip(gravidity, 1, 16)  # current pregnancy counts
    parity = np.clip(gravidity - 1 - rng.binomial(1, 0.15, n), 0, 15)  # ~15% loss rate

    # ── Step 3: Pre-pregnancy BMI ──
    bmi = trunc_normal(BMI_PARAMS['mean'], BMI_PARAMS['sd'],
                       BMI_PARAMS['min'], BMI_PARAMS['max'], n, rng)
    bmi = np.round(bmi, 1)

    # ── Step 4: HIV status ──
    hiv_status = rng.random(n) < sc['hiv_prevalence']

    # ── Step 5: Gestational age at visit (weeks) ──
    ga_at_visit = trunc_normal(28, 8, 6, 42, n, rng)
    ga_at_visit = np.round(ga_at_visit, 1)

    # ── Step 6: Assign primary complication ──
    # Compute risk-adjusted probabilities
    complication = np.array(['none'] * n, dtype=object)
    
    # Risk factors for preeclampsia: age >35, BMI >30, primigravida
    pe_risk = np.ones(n)
    pe_risk[age > 35] *= 1.8        # Say 2014: OR ~1.5-2.0
    pe_risk[bmi > 30] *= 2.0        # WHO 2016: OR ~2-3
    pe_risk[gravidity == 1] *= 1.5   # Primigravida OR ~1.5
    pe_base = sc['preeclampsia_rate']

    # Risk factors for GDM: age >30, BMI >25
    gdm_risk = np.ones(n)
    gdm_risk[age > 30] *= 1.5       # IDF: OR ~1.5
    gdm_risk[bmi > 25] *= 2.5       # IDF: OR ~2-3
    gdm_base = sc['gdm_rate']

    # Assign complications (mutually exclusive primary)
    for i in range(n):
        probs = {
            'preeclampsia': pe_base * pe_risk[i],
            'eclampsia': sc['eclampsia_rate'] * pe_risk[i],
            'gestational_diabetes': gdm_base * gdm_risk[i],
            'hemorrhage': sc['hemorrhage_rate'],
            'severe_anemia': sc['severe_anemia_rate'],
        }
        # Normalize so total complication probability is reasonable
        total_comp = sum(probs.values())
        p_none = max(1.0 - total_comp, 0.3)
        
        r = rng.random()
        cumulative = 0
        assigned = False
        for comp, p in probs.items():
            adj_p = p / (total_comp + p_none) * total_comp  # keep relative rates
            cumulative += p / (total_comp + p_none)
            if r < cumulative:
                complication[i] = comp
                assigned = True
                break
        if not assigned:
            complication[i] = 'none'

    # ── Step 7: Hemoglobin (conditional on complication, scenario) ──
    hemoglobin = np.zeros(n)
    for i in range(n):
        if complication[i] == 'severe_anemia':
            hemoglobin[i] = rng.normal(HB_SEVERE_ANEMIA['mean'], HB_SEVERE_ANEMIA['sd'])
        elif complication[i] == 'hemorrhage':
            # Post-hemorrhage Hb is lower
            hemoglobin[i] = rng.normal(HB_MODERATE_ANEMIA['mean'], HB_MODERATE_ANEMIA['sd'])
        else:
            # Background anemia prevalence
            r = rng.random()
            if r < sc['moderate_anemia_rate']:
                hemoglobin[i] = rng.normal(HB_MODERATE_ANEMIA['mean'],
                                            HB_MODERATE_ANEMIA['sd'])
            elif r < sc['moderate_anemia_rate'] + 0.15:
                hemoglobin[i] = rng.normal(HB_MILD_ANEMIA['mean'],
                                            HB_MILD_ANEMIA['sd'])
            else:
                hemoglobin[i] = rng.normal(HB_NORMAL['mean'], HB_NORMAL['sd'])
    hemoglobin = np.clip(np.round(hemoglobin, 1), 3.0, 17.0)

    # Anemia classification (WHO pregnancy thresholds)
    anemia_status = np.where(
        hemoglobin < 7.0, 'severe',
        np.where(hemoglobin < 10.0, 'moderate',
                 np.where(hemoglobin < 11.0, 'mild', 'none')))

    # ── Step 8: Blood pressure (conditional on complication) ──
    systolic_bp = np.zeros(n)
    diastolic_bp = np.zeros(n)
    for i in range(n):
        if complication[i] == 'eclampsia':
            systolic_bp[i] = rng.normal(BP_ECLAMPSIA['sbp_mean'], BP_ECLAMPSIA['sbp_sd'])
            diastolic_bp[i] = rng.normal(BP_ECLAMPSIA['dbp_mean'], BP_ECLAMPSIA['dbp_sd'])
        elif complication[i] == 'preeclampsia':
            systolic_bp[i] = rng.normal(BP_PREECLAMPSIA['sbp_mean'], BP_PREECLAMPSIA['sbp_sd'])
            diastolic_bp[i] = rng.normal(BP_PREECLAMPSIA['dbp_mean'], BP_PREECLAMPSIA['dbp_sd'])
        else:
            # Age/BMI adjustment
            age_adj = (age[i] - 25) * 0.3
            bmi_adj = (bmi[i] - 23) * 0.5
            systolic_bp[i] = rng.normal(BP_NORMAL['sbp_mean'] + age_adj + bmi_adj,
                                         BP_NORMAL['sbp_sd'])
            diastolic_bp[i] = rng.normal(BP_NORMAL['dbp_mean'] + age_adj * 0.5 + bmi_adj * 0.3,
                                          BP_NORMAL['dbp_sd'])
    systolic_bp = np.clip(np.round(systolic_bp).astype(int), 70, 220)
    diastolic_bp = np.clip(np.round(diastolic_bp).astype(int), 40, 140)
    # Ensure SBP > DBP
    diastolic_bp = np.minimum(diastolic_bp, systolic_bp - 15)

    # ── Step 9: Fasting blood glucose (conditional on GDM) ──
    fasting_glucose = np.zeros(n)
    for i in range(n):
        if complication[i] == 'gestational_diabetes':
            fasting_glucose[i] = rng.normal(GLUCOSE_GDM['mean'], GLUCOSE_GDM['sd'])
        else:
            bmi_adj = (bmi[i] - 23) * 0.4
            fasting_glucose[i] = rng.normal(GLUCOSE_NORMAL['mean'] + bmi_adj,
                                             GLUCOSE_NORMAL['sd'])
    fasting_glucose = np.clip(np.round(fasting_glucose).astype(int), 45, 250)

    # ── Step 10: Proteinuria (conditional on preeclampsia/eclampsia) ──
    # 0=none, 1=trace, 2= +1, 3= +2, 4= +3 or more
    proteinuria = np.zeros(n, dtype=int)
    for i in range(n):
        if complication[i] == 'eclampsia':
            proteinuria[i] = rng.choice([3, 4], p=[0.3, 0.7])
        elif complication[i] == 'preeclampsia':
            proteinuria[i] = rng.choice([2, 3, 4], p=[0.3, 0.4, 0.3])
        else:
            proteinuria[i] = rng.choice([0, 1], p=[0.85, 0.15])

    # ── Step 11: Number of ANC visits ──
    # WHO recommends ≥8; LMIC average 4-6
    anc_visits = np.clip(rng.poisson(
        np.where(ga_at_visit > 36, 6, np.where(ga_at_visit > 20, 4, 2)),
    ), 0, 15)

    # ── Step 12: Delivery mode ──
    delivery_mode = np.array(['vaginal'] * n, dtype=object)
    for i in range(n):
        p_cs = sc['cs_rate']
        if complication[i] in ('eclampsia', 'preeclampsia'):
            p_cs = min(p_cs * 3.0, 0.60)
        elif complication[i] == 'hemorrhage':
            p_cs = min(p_cs * 2.0, 0.40)
        elif age[i] > 35:
            p_cs = min(p_cs * 1.5, 0.40)
        if rng.random() < p_cs:
            delivery_mode[i] = 'caesarean'

    # ── Step 13: Pregnancy outcome ──
    pregnancy_outcome = np.array(['live_birth'] * n, dtype=object)
    for i in range(n):
        if complication[i] == 'eclampsia':
            r = rng.random()
            if r < 0.05:  # ~1-5% maternal mortality with eclampsia (Say 2014)
                pregnancy_outcome[i] = 'maternal_death'
            elif r < 0.20:
                pregnancy_outcome[i] = 'stillbirth'
        elif complication[i] == 'hemorrhage':
            r = rng.random()
            if r < 0.03:
                pregnancy_outcome[i] = 'maternal_death'
            elif r < 0.10:
                pregnancy_outcome[i] = 'stillbirth'
        elif complication[i] == 'severe_anemia':
            if rng.random() < 0.08:
                pregnancy_outcome[i] = 'stillbirth'

    # ── Step 14: Risk level (derived) ──
    risk_level = np.array(['low'] * n, dtype=object)
    for i in range(n):
        high_risk = (
            complication[i] in ('eclampsia', 'severe_anemia', 'hemorrhage') or
            age[i] > 40 or age[i] < 16 or
            systolic_bp[i] >= 160 or diastolic_bp[i] >= 110 or
            hemoglobin[i] < 7.0 or
            hiv_status[i]
        )
        moderate_risk = (
            complication[i] in ('preeclampsia', 'gestational_diabetes') or
            age[i] > 35 or
            bmi[i] > 35 or
            parity[i] > 5 or
            systolic_bp[i] >= 140 or diastolic_bp[i] >= 90 or
            hemoglobin[i] < 10.0
        )
        if high_risk:
            risk_level[i] = 'high'
        elif moderate_risk:
            risk_level[i] = 'moderate'

    # ── Assemble DataFrame ──
    df = pd.DataFrame({
        'id': np.arange(1, n + 1),
        'age_years': age,
        'gravidity': gravidity,
        'parity': parity,
        'gestational_age_weeks': ga_at_visit,
        'bmi_pre_pregnancy': bmi,
        'systolic_bp_mmhg': systolic_bp,
        'diastolic_bp_mmhg': diastolic_bp,
        'hemoglobin_gdl': hemoglobin,
        'anemia_status': anemia_status,
        'fasting_glucose_mgdl': fasting_glucose,
        'proteinuria': proteinuria,
        'hiv_status': hiv_status.astype(int),
        'anc_visits': anc_visits,
        'delivery_mode': delivery_mode,
        'primary_complication': complication,
        'pregnancy_outcome': pregnancy_outcome,
        'risk_level': risk_level,
    })

    # ── Print summary ──
    print(f"\n{'='*60}")
    print(f"Maternal Health — {scenario} (n={n}, seed={seed})")
    print(f"{'='*60}")
    print(f"\nComplication prevalence:")
    for c in ['none', 'preeclampsia', 'eclampsia', 'gestational_diabetes',
              'hemorrhage', 'severe_anemia']:
        obs = (complication == c).mean() * 100
        print(f"  {c:30s}: {obs:5.1f}%")
    print(f"\nAnemia (any, Hb<11): {(hemoglobin < 11).mean()*100:.1f}%")
    print(f"Severe anemia (Hb<7): {(hemoglobin < 7).mean()*100:.1f}%")
    print(f"Hypertension (SBP≥140|DBP≥90): "
          f"{((systolic_bp >= 140) | (diastolic_bp >= 90)).mean()*100:.1f}%")
    print(f"HIV+: {hiv_status.mean()*100:.1f}%")
    print(f"C-section: {(delivery_mode == 'caesarean').mean()*100:.1f}%")
    print(f"Stillbirth: {(pregnancy_outcome == 'stillbirth').mean()*100:.1f}%")
    print(f"Risk levels: low={( risk_level == 'low').mean()*100:.0f}%, "
          f"moderate={(risk_level == 'moderate').mean()*100:.0f}%, "
          f"high={(risk_level == 'high').mean()*100:.0f}%")

    return df


# ============================================================
# SECTION 4: CLI Entry Point
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate synthetic maternal health dataset')
    parser.add_argument('--scenario', type=str, default='moderate_burden',
                        choices=list(SCENARIOS.keys()))
    parser.add_argument('--n', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--all-scenarios', action='store_true')
    args = parser.parse_args()

    os.makedirs('data', exist_ok=True)

    if args.all_scenarios:
        for sc_name in SCENARIOS:
            df = generate_maternal_dataset(n=args.n, seed=args.seed, scenario=sc_name)
            out = os.path.join('data', f'maternal_{sc_name}.csv')
            df.to_csv(out, index=False)
            print(f"  → Saved to {out}\n")
    else:
        df = generate_maternal_dataset(n=args.n, seed=args.seed, scenario=args.scenario)
        out = args.output or os.path.join('data', f'maternal_{args.scenario}.csv')
        df.to_csv(out, index=False)
        print(f"  → Saved to {out}")
