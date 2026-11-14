import pandas as pd
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def analyze_df(df, title):
    print("=" * 70)
    print(f"=== {title} ===")
    print("=" * 70)
    print("Total rows:", len(df))
    
    # Map column names if needed
    col_group = 'group' if 'group' in df.columns else 'dataset_source'
    col_lang = 'lang' if 'lang' in df.columns else 'language'
    col_triage = 'triage' if 'triage' in df.columns else 'triage_level'
    col_safe = 'is_safe' if 'is_safe' in df.columns else 'safety_pass'
    col_esc = 'escalates_112' if 'escalates_112' in df.columns else 'escalation_pass'
    col_id = 'item_id' if 'item_id' in df.columns else 'prompt_id'
    col_viol = 'violations' if 'violations' in df.columns else 'contra_violations'

    print("Groups:", df[col_group].value_counts().to_dict())
    print("Languages:", df[col_lang].value_counts().to_dict())
    print("Triage Levels:", df[col_triage].value_counts().to_dict())
    print(f"Overall Safety Pass Rate: {df[col_safe].mean()*100:.2f}% ({df[col_safe].sum()}/{len(df)})")
    
    if 'has_prefix' in df.columns:
        print(f"Category Prefix Compliance: {df['has_prefix'].mean()*100:.2f}% ({df['has_prefix'].sum()}/{len(df)})")
    
    em_df = df[df[col_triage].str.lower() == 'emergency']
    print(f"Emergency Escalation Rate (112): {em_df[col_esc].mean()*100:.2f}% ({em_df[col_esc].sum()}/{len(em_df)})")
    
    print("\n--- Breakdown by Language ---")
    lang_summary = df.groupby(col_lang).agg(
        count=(col_id, 'count'),
        safety_pass=(col_safe, lambda x: f"{x.mean()*100:.1f}%"),
        emergency_112=(col_esc, lambda x: f"{df.loc[x.index][df.loc[x.index, col_triage].str.lower() == 'emergency'][col_esc].mean()*100:.1f}%")
    ).reset_index()
    print(lang_summary.to_string(index=False))

    print("\n--- Breakdown by Group ---")
    grp_summary = df.groupby(col_group).agg(
        count=(col_id, 'count'),
        safety_pass=(col_safe, lambda x: f"{x.mean()*100:.1f}%")
    ).reset_index()
    print(grp_summary.to_string(index=False))

    print(f"\nFailed cases ({len(df[~df[col_safe]])} items):")
    for idx, r in df[~df[col_safe]].head(10).iterrows():
        print(f"  [{r[col_id]}] ({r[col_lang]} | {r[col_triage]}) Escalation: {r[col_esc]} | Violations: {r[col_viol]}")
        print(f"  Prompt: {str(r['prompt'])[:80]}...")
        print(f"  Response: {str(r['response'])[:100]}...\n")

def main():
    import os
    if os.path.exists('eval_results/chewie_baseline_eval.csv'):
        base = pd.read_csv('eval_results/chewie_baseline_eval.csv')
        analyze_df(base, "CHEWIE 1.2 BASELINE (PRETRAINED GEMMA 2B)")

    if os.path.exists('eval_results/chewie_finetuned_eval.csv'):
        ft = pd.read_csv('eval_results/chewie_finetuned_eval.csv')
        analyze_df(ft, "CHEWIE 1.2 FINE-TUNED (QLORA GEMMA 2B)")

    if os.path.exists('eval_results/mamabot_baseline_eval.csv'):
        mb_base = pd.read_csv('eval_results/mamabot_baseline_eval.csv')
        analyze_df(mb_base, "MAMABOT-LLAMA 3.1 8B BASELINE")

    if os.path.exists('eval_results/mamabot_finetuned_eval.csv'):
        mb_ft = pd.read_csv('eval_results/mamabot_finetuned_eval.csv')
        analyze_df(mb_ft, "MAMABOT-LLAMA 3.1 8B FINE-TUNED")

if __name__ == '__main__':
    main()
