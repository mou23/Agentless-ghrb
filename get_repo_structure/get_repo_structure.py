import argparse
import ast
import json
import os
import subprocess
import uuid

import pandas as pd
from tqdm import tqdm
from get_repo_structure.java_parser import initialize_parser, extract_class_and_method_info

repo_to_top_folder = {
    "django/django": "django",
    "sphinx-doc/sphinx": "sphinx",
    "scikit-learn/scikit-learn": "scikit-learn",
    "sympy/sympy": "sympy",
    "pytest-dev/pytest": "pytest",
    "matplotlib/matplotlib": "matplotlib",
    "astropy/astropy": "astropy",
    "pydata/xarray": "xarray",
    "mwaskom/seaborn": "seaborn",
    "psf/requests": "requests",
    "pylint-dev/pylint": "pylint",
    "pallets/flask": "flask",
}


def checkout_commit(repo_path, commit_id):
    """Checkout the specified commit in the given local git repository.
    :param repo_path: Path to the local git repository
    :param commit_id: Commit ID to checkout
    :return: None
    """
    try:
        # Change directory to the provided repository path and checkout the specified commit
        print(f"Checking out commit {commit_id} in repository at {repo_path}...")
        subprocess.run(["git", "-C", repo_path, "checkout", commit_id], check=True)
        print("Commit checked out successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running git command: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def get_project_structure_from_scratch(
    repo, commit_id, instance_id, repo_playground
):
    repo_path = repo
    checkout_commit(repo_path, commit_id)
    structure = create_structure(repo_path)
    d = {
        "repo": repo,
        "base_commit": commit_id,
        "structure": structure,
        "instance_id": instance_id,
    }
    return d


def parse_java_file(file_path, file_content=None):
    """Parse a Java file to extract class and method definitions with their line numbers.
    :param file_path: Path to the Java file.
    :return: Class names, method names, and file contents
    """
    parser = initialize_parser()

    if file_content is None:
        try:
            # print(f"parsing {file_path}")
            with open((file_path), encoding="utf8", errors="ignore") as file:
                file_content = file.read()
                tree = parser.parse(bytes(file_content, "utf8"))
                root_node = tree.root_node
                class_info, file_lines = extract_class_and_method_info(file_content, root_node)
                return class_info, [], file_lines
        except Exception as e:  # Catch all types of exceptions
            print(f"Error in file {file_path}: {e}")
            return [], [], ""
    else:
        try:
            tree = parser.parse(bytes(file_content, "utf8"))
            root_node = tree.root_node
            class_info, file_lines = extract_class_and_method_info(file_content, root_node)
            return class_info, [], file_lines
        except Exception as e:
            print(f"Error in file {file_path}: {e}")
            return [], [], ""


def create_structure(directory_path, *, store_text=True, max_file_bytes=2_000_000):
    """
    Build a nested dict of the repo.
    - store_text=False: do not store file contents (prevents OOM).
    - max_file_bytes: skip parsing files larger than this size (None to disable).
    """
    structure = {}
    repo_name = os.path.basename(os.path.abspath(directory_path))
    total_dirs = total_files = parsed_java = skipped_large = parse_errors = 0

    for root, _, files in os.walk(directory_path, followlinks=False):
        # Build nested dict for this directory
        relative_root = os.path.relpath(root, directory_path)
        if relative_root == ".":
            relative_root = repo_name

        curr_struct = structure
        for part in relative_root.split(os.sep):
            if part not in curr_struct:
                curr_struct[part] = {}
            curr_struct = curr_struct[part]

        total_dirs += 1

        for file_name in files:
            # Always show where we are; flush so we see the last successful step if we hang/crash
            # print("file_name", file_name, "in", relative_root, flush=True)

            file_path = os.path.join(root, file_name)
            total_files += 1

            if file_name.endswith(".java"):
                # Optional: skip very large files to avoid parser hangs / memory spikes
                try:
                    if max_file_bytes is not None:
                        try:
                            if os.path.getsize(file_path) > max_file_bytes:
                                skipped_large += 1
                                curr_struct[file_name] = {"classes": [], "functions": []}
                                print(f"  skipped large file (> {max_file_bytes} bytes)", flush=True)
                                continue
                        except OSError:
                            # If stat fails, just attempt to parse
                            pass

                    # Parse with error guard
                    try:
                        class_info, function_names, file_lines = parse_java_file(file_path)
                        entry = {
                            "classes": class_info or [],
                            "functions": function_names or [],
                        }
                        if store_text:
                            entry["text"] = file_lines or []
                        curr_struct[file_name] = entry
                        parsed_java += 1
                        # print("  keys", list(curr_struct.keys()), flush=True)
                    except Exception as e:
                        parse_errors += 1
                        curr_struct[file_name] = {"classes": [], "functions": []}
                        print(f"  parse error: {e}", flush=True)
                except Exception as outer_e:
                    # Any unexpected error for this file shouldn't stop the whole walk
                    parse_errors += 1
                    curr_struct[file_name] = {"classes": [], "functions": []}
                    print(f"  unexpected error: {outer_e}", flush=True)
            # else:
            #     curr_struct[file_name] = {}

    print(
        f"structure ready | dirs={total_dirs}, files={total_files}, "
        f"parsed_java={parsed_java}, skipped_large={skipped_large}, parse_errors={parse_errors}",
        flush=True
    )
    return structure
