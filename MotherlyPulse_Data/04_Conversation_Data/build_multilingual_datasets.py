# -*- coding: utf-8 -*-
"""
Build Multilingual Conversational Datasets
=========================================
Generates:
1. yoruba_pairs.csv & yoruba_pairs.jsonl (200 records)
2. pidgin_pairs.csv & pidgin_pairs.jsonl (200 records)
3. multilingual_pairs.csv & multilingual_pairs.jsonl (200 records combining EN, YO, PCM)
4. Updates adaptation_template.csv with yo and pcm fields
"""

import os
import sys
import csv
import json
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

from maternal_translations_prg_1 import PRG_001_025
from maternal_translations_prg_2 import PRG_026_050
from maternal_translations_prg_3 import PRG_051_075
from maternal_translations_prg_4 import PRG_076_100
from maternal_translations_inf_1 import INF_001_025
from maternal_translations_inf_2 import INF_026_050
from maternal_translations_inf_3 import INF_051_075
from maternal_translations_inf_4 import INF_076_100

def load_all_translations():
    all_trans = {}
    for d in [PRG_001_025, PRG_026_050, PRG_051_075, PRG_076_100,
              INF_001_025, INF_026_050, INF_051_075, INF_076_100]:
        all_trans.update(d)
    return all_trans

def main():
    en_csv_path = os.path.join(CURRENT_DIR, "english_pairs.csv")
    df_en = pd.read_csv(en_csv_path, encoding="utf-8")
    translations = load_all_translations()
    
    print(f"Loaded {len(df_en)} English source records.")
    print(f"Loaded {len(translations)} translation mappings.")
    
    assert len(df_en) == 200, f"Expected 200 English records, got {len(df_en)}"
    assert len(translations) == 200, f"Expected 200 translations, got {len(translations)}"
    
    # ---------------------------------------------------------
    # 1. Yoruba Pairs (CSV & JSONL)
    # ---------------------------------------------------------
    yo_rows = []
    for _, r in df_en.iterrows():
        pid = r['pair_id']
        t = translations[pid]
        yo_msg, yo_reply = t['yo']
        
        row = {
            'pair_id': pid,
            'user_group': r['user_group'],
            'intended_split': r['intended_split'],
            'user_message': yo_msg,
            'intent': r['intent'],
            'triage_level': r['triage_level'],
            'urgency_category': r['urgency_category'],
            'language': 'Yoruba',
            'topic': r['topic'],
            'reply': yo_reply,
            'passage_id': r['passage_id'],
            'review_status': 'initial_translation_pending_human_review',
            'notes': f"Translated to Yoruba. Urgency prefix: {r['urgency_category'].upper()}."
        }
        yo_rows.append(row)
        
    df_yo = pd.DataFrame(yo_rows)
    yo_csv_path = os.path.join(CURRENT_DIR, "yoruba_pairs.csv")
    yo_jsonl_path = os.path.join(CURRENT_DIR, "yoruba_pairs.jsonl")
    df_yo.to_csv(yo_csv_path, index=False, encoding="utf-8")
    with open(yo_jsonl_path, "w", encoding="utf-8") as f:
        for row in yo_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Successfully generated {yo_csv_path} and {yo_jsonl_path} ({len(yo_rows)} records).")

    # ---------------------------------------------------------
    # 2. Nigerian Pidgin Pairs (CSV & JSONL)
    # ---------------------------------------------------------
    pcm_rows = []
    for _, r in df_en.iterrows():
        pid = r['pair_id']
        t = translations[pid]
        pcm_msg, pcm_reply = t['pcm']
        
        row = {
            'pair_id': pid,
            'user_group': r['user_group'],
            'intended_split': r['intended_split'],
            'user_message': pcm_msg,
            'intent': r['intent'],
            'triage_level': r['triage_level'],
            'urgency_category': r['urgency_category'],
            'language': 'Nigerian Pidgin',
            'topic': r['topic'],
            'reply': pcm_reply,
            'passage_id': r['passage_id'],
            'review_status': 'initial_translation_pending_human_review',
            'notes': f"Translated to Nigerian Pidgin. Urgency prefix: {r['urgency_category'].upper()}."
        }
        pcm_rows.append(row)
        
    df_pcm = pd.DataFrame(pcm_rows)
    pcm_csv_path = os.path.join(CURRENT_DIR, "pidgin_pairs.csv")
    pcm_jsonl_path = os.path.join(CURRENT_DIR, "pidgin_pairs.jsonl")
    df_pcm.to_csv(pcm_csv_path, index=False, encoding="utf-8")
    with open(pcm_jsonl_path, "w", encoding="utf-8") as f:
        for row in pcm_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Successfully generated {pcm_csv_path} and {pcm_jsonl_path} ({len(pcm_rows)} records).")

    # ---------------------------------------------------------
    # 3. Combined Multilingual Pairs (CSV & JSONL)
    # ---------------------------------------------------------
    multi_rows = []
    for _, r in df_en.iterrows():
        pid = r['pair_id']
        t = translations[pid]
        yo_msg, yo_reply = t['yo']
        pcm_msg, pcm_reply = t['pcm']
        
        row = {
            'pair_id': pid,
            'user_group': r['user_group'],
            'intended_split': r['intended_split'],
            'intent': r['intent'],
            'triage_level': r['triage_level'],
            'urgency_category': r['urgency_category'],
            'topic': r['topic'],
            'passage_id': r['passage_id'],
            'user_message_en': r['user_message'],
            'reply_en': r['reply'],
            'user_message_yo': yo_msg,
            'reply_yo': yo_reply,
            'user_message_pcm': pcm_msg,
            'reply_pcm': pcm_reply,
            'review_status': 'initial_translation_pending_human_review',
            'notes': r['notes']
        }
        multi_rows.append(row)
        
    df_multi = pd.DataFrame(multi_rows)
    multi_csv_path = os.path.join(CURRENT_DIR, "multilingual_pairs.csv")
    multi_jsonl_path = os.path.join(CURRENT_DIR, "multilingual_pairs.jsonl")
    df_multi.to_csv(multi_csv_path, index=False, encoding="utf-8")
    with open(multi_jsonl_path, "w", encoding="utf-8") as f:
        for row in multi_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Successfully generated {multi_csv_path} and {multi_jsonl_path} ({len(multi_rows)} records).")

    # ---------------------------------------------------------
    # 4. Update adaptation_template.csv
    # ---------------------------------------------------------
    adapt_path = os.path.join(CURRENT_DIR, "adaptation_template.csv")
    adapt_rows = []
    for _, r in df_en.iterrows():
        pid = r['pair_id']
        t = translations[pid]
        yo_msg, yo_reply = t['yo']
        pcm_msg, pcm_reply = t['pcm']
        
        row = {
            'pair_id': pid,
            'user_group': r['user_group'],
            'intended_split': r['intended_split'],
            'user_message_en': r['user_message'],
            'reply_en': r['reply'],
            'user_message_yo': yo_msg,
            'reply_yo': yo_reply,
            'user_message_ha': '',
            'reply_ha': '',
            'user_message_ig': '',
            'reply_ig': '',
            'user_message_pcm': pcm_msg,
            'reply_pcm': pcm_reply,
            'reviewer_name': '',
            'review_status': 'initial_translation_pending_human_review'
        }
        adapt_rows.append(row)
        
    df_adapt = pd.DataFrame(adapt_rows)
    df_adapt.to_csv(adapt_path, index=False, encoding="utf-8")
    print(f"Successfully updated {adapt_path} ({len(adapt_rows)} records).")

if __name__ == "__main__":
    main()

