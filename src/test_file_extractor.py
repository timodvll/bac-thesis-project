import os
import re

def contains_test(s: str):
    return re.match(r'^(test.*|.*test)$', s, re.IGNORECASE)

def is_python_file(filename: str):
    return filename.endswith('.py')

def collect_folder_flat(src_folder, collected_files, project_name):
    for root, _, files in os.walk(src_folder):
        for file in files:
            if is_python_file(file):
                src_path = os.path.join(root, file)
                collected_files.append((project_name, file, src_path))

def traverse_and_collect_project(project_path: str):
    collected_files = []
    collected_test_folders = set()
    project_name = os.path.basename(project_path)

    for root, dirs, files in os.walk(project_path):
        for folder in dirs:
            if contains_test(folder):
                folder_path = os.path.join(root, folder)
                if folder_path not in collected_test_folders:
                    collect_folder_flat(folder_path, collected_files, project_name)
                    collected_test_folders.add(folder_path)

        for file in files:
            src_path = os.path.join(root, file)

            if any(src_path.startswith(folder) for folder in collected_test_folders):
                continue

            if contains_test(file) and is_python_file(file):
                collected_files.append((project_name, file, src_path))

    return collected_files

def scan_all_projects(projects_directory: str):
    all_collected_files = []

    for item in os.listdir(projects_directory):
        project_path = os.path.join(projects_directory, item)
        if os.path.isdir(project_path):
            project_files = traverse_and_collect_project(project_path)
            all_collected_files.extend(project_files)

    return all_collected_files