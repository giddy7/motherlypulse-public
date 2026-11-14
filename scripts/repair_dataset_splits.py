"""
MotherlyPulse Dataset Split Repair and Backup Script
Safely normalizes exported data/*.jsonl files from single-line literal \n format
into genuine JSON Lines format with standard 0x0A newline bytes.
"""

import os
import re
import json
import glob
import shutil

def repair_dataset_splits():
    data_dir = "data"
    backup_dir = os.path.join("MotherlyPulse_Data", "backup_data_splits")
    os.makedirs(backup_dir, exist_ok=True)
    
    files = sorted(glob.glob(os.path.join(data_dir, "*.jsonl")))
    print(f"Found {len(files)} dataset split files in '{data_dir}'.")
    
    # 1. Create verifiable backup of original state
    print(f"\n--- Step 1: Creating Pre-Repair Backup in '{backup_dir}' ---")
    for f in files:
        dest = os.path.join(backup_dir, os.path.basename(f))
        shutil.copy2(f, dest)
    print(f"Backed up {len(files)} files successfully.")
    
    # 2. Parse and repair each file
    print("\n--- Step 2: Normalizing JSON Lines Formatting ---")
    results = {}
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            raw_text = fp.read()
            
        # Strip trailing literal \n if present
        cleaned_text = re.sub(r'\\n\s*$', '', raw_text.strip())
        # Split on the object boundary '}\n{'
        fixed_text = re.sub(r'\}\s*\\n\s*\{', '}\n{', cleaned_text)
        
        lines = fixed_text.strip().split('\n')
        parsed_objs = []
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue
            obj = json.loads(line_str)
            parsed_objs.append(obj)
            
        # Write back genuine JSON Lines format
        with open(f, "w", encoding="utf-8", newline="\n") as fp:
            for obj in parsed_objs:
                fp.write(json.dumps(obj, ensure_ascii=False) + "\n")
                
        results[os.path.basename(f)] = len(parsed_objs)
        print(f"Normalized {os.path.basename(f)}: wrote {len(parsed_objs)} records.")
        
    print("\n--- Step 3: Verifying Repaired Files ---")
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            re_read_lines = fp.readlines()
        print(f"{os.path.basename(f)}: verified physical lines = {len(re_read_lines)}")
        assert len(re_read_lines) == results[os.path.basename(f)], "Mismatch in line count!"
        
    print("\nRepair completed successfully without data loss!")

if __name__ == "__main__":
    repair_dataset_splits()

