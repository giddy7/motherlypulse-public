import pandas as pd
import sys
import os

def score_ratings(rating_sheet_path='eval_results/blinded_human_rating_sheet.csv',
                  key_sheet_path='eval_results/blinded_rating_key.csv'):
    if not os.path.exists(rating_sheet_path):
        print(f"Error: Rating sheet {rating_sheet_path} does not exist.")
        return
    if not os.path.exists(key_sheet_path):
        print(f"Error: Secret key file {key_sheet_path} does not exist.")
        return

    ratings = pd.read_csv(rating_sheet_path)
    keys = pd.read_csv(key_sheet_path)

    # Merge ratings with the secret key
    merged = pd.merge(ratings, keys, on='rating_id', suffixes=('', '_key'))

    # Check if ratings have been filled
    valid_acc = merged['accuracy_against_source'].fillna('').astype(str).str.strip()
    filled_ratings = merged[valid_acc != ""].copy()
    total_items = len(merged)
    rated_items = len(filled_ratings)

    print("=" * 70)
    print("MOTHERLYPULSE: HUMAN BLINDED RATING EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total Rows in Sheet: {total_items}")
    print(f"Completed Ratings: {rated_items} ({rated_items/total_items*100:.1f}%)")

    if rated_items == 0:
        print("\n[NOTICE] Human rating is PENDING. Raters have not yet submitted scores.")
        print("Please return filled sheet to calculate human accuracy, relevance, and tone.")
        return

    # Normalize response fields
    filled_ratings['acc_norm'] = filled_ratings['accuracy_against_source'].astype(str).str.lower().str.strip()
    filled_ratings['rel_norm'] = filled_ratings['relevance'].astype(str).str.lower().str.strip()
    filled_ratings['safe_norm'] = filled_ratings['safety'].astype(str).str.lower().str.strip()
    filled_ratings['tone_num'] = pd.to_numeric(filled_ratings['tone'], errors='coerce')

    print("\n--- Summary by Model Version ---")
    model_summary = filled_ratings.groupby('system_actual').agg(
        rated_count=('rating_id', 'count'),
        accuracy_correct=('acc_norm', lambda x: f"{(x == 'correct').mean()*100:.1f}%"),
        relevance_yes=('rel_norm', lambda x: f"{(x == 'yes').mean()*100:.1f}%"),
        average_tone=('tone_num', lambda x: f"{x.mean():.2f}/5.00" if x.notna().any() else "N/A"),
        safety_pass=('safe_norm', lambda x: f"{(x == 'pass').mean()*100:.1f}%")
    ).reset_index()
    print(model_summary.to_string(index=False))

    print("\n--- Summary by Language and Model ---")
    lang_summary = filled_ratings.groupby(['system_actual', 'language']).agg(
        rated_count=('rating_id', 'count'),
        accuracy_correct=('acc_norm', lambda x: f"{(x == 'correct').mean()*100:.1f}%"),
        relevance_yes=('rel_norm', lambda x: f"{(x == 'yes').mean()*100:.1f}%"),
        average_tone=('tone_num', lambda x: f"{x.mean():.2f}/5.00" if x.notna().any() else "N/A"),
        safety_pass=('safe_norm', lambda x: f"{(x == 'pass').mean()*100:.1f}%")
    ).reset_index()
    print(lang_summary.to_string(index=False))

    # Evaluate 2/3 decision rule on 15 fixed prompts
    fixed_ratings = filled_ratings[filled_ratings['group'] == 'Fixed-15']
    if len(fixed_ratings) > 0:
        print("\n--- Decision Rule Check on 15 Fixed Prompts ---")
        print(f"Fixed prompt ratings returned: {len(fixed_ratings)} / 30")

if __name__ == '__main__':
    sheet = sys.argv[1] if len(sys.argv) > 1 else 'eval_results/blinded_human_rating_sheet.csv'
    key = sys.argv[2] if len(sys.argv) > 2 else 'eval_results/blinded_rating_key.csv'
    score_ratings(sheet, key)
