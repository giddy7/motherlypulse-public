---
license: cc-by-4.0
task_categories:
  - tabular-classification
  - tabular-regression
language:
  - en
tags:
  - synthetic
  - healthcare
  - maternal-health
  - pregnancy
  - antenatal-care
  - preeclampsia
  - gestational-diabetes
  - anemia
  - who-guidelines
  - lmic
pretty_name: "Synthetic Maternal Health & Pregnancy Complications Dataset (ANC)"
size_categories:
  - 10K<n<100K
configs:
  - config_name: low_burden
    data_files: data/maternal_low_burden.csv
  - config_name: moderate_burden
    data_files: data/maternal_moderate_burden.csv
    default: true
  - config_name: high_burden
    data_files: data/maternal_high_burden.csv
---

# Synthetic Maternal Health & Pregnancy Complications Dataset

**The complete bundle** — including the full dataset (35,000 rows), trained xgboost model (AUC-ROC: 0.990), fully-executed notebook, and full Paper— is available on Gumroad:

👉 **[Get the full bundle on Gumroad for $30](https://kossisoro.gumroad.com/l/mphrsb)**

---
## Abstract

This dataset provides **30,000 synthetic records** (10,000 per scenario) of pregnant women attending antenatal care (ANC) in LMIC facility settings. Each record contains 16 clinically relevant variables including demographics (age, gravidity, parity), clinical measurements (blood pressure, hemoglobin, fasting glucose, BMI, proteinuria), risk factors (HIV status), and outcomes (primary complication, pregnancy outcome, risk level). All distributions are parameterized from WHO ANC guidelines, the Lancet Maternal Health series, UNAIDS, IDF Diabetes Atlas, and DHS surveys. Three burden scenarios (low, moderate, high) capture the spectrum from well-resourced urban facilities to under-resourced high-HIV settings.

## 1. Introduction

Maternal mortality remains unacceptably high in LMICs, with approximately 287,000 deaths annually (WHO 2023). Hypertensive disorders (preeclampsia/eclampsia), obstetric hemorrhage, and sepsis account for over 50% of maternal deaths (Say et al., 2014). Anemia affects 40-60% of pregnant women in Sub-Saharan Africa, and gestational diabetes prevalence is rising across LMICs.

Open-access clinical datasets of maternal health from LMIC contexts are scarce due to privacy regulations and fragmented health information systems. This synthetic dataset fills that gap for:

- Training ML models for pregnancy risk stratification
- Benchmarking complication prediction algorithms
- Prototyping ANC clinical decision support tools
- Educational use in global maternal health curricula

**This dataset is entirely synthetic. It must not be used for clinical decision-making.**

## 2. Methodology

### 2.1 Target Population

Pregnant women aged 15-49 presenting for ANC or delivery at LMIC health facilities.

### 2.2 Epidemiological Parameterization

| Parameter | Value | Source |
| --- | --- | --- |
| Preeclampsia prevalence | 2-10% by setting | Abalos et al., Hypertension in Pregnancy 2013 |
| Eclampsia incidence | 0.1-1.5% | Abalos et al., 2013 |
| GDM prevalence | 3-8% in LMIC | IDF Diabetes Atlas 2021 |
| Obstetric hemorrhage | 2-8% | Say et al., Lancet Global Health 2014 |
| Anemia in pregnancy (Hb<11) | 40-65% in SSA | Stevens et al., Lancet Global Health 2013 |
| Severe anemia (Hb<7) | 2-15% by setting | Stevens et al., 2013 |
| HIV prevalence (women) | 4-18% by setting | UNAIDS 2023 |
| C-section rate (LMIC) | 5-18% | DHS Program; Vogel et al., 2014 |

### 2.3 Scenario Design

| Scenario | Context | Preeclampsia | Eclampsia | GDM | Hemorrhage | Severe Anemia | HIV |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Low burden | Urban LMIC, functional ANC | 4.2% | 0.4% | 6.8% | 2.6% | 2.9% | 4.2% |
| Moderate burden | District hospital | 7.5% | 1.0% | 10.6% | 3.9% | 5.8% | 8.0% |
| High burden | Under-resourced / high-HIV | 11.6% | 2.1% | 13.5% | 6.0% | 9.9% | 18.1% |

### 2.4 Risk Factor Modelling

Complication probabilities are adjusted by individual risk factors:

- **Preeclampsia**: OR ~1.8 for age >35, OR ~2.0 for BMI >30, OR ~1.5 for primigravida (WHO 2016)
- **GDM**: OR ~1.5 for age >30, OR ~2.5 for BMI >25 (IDF 2021)
- **Blood pressure**: Conditional on complication, with age and BMI adjustments
- **Hemoglobin**: Background anemia prevalence plus complication-specific shifts

## 3. Dataset Description

### 3.1 Schema

| Column | Type | Units | Range | Description |
| --- | --- | --- | --- | --- |
| id | int | — | 1-10000 | Unique identifier |
| age_years | int | years | 15-49 | Maternal age |
| gravidity | int | — | 1-16 | Total pregnancies including current |
| parity | int | — | 0-15 | Previous deliveries |
| gestational_age_weeks | float | weeks | 6.0-42.0 | GA at clinical visit |
| bmi_pre_pregnancy | float | kg/m² | 14.0-48.0 | Pre-pregnancy BMI |
| systolic_bp_mmhg | int | mmHg | 70-220 | Systolic blood pressure |
| diastolic_bp_mmhg | int | mmHg | 40-140 | Diastolic blood pressure |
| hemoglobin_gdl | float | g/dL | 3.0-17.0 | Hemoglobin concentration |
| anemia_status | categorical | — | none/mild/moderate/severe | WHO pregnancy anemia classification |
| fasting_glucose_mgdl | int | mg/dL | 45-250 | Fasting blood glucose |
| proteinuria | ordinal | — | 0-4 | Urine protein (0=none, 4=≥+3) |
| hiv_status | binary | — | 0/1 | HIV serostatus |
| anc_visits | int | — | 0-15 | Number of ANC visits to date |
| delivery_mode | categorical | — | vaginal/caesarean | Mode of delivery |
| primary_complication | categorical | — | 6 classes | Primary pregnancy complication |
| pregnancy_outcome | categorical | — | live_birth/stillbirth/maternal_death | Pregnancy outcome |
| risk_level | categorical | — | low/moderate/high | Composite risk classification |

### 3.2 Classification Criteria

| Classification | Criteria | Source |
| --- | --- | --- |
| Anemia (mild) | Hb 10.0-10.9 g/dL | WHO 2011 |
| Anemia (moderate) | Hb 7.0-9.9 g/dL | WHO 2011 |
| Anemia (severe) | Hb < 7.0 g/dL | WHO 2011 |
| Hypertension | SBP ≥140 or DBP ≥90 mmHg | WHO ANC 2016 |
| Severe hypertension | SBP ≥160 or DBP ≥110 mmHg | WHO ANC 2016 |
| GDM (fasting) | Fasting glucose ≥92 mg/dL | IADPSG/WHO 2013 |

## 4. Validation

### 4.1 Cross-Scenario Monotonicity

All adverse outcomes increase monotonically from low → moderate → high burden: anemia (48% → 58% → 65%), hypertension (5% → 9% → 14%), HIV (4% → 8% → 18%), stillbirth (0.6% → 0.8% → 1.4%).

### 4.2 Diagnostic Plots

<p align="center">
  <img src="validation_report.png" alt="Validation Report" width="100%">
</p>

## 5. Usage

### 5.1 Loading with HuggingFace `datasets`

```python
from datasets import load_dataset

dataset = load_dataset("electricsheepafrica/synthetic-maternal-pregnancy-complications-WHO-ANC", "moderate_burden")
df = dataset["train"].to_pandas()
```

### 5.2 Loading directly from CSV

```python
import pandas as pd

df = pd.read_csv("data/maternal_moderate_burden.csv")
high_risk = df[df['risk_level'] == 'high']
print(f"High risk: {len(high_risk)/len(df)*100:.1f}%")
```

### 5.3 Regenerating

```bash
pip install numpy pandas scipy matplotlib
python generate_dataset.py --all-scenarios --n 10000 --seed 42
python validate_dataset.py
```

## 6. Limitations & Ethical Considerations

- **Synthetic data**: No real patients. Not for clinical use.
- **Simplified comorbidity**: Each woman has one primary complication; real pregnancies often involve multiple concurrent conditions.
- **No temporal modelling**: Single timepoint snapshot; does not capture ANC trajectory or disease progression.
- **HIV simplification**: HIV status modelled as binary; does not capture viral load, ART status, or CD4 count.
- **Geographic generalization**: Parameters drawn from pooled LMIC estimates; may not represent any single country precisely.

## 7. References

1. WHO (2016). WHO Recommendations on Antenatal Care for a Positive Pregnancy Experience. Geneva.
2. Say L, et al. (2014). Global causes of maternal death. *Lancet Global Health*, 2(6):e323-333.
3. Abalos E, et al. (2013). Global and regional estimates of preeclampsia and eclampsia. *Hypertension in Pregnancy*, 32(sup1):36.
4. IDF (2021). *IDF Diabetes Atlas*, 10th edition.
5. Stevens GA, et al. (2013). Global, regional, and national trends in haemoglobin concentration. *Lancet Global Health*, 1(1):e16-25.
6. UNAIDS (2023). Global HIV & AIDS statistics fact sheet.
7. WHO (2023). Trends in maternal mortality 2000-2020. Geneva.
8. DHS Program. Demographic and Health Surveys, multiple countries.
9. Vogel JP, et al. (2014). Use of the Robson classification. *Lancet Global Health*, 2(5):e260-270.
10. Souza JP, et al. (2013). Moving beyond essential interventions. *Lancet*, 381(9879):1747-1755.

## Citation

```bibtex
@dataset{esa_maternal_2025,
  title={Synthetic Maternal Health and Pregnancy Complications Dataset},
  author={Electric Sheep Africa},
  year={2025},
  publisher={Hugging Face},
  url={https://huggingface.co/datasets/electricsheepafrica/synthetic-maternal-pregnancy-complications-WHO-ANC}
}
```

## License

This dataset is released under the [Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/) license.
