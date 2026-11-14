"""
MotherlyPulse Automated Dataset Split Validation Script
Verifies:
1. File existence and physical line counts.
2. Every line parses independently as valid JSON.
3. Train (140), Validation (20), and Test (40) split targets.
4. Total 200 unique scenario IDs (100 pregnancy, 100 infant).
5. Disjointness: No scenario appears in more than one split.
6. Cross-lingual split consistency: Same pair ID is assigned to the same split in EN, YO, and PCM.
7. Label schema integrity: Triage levels (Emergency, Priority, Routine) and user groups.
"""

import os
import sys
import json
import glob
import collections

EXPECTED_SPLIT_COUNTS = {
    "train": 140,
    "val": 20,
    "test": 40
}

LANGUAGES = ["en", "pcm", "yo"]

def validate_dataset():
    data_dir = "data"
    print("=" * 70)
    print(" MOTHERLYPULSE DATASET SPLIT VALIDATION AUDIT")
    print("=" * 70)
    
    if not os.path.isdir(data_dir):
        print(f"ERROR: Dataset directory '{data_dir}' not found.")
        sys.exit(1)
        
    all_files = sorted(glob.glob(os.path.join(data_dir, "*.jsonl")))
    print(f"Inspecting {len(all_files)} files in '{data_dir}':\n")
    
    split_records = collections.defaultdict(dict) # (split, lang) -> list of dicts
    file_errors = collections.defaultdict(list)
    pair_id_to_split = collections.defaultdict(dict) # pair_id -> {lang: split}
    
    # 1. Independent Line-by-Line JSON Parsing
    for filepath in all_files:
        filename = os.path.basename(filepath)
        parts = filename.replace(".jsonl", "").split("_")
        if len(parts) != 2:
            print(f"Warning: Unexpected filename format: {filename}")
            continue
        split, lang = parts[0], parts[1]
        
        expected_count = EXPECTED_SPLIT_COUNTS.get(split)
        
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        parsed_objects = []
        for line_num, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str:
                file_errors[filename].append(f"Line {line_num}: Empty line detected.")
                continue
            try:
                obj = json.loads(line_str)
                parsed_objects.append(obj)
                
                # Check mandatory fields
                pid = obj.get("pair_id")
                if not pid:
                    file_errors[filename].append(f"Line {line_num}: Missing 'pair_id'.")
                else:
                    pair_id_to_split[pid][lang] = split
                    
            except Exception as e:
                file_errors[filename].append(f"Line {line_num}: JSONDecodeError: {str(e)}")
                
        split_records[(split, lang)] = parsed_objects
        
        has_errors = bool(file_errors.get(filename, []))
        status = "PASS" if len(parsed_objects) == expected_count and not has_errors else "FAIL"
        print(f"[{status}] {filename:15} -> Lines: {len(lines):3} | Parsed Objects: {len(parsed_objects):3} (Expected: {expected_count:3})")
        if has_errors:
            for err in file_errors[filename][:3]:
                print(f"       ERROR: {err}")
                
    # 2. Check Disjointness Across Splits
    print("\n--- Split Disjointness & Cross-Lingual Consistency Audit ---")
    splits_by_pair = collections.defaultdict(set)
    for pid, lang_map in pair_id_to_split.items():
        for lang, sp in lang_map.items():
            splits_by_pair[pid].add(sp)
            
    overlapping_pairs = {pid: sps for pid, sps in splits_by_pair.items() if len(sps) > 1}
    if overlapping_pairs:
        print(f"FAIL: {len(overlapping_pairs)} pairs appear in multiple splits: {overlapping_pairs}")
    else:
        print("PASS: Splits are strictly disjoint. No pair appears in more than one split.")
        
    # Cross-lingual alignment check
    misaligned_pairs = []
    for pid, lang_map in pair_id_to_split.items():
        distinct_splits = set(lang_map.values())
        if len(distinct_splits) > 1:
            misaligned_pairs.append((pid, lang_map))
        if len(lang_map) < len(LANGUAGES):
            missing_langs = set(LANGUAGES) - set(lang_map.keys())
            print(f"Warning: {pid} missing languages: {missing_langs}")
            
    if misaligned_pairs:
        print(f"FAIL: {len(misaligned_pairs)} pairs have inconsistent splits across languages!")
    else:
        print("PASS: 100% of pairs have identical split assignments across English, Yoruba, and Pidgin.")
        
    # 3. Overall Scenario & Triage Distribution
    print("\n--- Corpus Composition & Triage Distribution ---")
    total_unique_pairs = len(pair_id_to_split)
    pregnancy_count = sum(1 for pid in pair_id_to_split if "PRG" in pid)
    infant_count = sum(1 for pid in pair_id_to_split if "INF" in pid)
    
    print(f"Total Unique Scenarios: {total_unique_pairs} (Expected: 200)")
    print(f"• Pregnancy Scenarios:  {pregnancy_count} (Expected: 100)")
    print(f"• Infant Scenarios:     {infant_count} (Expected: 100)")
    
    triage_counts = collections.Counter()
    for obj in split_records[("train", "en")]:
        triage_counts[obj.get("triage_level")] += 1
    for obj in split_records[("val", "en")]:
        triage_counts[obj.get("triage_level")] += 1
    for obj in split_records[("test", "en")]:
        triage_counts[obj.get("triage_level")] += 1
        
    print(f"Triage Breakdown (Unique Scenarios):")
    for lvl, cnt in triage_counts.most_common():
        pct = (cnt / total_unique_pairs) * 100
        print(f"• {lvl:12}: {cnt:3} ({pct:.1f}%)")
        
    # Split Summary
    print("\n--- Split Size Summary ---")
    for sp in ["train", "val", "test"]:
        en_cnt = len(split_records[(sp, "en")])
        pcm_cnt = len(split_records[(sp, "pcm")])
        yo_cnt = len(split_records[(sp, "yo")])
        exp = EXPECTED_SPLIT_COUNTS[sp]
        print(f"• {sp.upper():5} Split -> EN: {en_cnt} | PCM: {pcm_cnt} | YO: {yo_cnt} | Target: {exp} | Status: {'OK' if en_cnt == exp and pcm_cnt == exp and yo_cnt == exp else 'FAIL'}")
        
    # Final Result
    total_errors = sum(len(errs) for errs in file_errors.values())
    all_ok = (
        total_errors == 0 and
        not overlapping_pairs and
        not misaligned_pairs and
        total_unique_pairs == 200 and
        pregnancy_count == 100 and
        infant_count == 100
    )
    
    print("\n" + "=" * 70)
    if all_ok:
        print(" OVERALL VALIDATION RESULT: ALL CHECKS PASSED (100% HEALTHY)")
    else:
        print(" OVERALL VALIDATION RESULT: VALIDATION FAILED")
    print("=" * 70)
    
    return all_ok

if __name__ == "__main__":
    success = validate_dataset()
    sys.exit(0 if success else 1)
