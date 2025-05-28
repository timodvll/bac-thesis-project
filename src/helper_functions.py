import ast
import csv
import os


def is_same_func(func1, func2):
    if type(func1) != type(func2):
        return False
    if isinstance(func1, ast.Name):
        return func1.id == func2.id
    if isinstance(func1, ast.Attribute):
        return func1.attr == func2.attr and is_same_func(func1.value, func2.value)
    return False

def args_are_same_but_reordered(args1, args2):
    if len(args1) != len(args2):
        return False
    dumps1 = [ast.dump(arg) for arg in args1]
    dumps2 = [ast.dump(arg) for arg in args2]
    return sorted(dumps1) == sorted(dumps2) and dumps1 != dumps2

def is_fx(node, left_arg):
    return (isinstance(node, ast.Call) and
        len(node.args) == 1 and
        ast.dump(node.args[0]) == ast.dump(left_arg.left) or
        ast.dump(node.args[0]) == ast.dump(left_arg.right))
def get_const(node):
    if isinstance(node, (ast.Constant, ast.Num)):
        return node.value if hasattr(node, 'value') else node.n
    return None

def create_csv_file(filepath):
    if not os.path.exists(filepath):
        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["File Path", "Project Name", "File Name", "Function Name", "Log Type", "Line Number", "Classification" ]) #header

    
def log_csv(log, log_file_path, file_path, project_name, file_name, function_name, log_type):
    line_no = log[0]
    classification = log[1:]
    if not os.path.exists(log_file_path):
        create_csv_file(log_file_path)
    
    with open(log_file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([file_path, 
                        project_name,
                        file_name,
                        function_name, 
                        log_type, 
                        line_no, 
                        classification])
