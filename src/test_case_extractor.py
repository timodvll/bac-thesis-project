import ast
import classification_functions as cf

def is_hypothesis_test(func_node):
    if not isinstance(func_node, ast.FunctionDef):
        return False

    for decorator in func_node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "given":
            return True
        elif isinstance(decorator, ast.Attribute) and decorator.attr == "given":
            return True
        elif isinstance(decorator, ast.Call) and (
            (isinstance(decorator.func, ast.Name) and decorator.func.id == "given") or
            (isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "given")
        ):
            return True
    return False

def has_hypothesis_import(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("hypothesis"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("hypothesis"):
                return True
    return False


def extract_full_function_source(file_path, func_node):
    
    source_lines = open(file_path, "r", encoding="utf-8").readlines()

    start_line = func_node.lineno - 1
    if func_node.decorator_list:
        start_line = func_node.decorator_list[0].lineno - 1 
    
    end_line = func_node.end_lineno
    return "".join(source_lines[start_line:end_line])  


def find_hypothesis_tests(file_path):
    source_code = open(file_path, "r", encoding="utf-8").read()
    tree = ast.parse(source_code, filename=file_path)

    if not has_hypothesis_import(tree):
        return []

    tests = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and is_hypothesis_test(node):
            tests.append(node)

    return tests