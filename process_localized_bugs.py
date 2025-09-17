import os
import csv
import json
from tqdm import tqdm
import argparse
import xml.etree.ElementTree as ET
from glob import glob

def check_localization_at_k(fixed_files, suspicious_files, k):
    """Return True if any fixed file is in the top-k suspicious files."""
    top_files = suspicious_files[:k]
    for fixed_file in fixed_files:
        if fixed_file in top_files:
            return True
    return False


def get_bug_data(xml_report_path):
    bugs = []
    tree = ET.parse(xml_report_path)
    root = tree.getroot()
    for element in root.findall(".//table"):
        bug_id = element[1].text
        summary = element[2].text
        description = element[3].text
        buggy_commit = element[4].text
        fixed_files = (element[5].text).split('.java')

        bug_data = {
            "id": bug_id,
            "summary": summary,
            "description": description,
            "fixed_files": [(file + '.java').strip() for file in fixed_files[:-1]]
        }
        bugs.append(bug_data)

    return bugs

def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Bad JSON on line {ln} in {path}: {e}")

def main(root):
    trial = 3
    # Find all combined_locs.jsonl under results/file_level_combined/<project>/
    pattern = os.path.join(root, f"results{trial}", "file_level_combined", "*", "combined_locs.jsonl")
    paths = glob(pattern)
    if not paths:
        raise SystemExit(f"No files matched: {pattern}")

    all_bug_data = []

    for p in paths:
        project = os.path.basename(os.path.dirname(p))
        bug_data = get_bug_data(f'../sample/{project}.xml')

        print(f"Processing project: {project}")
        results = {}
        for rec in read_jsonl(p):
            bug_id = str(rec.get("instance_id", "")).strip()
            suspicious_files = rec.get("found_files") or []
            if not isinstance(suspicious_files, list):
                suspicious_files = [str(suspicious_files)]
            results[bug_id] = suspicious_files
        
        # print(len(results))
        # print(len(bug_data))
        for bug in bug_data:
            bug_id = bug['id']
            fixed_files = bug['fixed_files']
            suspicious_files = results.get(bug_id, [])

            bug_data_entry = {
                'bug_id': f"{project}-{bug_id}",
                'fixed_files': fixed_files,
                'suspicious_files': suspicious_files
            }

            all_bug_data.append(bug_data_entry)
    
    acc1_ids, acc5_ids, acc10_ids = [], [], []

    for bug in tqdm(all_bug_data, desc="Processing Bugs"):
        bug_id = bug['bug_id']
        fixed_files = bug.get('fixed_files', []) or []
        suspicious_files = bug.get('suspicious_files', []) or []

        if check_localization_at_k(fixed_files, suspicious_files, 1):
            acc1_ids.append(bug_id)
        if check_localization_at_k(fixed_files, suspicious_files, 5):
            acc5_ids.append(bug_id)
        if check_localization_at_k(fixed_files, suspicious_files, 10):
            acc10_ids.append(bug_id)

    # Align rows so CSV has equal length columns (fill empty cells with "")
    max_len = max(len(acc1_ids), len(acc5_ids), len(acc10_ids))
    rows = []
    for i in range(max_len):
        rows.append([
            acc1_ids[i] if i < len(acc1_ids) else "",
            acc5_ids[i] if i < len(acc5_ids) else "",
            acc10_ids[i] if i < len(acc10_ids) else ""
        ])

    out_file = f"localized_bugs{trial}.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["accuracy@1", "accuracy@5", "accuracy@10"])
        writer.writerows(rows)

    print(f"Wrote bug IDs to {out_file}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extract found_files per instance_id per project.")
    ap.add_argument("--root", default=".", help="Repo root (default: current dir)")
    args = ap.parse_args()
    main(args.root)

    
