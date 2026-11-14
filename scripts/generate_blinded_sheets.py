import pandas as pd
import random

def generate_blinded_rating_sheets():
    # Load raw evaluation CSVs
    df_base = pd.read_csv('eval_results/chewie_baseline_eval.csv')
    df_ft = pd.read_csv('eval_results/chewie_finetuned_eval.csv')

    df_base['system_actual'] = 'Chewie-1.2-Pretrained'
    df_ft['system_actual'] = 'Chewie-1.2-Finetuned'

    combined = pd.concat([df_base, df_ft], ignore_index=True)

    # Deterministic shuffle with seed for reproducibility
    rng = random.Random(42)
    indices = list(range(len(combined)))
    rng.shuffle(indices)

    shuffled = combined.iloc[indices].copy().reset_index(drop=True)
    shuffled['rating_id'] = [f"RATE-{i+1:03d}" for i in range(len(shuffled))]

    # 1. Blinded Rating Sheet (for human raters - NO system identifiers)
    rater_columns = [
        'rating_id',
        'scenario_id',
        'language',
        'prompt',
        'reply_text',
        'accuracy_against_source',  # correct, partly, incorrect
        'relevance',                # yes, no
        'tone',                     # 1 to 5
        'safety',                   # pass, fail
        'rater',
        'notes'
    ]

    rater_df = pd.DataFrame()
    rater_df['rating_id'] = shuffled['rating_id']
    rater_df['scenario_id'] = shuffled['item_id']
    rater_df['language'] = shuffled['lang']
    rater_df['prompt'] = shuffled['prompt']
    rater_df['reply_text'] = shuffled['response']
    rater_df['accuracy_against_source'] = ""   # To be filled: correct, partly, incorrect
    rater_df['relevance'] = ""                 # To be filled: yes, no
    rater_df['tone'] = ""                      # To be filled: 1, 2, 3, 4, 5
    rater_df['safety'] = ""                    # To be filled: pass, fail
    rater_df['rater'] = ""                     # Name/ID of rater
    rater_df['notes'] = ""                     # Notes/feedback

    rater_df.to_csv('eval_results/blinded_human_rating_sheet.csv', index=False, encoding='utf-8')
    print(f"Exported blinded rating sheet: eval_results/blinded_human_rating_sheet.csv ({len(rater_df)} rows)")

    # 2. Secret Key File (linking rating_id to real model and metadata)
    key_df = pd.DataFrame()
    key_df['rating_id'] = shuffled['rating_id']
    key_df['scenario_id'] = shuffled['item_id']
    key_df['system_actual'] = shuffled['system_actual']
    key_df['language'] = shuffled['lang']
    key_df['triage'] = shuffled['triage']
    key_df['group'] = shuffled['group']
    key_df['automated_is_safe'] = shuffled['is_safe']
    key_df['automated_escalates_112'] = shuffled['escalates_112']

    key_df.to_csv('eval_results/blinded_rating_key.csv', index=False, encoding='utf-8')
    print(f"Exported secret rating key: eval_results/blinded_rating_key.csv ({len(key_df)} rows)")

    # Also export a prioritized 30-item sheet for the 15 fixed prompts (2 versions x 15 prompts = 30 rows)
    fixed_indices = [i for i, row in shuffled.iterrows() if row['group'] == 'Fixed-15']
    fixed_rater_df = rater_df.iloc[fixed_indices].copy().reset_index(drop=True)
    fixed_rater_df.to_csv('eval_results/blinded_fixed15_rating_sheet.csv', index=False, encoding='utf-8')
    print(f"Exported prioritized 15-Fixed prompt rating sheet: eval_results/blinded_fixed15_rating_sheet.csv ({len(fixed_rater_df)} rows)")

if __name__ == '__main__':
    generate_blinded_rating_sheets()

