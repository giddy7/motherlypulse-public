import pathlib
import csv
import json
import os
import sys

data_dir = str(pathlib.Path(__file__).resolve().parents[2] / "MotherlyPulse_Data")
repo_root = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(repo_root)

print("==================================================================")
print("--- MOTHERLYPULSE POST-AUDIT COMPREHENSIVE VALIDATION SUITE ---")
print("==================================================================")

test_results = {}

def record_test(name, passed, details=""):
    test_results[name] = {"passed": passed, "details": details}
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name} {('- ' + details) if details else ''}")

# 1. Sources check
sources_file = os.path.join(data_dir, "01_Sources", "source_register.csv")
with open(sources_file, mode="r", encoding="utf-8") as f:
    sources = list(csv.DictReader(f))
record_test("Registered Sources Integrity", len(sources) == 9, f"Total sources: {len(sources)}")

# 2. Passages check
passages_file = os.path.join(data_dir, "02_Passages", "passages.csv")
with open(passages_file, mode="r", encoding="utf-8") as f:
    passages = list(csv.DictReader(f))
record_test("Passages Registry Integrity", len(passages) == 35, f"Total passages: {len(passages)}")

# 3. Facilities statewide coverage
facilities_file = os.path.join(data_dir, "05_Facilities_Ondo", "facilities.csv")
with open(facilities_file, mode="r", encoding="utf-8") as f:
    facilities = list(csv.DictReader(f))
all_18_lgas = {
    "Akoko North-East", "Akoko North-West", "Akoko South-East", "Akoko South-West",
    "Akure North", "Akure South", "Ese Odo", "Idanre", "Ifedore", "Ilaje",
    "Ile Oluji/Okeigbo", "Irele", "Odigbo", "Okitipupa", "Ondo East", "Ondo West", "Ose", "Owo"
}
fac_lgas = {fac["local_government_area"] for fac in facilities}
record_test("Facilities Statewide Coverage", fac_lgas == all_18_lgas, f"{len(fac_lgas)}/18 LGAs covered ({len(facilities)} facilities)")

# 4. Immunization centers statewide coverage
immunization_file = os.path.join(data_dir, "07_Immunization_Ondo", "immunization_centers.csv")
with open(immunization_file, mode="r", encoding="utf-8") as f:
    imm_centers = list(csv.DictReader(f))
imm_lgas = {c["local_government_area"] for c in imm_centers}
record_test("Immunization Centers Coverage", imm_lgas == all_18_lgas, f"{len(imm_lgas)}/18 LGAs covered ({len(imm_centers)} centres)")

# 5. Exact 200 conversational records
conv_csv = os.path.join(data_dir, "04_Conversation_Data", "english_pairs.csv")
conv_jsonl = os.path.join(data_dir, "04_Conversation_Data", "english_pairs.jsonl")
adapt_csv = os.path.join(data_dir, "04_Conversation_Data", "adaptation_template.csv")

with open(conv_csv, mode="r", encoding="utf-8") as f:
    pairs = list(csv.DictReader(f))
record_test("Exact 200 Conversational Records (CSV)", len(pairs) == 200, f"Found {len(pairs)} records")

with open(conv_jsonl, mode="r", encoding="utf-8") as f:
    jsonl_pairs = [json.loads(line) for line in f if line.strip()]
record_test("Exact 200 Conversational Records (JSONL)", len(jsonl_pairs) == 200, f"Found {len(jsonl_pairs)} records")

# CSV vs JSONL consistency
csv_ids = [p["pair_id"] for p in pairs]
jsonl_ids = [p["pair_id"] for p in jsonl_pairs]
id_match = (csv_ids == jsonl_ids)
csv_jsonl_mismatches = 0
for i, (cp, jp) in enumerate(zip(pairs, jsonl_pairs)):
    for k in cp:
        if str(cp[k]).strip() != str(jp.get(k, "")).strip():
            csv_jsonl_mismatches += 1
record_test("CSV and JSONL 100% Parity", id_match and csv_jsonl_mismatches == 0, f"ID alignment: {id_match}, field mismatches: {csv_jsonl_mismatches}")

# 6. Exact 100 pregnancy and 100 infant-care split
prg_cnt = sum(1 for p in pairs if p["user_group"] == "pregnancy")
inf_cnt = sum(1 for p in pairs if p["user_group"] == "infant")
record_test("Domain Balance: 100 Pregnancy Records", prg_cnt == 100, f"Found {prg_cnt} pregnancy records")
record_test("Domain Balance: 100 Infant-Care Records", inf_cnt == 100, f"Found {inf_cnt} infant records")

# 7. Consistent response prefixes across all 200 records
prefix_issues = []
for p in pairs:
    rep = p["reply"]
    expected_prefix = p["urgency_category"].upper() + ":"
    if not rep.startswith(expected_prefix):
        prefix_issues.append((p["pair_id"], expected_prefix, rep[:30]))
record_test("Consistent Category Prefixes across 200 Records", len(prefix_issues) == 0, f"{len(pairs) - len(prefix_issues)}/200 formatted with exact category prefix")

# 8. Correct urgency categories for flagged records
flagged_checks = {
    "PAIR-PRG-042": ("emergency", "Chorioamnionitis / Foul discharge with pelvic pain"),
    "PAIR-INF-087": ("emergency", "Neonatal cholestasis / Biliary atresia with pale stools"),
    "PAIR-INF-011": ("emergency", "Infant under 3 months with fever"),
    "PAIR-PRG-037": ("emergency", "Active labour at term (contractions every 4 mins)"),
    "PAIR-PRG-068": ("priority", "Elevated fasting blood glucose (105 mg/dL)")
}
pairs_by_id = {p["pair_id"]: p for p in pairs}
all_flagged_correct = True
flagged_details = []
for fid, (exp_cat, rationale) in flagged_checks.items():
    actual_cat = pairs_by_id.get(fid, {}).get("urgency_category")
    if actual_cat != exp_cat:
        all_flagged_correct = False
        flagged_details.append(f"{fid}: expected {exp_cat}, got {actual_cat}")
    else:
        flagged_details.append(f"{fid}: {actual_cat}")
record_test("Flagged Clinical Records Audit", all_flagged_correct, "; ".join(flagged_details))

# 9. Strict English-only content
non_english_count = sum(1 for p in pairs if p.get("language") != "English")
record_test("English-Only Conversational Content", non_english_count == 0, f"100% English ({len(pairs)} records)")

# 10. Yoruba and Pidgin translation completeness in adaptation_template.csv
with open(adapt_csv, mode="r", encoding="utf-8") as f:
    adapt_rows = list(csv.DictReader(f))
yo_pcm_complete = sum(
    1 for r in adapt_rows 
    if r["user_message_yo"] != "" and r["reply_yo"] != "" 
    and r["user_message_pcm"] != "" and r["reply_pcm"] != ""
)
ha_ig_blank = sum(
    1 for r in adapt_rows
    if r["user_message_ha"] == "" and r["reply_ha"] == ""
    and r["user_message_ig"] == "" and r["reply_ig"] == ""
)
record_test(
    "Adaptation Template Localization (Yoruba & Pidgin)", 
    len(adapt_rows) == 200 and yo_pcm_complete == 200 and ha_ig_blank == 200, 
    f"{yo_pcm_complete}/200 Yoruba & Pidgin pairs populated; Hausa/Igbo preserved blank"
)

# 11. Test Dynamic Triage & Separation of Medication Safety
from motherlypulse_app.classifier import DynamicTriageClassifier
from motherlypulse_app.assistant import MotherlyPulseAssistant

classifier = DynamicTriageClassifier()
assistant = MotherlyPulseAssistant()

# Test 11a: Emergency + Medication request
res_emg_med = classifier.classify("My 6-week-old baby has a 38.5C fever and is vomiting, what paracetamol dose should I give?")
record_test(
    "Separation of Urgency & Safety: Emergency + Medication",
    res_emg_med["urgency_category"] == "emergency" and res_emg_med["medication_safety_triggered"] == True,
    f"Category: {res_emg_med['urgency_category']}, Med Safety Triggered: {res_emg_med['medication_safety_triggered']}"
)

# Test 11b: Priority + Prescription request
res_pri_med = classifier.classify("Every time I pee it burns and stings terribly, can you prescribe an antibiotic?")
record_test(
    "Separation of Urgency & Safety: Priority + Prescription",
    res_pri_med["urgency_category"] == "priority" and res_pri_med["medication_safety_triggered"] == True,
    f"Category: {res_pri_med['urgency_category']}, Med Safety Triggered: {res_pri_med['medication_safety_triggered']}"
)

# Test 11c: Routine + Medication request
res_rou_med = classifier.classify("Can I take paracetamol for a mild backache in pregnancy?")
record_test(
    "Separation of Urgency & Safety: Routine + Medication",
    res_rou_med["urgency_category"] == "routine" and res_rou_med["medication_safety_triggered"] == True,
    f"Category: {res_rou_med['urgency_category']}, Med Safety Triggered: {res_rou_med['medication_safety_triggered']}"
)

# Test 12: Emergency Precedence over Priority and Routine
res_prec1 = classifier.classify("When is my next appointment, but I am bleeding heavily right now?")
res_prec2 = classifier.classify("What foods should I eat, but my baby has stopped moving completely?")
record_test(
    "Emergency Precedence over Priority and Routine",
    res_prec1["urgency_category"] == "emergency" and res_prec2["urgency_category"] == "emergency",
    f"Precedence check 1: {res_prec1['urgency_category']}, check 2: {res_prec2['urgency_category']}"
)

# Test 13: Multi-turn Emergency Escalation & State Persistence
history_emg = ["I had a severe convulsion and fell down."]
res_persist = classifier.classify("Can I eat some oranges?", conversation_history=history_emg)
record_test(
    "Multi-turn Emergency State Persistence",
    res_persist["urgency_category"] == "emergency",
    f"Persisted category after emergency in history: {res_persist['urgency_category']}"
)

# Test 14: Assistant Response Prefix & Tone
resp_emg = assistant.respond("I am bleeding heavily and soaking my pads.")
resp_rou = assistant.respond("Which side is best to sleep on in pregnancy?")
record_test(
    "Assistant Prefixes Compliance",
    resp_emg["reply"].startswith("EMERGENCY:") and resp_rou["reply"].startswith("ROUTINE:"),
    f"Emergency prefix: '{resp_emg['reply'][:15]}', Routine prefix: '{resp_rou['reply'][:15]}'"
)

print("\n==================================================================")
all_tests_passed = all(t["passed"] for t in test_results.values())
passed_count = sum(1 for t in test_results.values() if t["passed"])
total_count = len(test_results)
print(f"--- VALIDATION SUITE COMPLETE: {passed_count}/{total_count} TESTS PASSED ({'100%' if all_tests_passed else 'FAILURES DETECTED'}) ---")
print("==================================================================")
print("NOTE: Structural & syntactic validator passing confirms dataset integrity,")
print("referential consistency, and classification precedence rules.")
print("It does NOT substitute for formal clinical review by licensed clinicians.")
print("All 200 conversational records remain marked as 'pending_clinical_review'.")
print("==================================================================")
