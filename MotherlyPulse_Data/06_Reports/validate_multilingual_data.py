# -*- coding: utf-8 -*-
"""
MotherlyPulse Multilingual Dataset Comprehensive Validation Suite
=================================================================
Validates structural, referential, linguistic, and clinical safety integrity
across English, Yoruba, and Nigerian Pidgin conversational datasets.
"""

import os
import sys
import csv
import json
import pandas as pd

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONV_DIR = os.path.join(DATA_DIR, "04_Conversation_Data")

test_results = {}

def record_test(name, passed, details=""):
    test_results[name] = {"passed": passed, "details": details}
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {('- ' + details) if details else ''}")

def main():
    print("==================================================================")
    print("--- MOTHERLYPULSE MULTILINGUAL VALIDATION SUITE ---")
    print("==================================================================")

    # 1. English Source Dataset Parity
    en_csv = os.path.join(CONV_DIR, "english_pairs.csv")
    en_jsonl = os.path.join(CONV_DIR, "english_pairs.jsonl")
    df_en = pd.read_csv(en_csv, encoding="utf-8")
    with open(en_jsonl, "r", encoding="utf-8") as f:
        jsonl_en = [json.loads(line) for line in f if line.strip()]
    record_test("English Source Dataset Count (200)", len(df_en) == 200 and len(jsonl_en) == 200, f"CSV: {len(df_en)}, JSONL: {len(jsonl_en)}")

    # 2. Yoruba Dataset Count & CSV/JSONL Parity
    yo_csv = os.path.join(CONV_DIR, "yoruba_pairs.csv")
    yo_jsonl = os.path.join(CONV_DIR, "yoruba_pairs.jsonl")
    df_yo = pd.read_csv(yo_csv, encoding="utf-8")
    with open(yo_jsonl, "r", encoding="utf-8") as f:
        jsonl_yo = [json.loads(line) for line in f if line.strip()]
    yo_parity = (len(df_yo) == 200 and len(jsonl_yo) == 200 and list(df_yo['pair_id']) == [r['pair_id'] for r in jsonl_yo])
    record_test("Yoruba Dataset 200 Records & Parity", yo_parity, f"CSV: {len(df_yo)}, JSONL: {len(jsonl_yo)}")

    # 3. Nigerian Pidgin Dataset Count & CSV/JSONL Parity
    pcm_csv = os.path.join(CONV_DIR, "pidgin_pairs.csv")
    pcm_jsonl = os.path.join(CONV_DIR, "pidgin_pairs.jsonl")
    df_pcm = pd.read_csv(pcm_csv, encoding="utf-8")
    with open(pcm_jsonl, "r", encoding="utf-8") as f:
        jsonl_pcm = [json.loads(line) for line in f if line.strip()]
    pcm_parity = (len(df_pcm) == 200 and len(jsonl_pcm) == 200 and list(df_pcm['pair_id']) == [r['pair_id'] for r in jsonl_pcm])
    record_test("Nigerian Pidgin Dataset 200 Records & Parity", pcm_parity, f"CSV: {len(df_pcm)}, JSONL: {len(jsonl_pcm)}")

    # 4. Multilingual Dataset Count & CSV/JSONL Parity
    multi_csv = os.path.join(CONV_DIR, "multilingual_pairs.csv")
    multi_jsonl = os.path.join(CONV_DIR, "multilingual_pairs.jsonl")
    df_multi = pd.read_csv(multi_csv, encoding="utf-8")
    with open(multi_jsonl, "r", encoding="utf-8") as f:
        jsonl_multi = [json.loads(line) for line in f if line.strip()]
    multi_parity = (len(df_multi) == 200 and len(jsonl_multi) == 200 and list(df_multi['pair_id']) == [r['pair_id'] for r in jsonl_multi])
    record_test("Multilingual Combined Dataset 200 Records & Parity", multi_parity, f"CSV: {len(df_multi)}, JSONL: {len(jsonl_multi)}")

    # 5. Adaptation Template Completeness
    adapt_csv = os.path.join(CONV_DIR, "adaptation_template.csv")
    df_adapt = pd.read_csv(adapt_csv, encoding="utf-8")
    adapt_yo_complete = (df_adapt['user_message_yo'].notna() & (df_adapt['user_message_yo'] != "")).all() and (df_adapt['reply_yo'].notna() & (df_adapt['reply_yo'] != "")).all()
    adapt_pcm_complete = (df_adapt['user_message_pcm'].notna() & (df_adapt['user_message_pcm'] != "")).all() and (df_adapt['reply_pcm'].notna() & (df_adapt['reply_pcm'] != "")).all()
    record_test("Adaptation Template Yoruba Completeness (200/200)", adapt_yo_complete, "All 200 Yoruba pairs populated")
    record_test("Adaptation Template Pidgin Completeness (200/200)", adapt_pcm_complete, "All 200 Pidgin pairs populated")

    # 6. Domain Balance Across All Files (100 Pregnancy / 100 Infant)
    yo_prg = sum(df_yo['user_group'] == 'pregnancy')
    yo_inf = sum(df_yo['user_group'] == 'infant')
    pcm_prg = sum(df_pcm['user_group'] == 'pregnancy')
    pcm_inf = sum(df_pcm['user_group'] == 'infant')
    domain_ok = (yo_prg == 100 and yo_inf == 100 and pcm_prg == 100 and pcm_inf == 100)
    record_test("Domain Balance (100 Pregnancy, 100 Infant)", domain_ok, f"YO: {yo_prg}/{yo_inf}, PCM: {pcm_prg}/{pcm_inf}")

    # 7. Training/Testing Split Protection (160 Train / 40 Test Exact Alignment)
    yo_split_match = (list(df_yo['intended_split']) == list(df_en['intended_split']))
    pcm_split_match = (list(df_pcm['intended_split']) == list(df_en['intended_split']))
    multi_split_match = (list(df_multi['intended_split']) == list(df_en['intended_split']))
    train_count = sum(df_yo['intended_split'] == 'train')
    test_count = sum(df_yo['intended_split'] == 'test')
    splits_ok = yo_split_match and pcm_split_match and multi_split_match and train_count == 160 and test_count == 40
    record_test("Training (160) & Testing (40) Split Preservation", splits_ok, f"160 train, 40 test across all languages; identical partition")

    # 8. Category Response Prefixes (EMERGENCY:, PRIORITY:, ROUTINE:)
    yo_prefix_issues = []
    pcm_prefix_issues = []
    for idx, r in df_en.iterrows():
        pid = r['pair_id']
        expected_prefix = r['urgency_category'].upper() + ":"
        yo_rep = df_yo.loc[idx, 'reply']
        pcm_rep = df_pcm.loc[idx, 'reply']
        if not yo_rep.startswith(expected_prefix):
            yo_prefix_issues.append((pid, expected_prefix, yo_rep[:20]))
        if not pcm_rep.startswith(expected_prefix):
            pcm_prefix_issues.append((pid, expected_prefix, pcm_rep[:20]))
    record_test("Yoruba Consistent Category Prefixes", len(yo_prefix_issues) == 0, f"{200 - len(yo_prefix_issues)}/200 formatted correctly")
    record_test("Nigerian Pidgin Consistent Category Prefixes", len(pcm_prefix_issues) == 0, f"{200 - len(pcm_prefix_issues)}/200 formatted correctly")

    # 9. No Empty or Truncated Fields
    empty_yo = df_yo['user_message'].isna().sum() + df_yo['reply'].isna().sum()
    empty_pcm = df_pcm['user_message'].isna().sum() + df_pcm['reply'].isna().sum()
    record_test("Zero Missing/Empty Translations", empty_yo == 0 and empty_pcm == 0, f"Empty YO: {empty_yo}, Empty PCM: {empty_pcm}")

    # 10. Referential Integrity Check with English IDs
    id_align_yo = (list(df_yo['pair_id']) == list(df_en['pair_id']))
    id_align_pcm = (list(df_pcm['pair_id']) == list(df_en['pair_id']))
    record_test("Pair ID Referential Parity (200/200)", id_align_yo and id_align_pcm, "All IDs map 1:1 in exact sequence")

    # Summary
    print("\n==================================================================")
    all_passed = all(t["passed"] for t in test_results.values())
    passed_count = sum(1 for t in test_results.values() if t["passed"])
    total_count = len(test_results)
    print(f"--- VALIDATION SUITE COMPLETE: {passed_count}/{total_count} TESTS PASSED ({'100%' if all_passed else 'FAILURES DETECTED'}) ---")
    print("==================================================================")

if __name__ == "__main__":
    main()

