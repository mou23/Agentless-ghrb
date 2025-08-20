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


def create_structure(directory_path):
    """Create the structure of the repository directory by parsing Java files.
    :param directory_path: Path to the repository directory.
    :return: A dictionary representing the structure.
    """
    structure = {}

    for root, _, files in os.walk(directory_path):
        repo_name = os.path.basename(directory_path)
        relative_root = os.path.relpath(root, directory_path)
        if relative_root == ".":
            relative_root = repo_name
        curr_struct = structure
        for part in relative_root.split(os.sep):
            if part not in curr_struct:
                curr_struct[part] = {}
            curr_struct = curr_struct[part]
        for file_name in files:
            if file_name.endswith(".java"):
                file_path = os.path.join(root, file_name)
                class_info, function_names, file_lines = parse_java_file(file_path)
                curr_struct[file_name] = {
                    "classes": class_info,
                    "functions": function_names,
                    "text": file_lines,
                }
            # else:
            #     curr_struct[file_name] = {}

    return structure
