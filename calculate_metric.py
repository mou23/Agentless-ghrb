#!/usr/bin/env python3
import os
import json
import csv
import argparse
import xml.etree.ElementTree as ET
from glob import glob

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

def calculate_accuracy_at_k(bug_data):
    for top in [1,5,10]:
        count = 0
        total_bug = 0
        for bug in bug_data:
            suspicious_files = bug['suspicious_files']
            # length_of_suspicious_files = len(suspicious_files)

            fixed_files = bug['fixed_files']

            # fixed_files = bug['fixed_files'].split('.java')
            # fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]

            # print(bug['bug_id'], fixed_files)
            for fixed_file in fixed_files:
                if fixed_file in suspicious_files[0:top]:
                    # print(bug['bug_id'],fixed_file)
                    count = count + 1
                    break
            total_bug = total_bug + 1
        print('accuracy@', top, count, total_bug, (count*100/total_bug))


def calculate_mean_reciprocal_rank_at_k(bug_data):
    for top in [10]:
        total_bug = 0
        inverse_rank = 0
        for bug in bug_data:
            suspicious_files = bug['suspicious_files']
            length_of_suspicious_files = len(suspicious_files)
            fixed_files = bug['fixed_files']

            # fixed_files = bug['fixed_files'].split('.java')
            # fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]
            # print("ID ",item['bug_id'])
            # print(suspicious_files)
            # print("length_of_suspicious_files",length_of_suspicious_files)
            minimum_length = min(top,length_of_suspicious_files)
            for i in range(minimum_length):
                if(suspicious_files[i] in fixed_files):
                    # print('first rank', item['bug_id'], i+1, suspicious_files[i])
                    inverse_rank = inverse_rank + (1/(i+1))
                    break
            total_bug = total_bug + 1
        if inverse_rank == 0:
            print("MRR@", top, 0)
        else:
            print("MRR@", top, (1/total_bug)*inverse_rank, total_bug)
           
     
def calculate_mean_average_precision_at_k(bug_data):
    for top in [10]:
        total_bug = 0
        total_average_precision = 0
        for bug in bug_data:
            total_bug = total_bug + 1
            average_precision = 0
            precision = 0
            suspicious_files = bug['suspicious_files']
            length_of_suspicious_files = len(suspicious_files)
            fixed_files = bug['fixed_files']

            if not fixed_files:
                continue
            # fixed_files = bug['fixed_files'].split('.java')
            # fixed_files = [(file + '.java').strip() for file in fixed_files[:-1]]
            number_of_relevant_files = 0
            minimum_length = min(top,length_of_suspicious_files)
            for i in range(minimum_length):
                # print("i",i)
                if(suspicious_files[i] in fixed_files):
                    # print(item['bug_id'],suspicious_files[i], " relevant")
                    number_of_relevant_files = number_of_relevant_files + 1                        
                    precision = precision + (number_of_relevant_files/(i+1))
                # print("precision ", precision)
            average_precision = precision/len(fixed_files)
            # print("average_precision" ,average_precision, len(fixed_files))
            total_average_precision = total_average_precision + average_precision
            
        mean_average_precision = total_average_precision/total_bug
        print("MAP@", top, mean_average_precision, total_bug)

def main(root):
    # Find all combined_locs.jsonl under results/file_level_combined/<project>/
    pattern = os.path.join(root, "results3", "file_level_combined", "*", "combined_locs.jsonl")
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
    
    print(f"Processed {len(all_bug_data)}")

    calculate_accuracy_at_k(all_bug_data)
    calculate_mean_reciprocal_rank_at_k(all_bug_data)
    calculate_mean_average_precision_at_k(all_bug_data)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extract found_files per instance_id per project.")
    ap.add_argument("--root", default=".", help="Repo root (default: current dir)")
    args = ap.parse_args()
    main(args.root)
