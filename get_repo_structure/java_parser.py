import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
import os
from datetime import datetime

def initialize_parser():
    parser = Parser()
    JAVA_LANGUAGE = Language(tsjava.language(), 'java')
    parser.set_language(JAVA_LANGUAGE)
    return parser

def extract_node_text(node, field_name, default):
    field_node = node.child_by_field_name(field_name)
    return field_node.text.decode('utf-8') if field_node else default


def get_method_body(method_declaration_node):
    return method_declaration_node.text.decode('utf-8')


def extract_class_and_method_info(file_content, node, class_info=None):
    try:
        if class_info is None:
            class_info = []

        if node.type == 'class_declaration':            
            class_name = extract_node_text(node, 'name', '')
            start_line, start_column = node.start_point
            end_line, end_column = node.end_point

            methods = []
            body_node = node.child_by_field_name('body')

            if body_node:
                for body_child in body_node.named_children:
                    if body_child.type == 'method_declaration' or body_child.type == 'constructor_declaration':
                        method_name = extract_node_text(body_child, 'name', '')
                        method_start, method_column = body_child.start_point
                        method_end, method_end_column = body_child.end_point
                        methods.append(
                        {
                            "name": method_name,
                            "start_line": method_start+1,
                            "end_line": method_end+1,
                            "text": file_content.splitlines()[
                                method_start : method_end+1
                            ],
                        }
                    )
            
            class_info.append(
                {
                    "name": class_name,
                    "start_line": start_line + 1,
                    "end_line": end_line + 1,
                    "text": file_content.splitlines()[
                        start_line : end_line+1
                    ],
                    "methods": methods,
                }
            )
        for child in node.children:
            extract_class_and_method_info(file_content, child, class_info)

        return class_info, file_content.splitlines()
    
    except Exception as e:
        print(f'Error: {e}')
        return class_info, file_content.splitlines()

def extract_node_text(node, field_name, default):
    field_node = node.child_by_field_name(field_name)
    return field_node.text.decode('utf-8') if field_node else default

if __name__ == '__main__':
    def process_files(repo_path):
        global list_of_files, list_of_ids
        initialize_parser()
        for root, dirs, files in os.walk(repo_path):
            relative_root = os.path.relpath(root, repo_path)
            for file in files:
                if file.endswith(".java"):
                    file_path = os.path.join(relative_root, file)
                    file_path = file_path.replace("\\", "/")
                    print(parse_java_file(repo_path+file_path))
                    print('*****************************************')

    start_time = datetime.now()

    git_repo = 'D:/FL/extra code/'
    process_files(git_repo)