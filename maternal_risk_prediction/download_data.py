import os
import urllib.request
import pandas as pd

BASE_URL = "https://huggingface.co/buckets/gidey7/maternal-health-pregnancy-bucket/resolve"

files_to_download = [
    ("README.md", "maternal_risk_prediction/data/DATASET_README.md"),
    ("data/maternal_low_burden.csv", "maternal_risk_prediction/data/maternal_low_burden.csv"),
    ("data/maternal_moderate_burden.csv", "maternal_risk_prediction/data/maternal_moderate_burden.csv"),
    ("data/maternal_high_burden.csv", "maternal_risk_prediction/data/maternal_high_burden.csv"),
    ("generate_dataset.py", "maternal_risk_prediction/data/generate_dataset.py"),
    ("validate_dataset.py", "maternal_risk_prediction/data/validate_dataset.py"),
    ("requirements.txt", "maternal_risk_prediction/data/requirements.txt")
]

headers = {'User-Agent': 'Mozilla/5.0'}

os.makedirs("maternal_risk_prediction/data", exist_ok=True)

for remote_rel, local_dest in files_to_download:
    url = f"{BASE_URL}/{remote_rel}?download=true"
    print(f"Downloading {url} -> {local_dest} ...")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, open(local_dest, "wb") as out:
            data = resp.read()
            out.write(data)
            print(f" Saved {local_dest} ({len(data):,} bytes)")
    except Exception as e:
        print(f" ERROR downloading {remote_rel}: {e}")

print("\n--- Verifying Downloaded CSV Datasets ---")
csv_files = [
    "maternal_risk_prediction/data/maternal_low_burden.csv",
    "maternal_risk_prediction/data/maternal_moderate_burden.csv",
    "maternal_risk_prediction/data/maternal_high_burden.csv"
]

total_rows = 0
for f in csv_files:
    if os.path.exists(f):
        df = pd.read_csv(f)
        total_rows += len(df)
        print(f" {os.path.basename(f)}: {len(df):,} rows x {len(df.columns)} columns")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Risk level distribution: {dict(df['risk_level'].value_counts())}")
        print(f"   Complications: {dict(df['primary_complication'].value_counts())}\n")
    else:
        print(f" Missing file: {f}")

print(f"Total downloaded patient records: {total_rows:,}")
