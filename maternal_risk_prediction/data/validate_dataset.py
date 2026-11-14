#!/usr/bin/env python3
"""
Validation & Diagnostic Visualization for Maternal Health Dataset.
Produces an 8-panel diagnostic figure (validation_report.png).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

SCENARIOS = ['low_burden', 'moderate_burden', 'high_burden']
COMP_ORDER = ['none', 'preeclampsia', 'eclampsia', 'gestational_diabetes',
              'hemorrhage', 'severe_anemia']
COLORS = {'none': '#2ecc71', 'preeclampsia': '#e74c3c', 'eclampsia': '#c0392b',
          'gestational_diabetes': '#f39c12', 'hemorrhage': '#9b59b6',
          'severe_anemia': '#3498db'}


def load_scenarios(data_dir='data'):
    dfs = {}
    for sc in SCENARIOS:
        path = os.path.join(data_dir, f'maternal_{sc}.csv')
        if os.path.exists(path):
            dfs[sc] = pd.read_csv(path)
    return dfs


def make_report(dfs, output='validation_report.png'):
    fig, axes = plt.subplots(4, 2, figsize=(16, 22))
    fig.suptitle('Maternal Health & Pregnancy Complications — Validation Report',
                 fontsize=16, fontweight='bold', y=0.98)

    df = dfs.get('moderate_burden', list(dfs.values())[0])

    # Panel 1: Complication distribution
    ax = axes[0, 0]
    counts = df['primary_complication'].value_counts()
    counts = counts.reindex([o for o in COMP_ORDER if o in counts.index])
    bars = ax.barh(range(len(counts)), counts.values,
                   color=[COLORS.get(o, '#95a5a6') for o in counts.index])
    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels([o.replace('_', ' ').title() for o in counts.index], fontsize=9)
    for i, v in enumerate(counts.values):
        ax.text(v + 30, i, f'{v/len(df)*100:.1f}%', va='center', fontsize=9)
    ax.set_xlabel('Count')
    ax.set_title('Primary Complication Distribution (Moderate)')
    ax.invert_yaxis()

    # Panel 2: Hemoglobin distribution
    ax = axes[0, 1]
    ax.hist(df['hemoglobin_gdl'], bins=50, color='#e74c3c', alpha=0.7, edgecolor='white')
    ax.axvline(11.0, color='orange', ls='--', lw=1.5, label='Anemia <11 g/dL')
    ax.axvline(7.0, color='darkred', ls='--', lw=1.5, label='Severe <7 g/dL')
    ax.set_xlabel('Hemoglobin (g/dL)')
    ax.set_ylabel('Count')
    ax.set_title(f'Hemoglobin (mean={df["hemoglobin_gdl"].mean():.1f}, '
                 f'anemia={(df["hemoglobin_gdl"]<11).mean()*100:.0f}%)')
    ax.legend(fontsize=8)

    # Panel 3: Blood pressure scatter
    ax = axes[1, 0]
    sample = df.sample(min(3000, len(df)), random_state=42)
    for c in COMP_ORDER:
        sub = sample[sample['primary_complication'] == c]
        if len(sub) > 0:
            ax.scatter(sub['systolic_bp_mmhg'], sub['diastolic_bp_mmhg'],
                      alpha=0.4, s=10, c=COLORS.get(c, '#95a5a6'),
                      label=c.replace('_', ' ').title())
    ax.axhline(90, color='red', ls=':', alpha=0.5)
    ax.axvline(140, color='red', ls=':', alpha=0.5)
    ax.set_xlabel('Systolic BP (mmHg)')
    ax.set_ylabel('Diastolic BP (mmHg)')
    ax.set_title('Blood Pressure by Complication')
    ax.legend(fontsize=6, markerscale=2)

    # Panel 4: BMI vs Blood glucose by complication
    ax = axes[1, 1]
    for c in ['none', 'gestational_diabetes', 'preeclampsia']:
        sub = sample[sample['primary_complication'] == c]
        if len(sub) > 0:
            ax.scatter(sub['bmi_pre_pregnancy'], sub['fasting_glucose_mgdl'],
                      alpha=0.4, s=10, c=COLORS.get(c, '#95a5a6'),
                      label=c.replace('_', ' ').title())
    ax.axhline(92, color='red', ls=':', alpha=0.5, label='GDM threshold')
    ax.set_xlabel('Pre-pregnancy BMI')
    ax.set_ylabel('Fasting Glucose (mg/dL)')
    ax.set_title('BMI vs Glucose')
    ax.legend(fontsize=7, markerscale=2)

    # Panel 5: Risk level distribution
    ax = axes[2, 0]
    risk_counts = df['risk_level'].value_counts().reindex(['low', 'moderate', 'high'])
    colors_risk = ['#2ecc71', '#f39c12', '#e74c3c']
    bars = ax.bar(range(3), risk_counts.values, color=colors_risk)
    ax.set_xticks(range(3))
    ax.set_xticklabels(['Low', 'Moderate', 'High'])
    for i, v in enumerate(risk_counts.values):
        ax.text(i, v + 50, f'{v/len(df)*100:.0f}%', ha='center', fontsize=10)
    ax.set_ylabel('Count')
    ax.set_title('Risk Level Distribution')

    # Panel 6: Cross-scenario complication rates
    ax = axes[2, 1]
    adverse = ['preeclampsia', 'eclampsia', 'gestational_diabetes',
               'hemorrhage', 'severe_anemia']
    x = np.arange(len(adverse))
    width = 0.25
    for i, sc in enumerate(SCENARIOS):
        if sc not in dfs:
            continue
        d = dfs[sc]
        rates = [(d['primary_complication'] == c).mean() * 100 for c in adverse]
        ax.bar(x + i * width, rates, width, label=sc.replace('_', ' ').title(),
               alpha=0.8)
    ax.set_xticks(x + width)
    ax.set_xticklabels([c.replace('_', '\n').title() for c in adverse], fontsize=7)
    ax.set_ylabel('Prevalence (%)')
    ax.set_title('Complication Rates Across Scenarios')
    ax.legend(fontsize=8)

    # Panel 7: Age distribution by complication
    ax = axes[3, 0]
    for c in ['none', 'preeclampsia', 'gestational_diabetes']:
        sub = df[df['primary_complication'] == c]['age_years']
        ax.hist(sub, bins=30, alpha=0.5, label=c.replace('_', ' ').title(),
                color=COLORS.get(c, '#95a5a6'), edgecolor='white')
    ax.set_xlabel('Age (years)')
    ax.set_ylabel('Count')
    ax.set_title('Age Distribution by Complication')
    ax.legend(fontsize=8)

    # Panel 8: Correlation heatmap
    ax = axes[3, 1]
    num_cols = ['age_years', 'bmi_pre_pregnancy', 'systolic_bp_mmhg',
                'diastolic_bp_mmhg', 'hemoglobin_gdl', 'fasting_glucose_mgdl',
                'gravidity', 'parity']
    corr = df[num_cols].corr()
    short = [c.replace('_', '\n') for c in num_cols]
    im = ax.imshow(corr.values, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    ax.set_xticks(range(len(short)))
    ax.set_xticklabels(short, fontsize=6, rotation=45, ha='right')
    ax.set_yticks(range(len(short)))
    ax.set_yticklabels(short, fontsize=6)
    for i in range(len(num_cols)):
        for j in range(len(num_cols)):
            ax.text(j, i, f'{corr.values[i, j]:.2f}', ha='center', va='center',
                    fontsize=5, color='white' if abs(corr.values[i, j]) > 0.5 else 'black')
    ax.set_title('Correlation Matrix')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f'Saved validation report to {output}')
    plt.close()


if __name__ == '__main__':
    dfs = load_scenarios()
    if not dfs:
        print('No data files found in data/')
    else:
        make_report(dfs)
        for sc, df in dfs.items():
            print(f'\n=== {sc} (n={len(df)}) ===')
            print(f'  Anemia rate: {(df["hemoglobin_gdl"] < 11).mean()*100:.1f}%')
            print(f'  Hypertension: {((df["systolic_bp_mmhg"]>=140)|(df["diastolic_bp_mmhg"]>=90)).mean()*100:.1f}%')
            print(f'  HIV+: {df["hiv_status"].mean()*100:.1f}%')
            print(f'  Stillbirth: {(df["pregnancy_outcome"]=="stillbirth").mean()*100:.1f}%')
