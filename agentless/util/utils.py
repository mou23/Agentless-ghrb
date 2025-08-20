import json
import logging
import os
import xml.etree.ElementTree as ET
from typing import List, Dict
import re
import html

def load_jsonl(filepath):
    """
    Load a JSONL file from the given filepath.

    Arguments:
    filepath -- the path to the JSONL file to load

    Returns:
    A list of dictionaries representing the data in each line of the JSONL file.
    """
    with open(filepath, "r") as file:
        return [json.loads(line) for line in file]


def write_jsonl(data, filepath):
    """
    Write data to a JSONL file at the given filepath.

    Arguments:
    data -- a list of dictionaries to write to the JSONL file
    filepath -- the path to the JSONL file to write
    """
    with open(filepath, "w") as file:
        for entry in data:
            file.write(json.dumps(entry) + "\n")


def load_json(filepath):
    return json.load(open(filepath, "r"))


def combine_by_instance_id(data):
    """
    Combine data entries by their instance ID.

    Arguments:
    data -- a list of dictionaries with instance IDs and other information

    Returns:
    A list of combined dictionaries by instance ID with all associated data.
    """
    combined_data = defaultdict(lambda: defaultdict(list))
    for item in data:
        instance_id = item.get("instance_id")
        if not instance_id:
            continue
        for key, value in item.items():
            if key != "instance_id":
                combined_data[instance_id][key].extend(
                    value if isinstance(value, list) else [value]
                )
    return [
        {**{"instance_id": iid}, **details} for iid, details in combined_data.items()
    ]


def setup_logger(log_file):
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    return logger


def cleanup_logger(logger):
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()


def load_existing_instance_ids(output_file):
    instance_ids = set()
    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    instance_ids.add(data["instance_id"])
                except json.JSONDecodeError:
                    continue
    return instance_ids


def _clean_text(text: str) -> str:
    if text is None:
        return ""
    # Replace Unicode escape sequences with actual characters
    text = re.sub(r'\\u([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), text)
    # Unescape HTML entities (if present)
    text = html.unescape(text)
    # Strip leading/trailing spaces
    return text.strip()

def load_yeetal_dataset(project_name: str) -> List[Dict]:
    xml_file = f"dataset/{project_name}-merged.xml"
    with open(xml_file, 'r', encoding="utf-8", errors='replace') as file:
        data = file.read()
        xml_data = ET.fromstring(data)

    json_data_list = []

    for table in xml_data.findall(".//table"):
        bug_id = table.find(".//column[@name='bug_id']")
        summary = table.find(".//column[@name='summary']")
        description = table.find(".//column[@name='description']")
        buggy_commit = table.find(".//column[@name='buggy_commit']")
        buggy_commit_time = table.find(".//column[@name='buggy_commit_time']")
        fixed_commit_timestamp = table.find(".//column[@name='fixed_commit_timestamp']")

        bug_id = _clean_text(bug_id.text if bug_id is not None else "")
        summary = _clean_text(summary.text if summary is not None else "")
        description = _clean_text(description.text if description is not None else "")
        buggy_commit = _clean_text(buggy_commit.text if buggy_commit is not None else "")

        issue = {
            "instance_id": bug_id,
            "problem_statement": summary + "\n" + description,
            "repo": project_name,
            "base_commit": buggy_commit,
            "buggy_commit_time": buggy_commit_time.text if buggy_commit_time is not None else "",
            "fixed_commit_time": fixed_commit_timestamp.text if fixed_commit_timestamp is not None else "",
        }

        json_data_list.append(issue)

    json_data_list = sorted(json_data_list, key=lambda d: d['fixed_commit_time'])
    split_index = len(json_data_list) - int(len(json_data_list)*0.4)
    json_data_list = json_data_list[split_index:]
    json_data_list = sorted(json_data_list, key=lambda d: d['buggy_commit_time'])

    return json_data_list




#need to change
def load_ghrb_dataset(project_name, repo_location) -> List[Dict]:
    xml_file = f"{repo_location}/{project_name}.xml"
    with open(xml_file, 'r', encoding="utf-8", errors='replace') as file:
        data = file.read()
        xml_data = ET.fromstring(data)

    json_data_list = []

    for table in xml_data.findall(".//table"):
        bug_id = table.find(".//column[@name='bug_id']")
        summary = table.find(".//column[@name='summary']")
        description = table.find(".//column[@name='description']")
        buggy_commit = table.find(".//column[@name='commit']")
        

        bug_id = _clean_text(bug_id.text if bug_id is not None else "")
        summary = _clean_text(summary.text if summary is not None else "")
        description = _clean_text(description.text if description is not None else "")
        buggy_commit = _clean_text(buggy_commit.text if buggy_commit is not None else "")

        issue = {
            "instance_id": bug_id,
            "problem_statement": summary + "\n" + description,
            "repo": f"{repo_location}/{project_name}",
            "base_commit": buggy_commit,
        }

        json_data_list.append(issue)

    return json_data_list