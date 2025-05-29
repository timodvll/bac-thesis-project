import ast
import helper_functions as h


#checks the body of the test case for any patterns
#strictness can be 1: Low, 2: Medium, 3: High 
def check_body(func_node, strictness):
    result = []
    line_no = func_node.lineno

    def add_unique(val):
        if val not in result:
            result.append(val)

    for node in ast.walk(func_node):
        if isinstance(node, ast.Assert):
            continue #skip assertions as they are checked later on.

        #match any range(...) call
        if strictness == 1: #low
            if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'range':
                add_unique(1)

        #match any st.<...>(min_value=..., max_value=...)
        if strictness == 1 or strictness == 2: #low and medium
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if getattr(node.func.value, 'id', '') == 'st':
                    kwarg_names = {kw.arg for kw in node.keywords}
                    if 'min_value' in kwarg_names and 'max_value' in kwarg_names:
                        add_unique(1)

        #assume(min < x < max)
        if strictness == 1: #low
            if isinstance(node, ast.Call) and getattr(node.func, 'id', '') == 'assume':
                if node.args and isinstance(node.args[0], ast.Compare):
                    add_unique(1)


        #lexical checks
        if strictness == 1: #low
            if isinstance(node, ast.Name) and node.id in {'encode', 'decode'}:
                add_unique(3)
            elif isinstance(node, ast.Str) and any(kw in node.s for kw in ['encode', 'decode']):
                add_unique(3)

            if isinstance(node, ast.Name) and node.id in {'from', 'to'}:
                add_unique(3)
            elif isinstance(node, ast.Str) and any(kw in node.s for kw in ['from', 'to']):
                add_unique(3)

            if isinstance(node, ast.Name) and node.id in {'merge', 'combine'}:
                add_unique(6)
            elif isinstance(node, ast.Str) and any(kw in node.s for kw in ['merge', 'combine']):
                add_unique(6)

            if isinstance(node, ast.Name) and node.id in {'is_valid', 'verify', 'is_true', 'is_false'}:
                add_unique(7)

            if isinstance(node, ast.Name) and any(sub in node.id for sub in ['ref', 'reference', 'my']):
                add_unique(8)
            elif isinstance(node, ast.Str) and any(sub in node.s for sub in ['ref', 'reference', 'my']):
                add_unique(8)

            if isinstance(node, ast.Name) and 'model' in node.id:
                add_unique(9)
            elif isinstance(node, ast.Str) and 'model' in node.s:
                add_unique(9)

    if strictness == 4: #classification is off
        result = []
    return [line_no] + list(result)


def check_assertions(func_node, strictness):

    results = []

    def add_unique(val):
        if val not in detected_categories:
            detected_categories.append(val)
    
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assert):
            line_no = node.lineno
            detected_categories = []
            test = node.test

            # assert x < a < y
            if isinstance(test, ast.Compare):
                ops = test.ops
                if len(ops) == 2:
                    if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                        op1, op2 = ops
                        valid_ops = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)
                        if isinstance(op1, valid_ops) and isinstance(op2, valid_ops):
                            is_less = isinstance(op1, (ast.Lt, ast.LtE)) and isinstance(op2, (ast.Lt, ast.LtE))    # x < a < y
                            is_greater = isinstance(op1, (ast.Gt, ast.GtE)) and isinstance(op2, (ast.Gt, ast.GtE)) # x > a > y
                            if is_less or is_greater:
                                add_unique(1) 
                elif len(ops) == 1: #check for only one operation
                    if strictness == 1 or strictness == 2: #low and medium
                        op = ops[0]
                        if isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)): # test for <, >, <=, >=
                            add_unique(1)  # x < a or x > a
            
            # assert f(a, b, ...) == f(..., b, a)  (order of arguments is arbitrary, but the actual arguments are the same)
            if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    left, right = test.left, test.comparators[0]
                    if isinstance(left, ast.Call) and isinstance(right, ast.Call): #check for both functions
                        if h.is_same_func(left.func, right.func): #chck if f's are equal
                            if h.args_are_same_but_reordered(left.args, right.args): #check if f's arguments are the same but in different orders
                                add_unique(2)

            #assert f(x) == g(x)
            if strictness == 1 or strictness == 2: #low and medium
                if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    left, right = test.left, test.comparators[0]
                    if isinstance(left, ast.Call) and isinstance(right, ast.Call): #check for f and g
                        if not h.is_same_func(left.func, right.func): #check if f != g
                            if len(left.args) == len(right.args) == 1:
                                if ast.dump(left.args[0]) == ast.dump(right.args[0]): #check if x's are equal
                                    add_unique(2)

            #assert f(g(x)) == x
            if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    left, right = test.left, test.comparators[0]
                    if (isinstance(left, ast.Call) and len(left.args) == 1 and #check for f
                        isinstance(left.args[0], ast.Call) and len(left.args[0].args) == 1): #check for g
                        if not h.functions_equal(left.func, left.args[0].func): #check if f != g
                            x = left.args[0].args[0]
                            if ast.dump(x) == ast.dump(right): #check if x's are equal
                                add_unique(3)

            # assert f(x) == x
            if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                if (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
                    left, right = test.left, test.comparators[0]
                    if isinstance(left, ast.Call) and len(left.args) == 1: #check if left is a function f
                        if ast.dump(left.args[0]) == ast.dump(right): #check if x's are equal
                            add_unique(4)

            # assert(isinstance(x, SomeType)) (lexical)
            if strictness == 1: #low
                if (isinstance(test, ast.Call) and
                    isinstance(test.func, ast.Name) and test.func.id == 'isinstance' and #check for syntax
                    len(test.args) == 2):
                        add_unique(4)

            #assert f(f(x)) == f(x) and assert(f(g(x) == f(x))
            if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                left, right = test.left, test.comparators[0]
                if isinstance(left, ast.Call) and isinstance(right, ast.Call):
                    if h.is_same_func(left.func, right.func): #check f == f
                        if len(left.args) == 1 and isinstance(left.args[0], ast.Call):
                            inner_call = left.args[0]
                            if h.is_same_func(inner_call.func, left.func): #check if inner f == f (category 5)
                                if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                                    if len(inner_call.args) == 1 and len(right.args) == 1:
                                        if ast.dump(inner_call.args[0]) == ast.dump(right.args[0]): #check if x == x
                                            add_unique(5)
                            if not h.is_same_func(inner_call.func, left.func): #check if inner f != f (category 4)
                                if strictness == 1 or strictness == 2: #low and medium
                                    if len(inner_call.args) == 1 and len(right.args) == 1:
                                        if ast.dump(inner_call.args[0]) == ast.dump(right.args[0]): #check if x == x
                                            add_unique(4)
            
            # assert(f(x + c) >= f(x)) or assert(f(x - c) <= f(x)) (or any operation: x op c)
            if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                if (isinstance(test, ast.Compare) and len(test.ops) == 1 and
                    isinstance(test.ops[0], (ast.GtE, ast.LtE, ast.Gt, ast.Lt))):

                    left, right = test.left, test.comparators[0]

                    if (isinstance(left, ast.Call) and isinstance(right, ast.Call) and
                        h.functions_equal(left.func, right.func) and
                        len(left.args) == 1 and len(right.args) == 1):

                        arg_left = left.args[0]
                        arg_right = right.args[0]

                        if (isinstance(arg_left, ast.BinOp) and #check operation: x op c
                            (isinstance(arg_left.op, (ast.Add, ast.Sub, ast.Mult, ast.Div))) and
                            (ast.dump(arg_right) == ast.dump(arg_left.left) or ast.dump(arg_right) == ast.dump(arg_left.right)) and #check if x's are equal
                            (isinstance(arg_left.left, ast.Constant) or isinstance(arg_left.right, ast.Constant))): #check for constant c
                                add_unique(10)

            #assert(f(c op x) == c op f(x))
            if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                if (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
                    left, right = test.left, test.comparators[0]

                    if (isinstance(left, ast.Call) and len(left.args) == 1 and
                        isinstance(left.args[0], ast.BinOp)): #left side: f(c op x) or f(x op c)
                        left_arg = left.args[0]
                        op_left = type(left_arg.op)

                        if isinstance(right, ast.BinOp): #right side: c op f(x) or f(x) op c

                            op_right = type(right.op)
                            if op_left == op_right: #check if op's are equal
                                right_left, right_right = right.left, right.right

                                fx_node = None #check which side is f and which is c
                                if h.is_fx(right_left, left_arg):
                                    fx_node = right_left
                                    const_node = right_right
                                elif h.is_fx(right_right, left_arg):
                                    fx_node = right_right
                                    const_node = right_left

                                if fx_node is not None:
                                    if h.functions_equal(left.func, fx_node.func): #check if f's are equal
                                        const_left = h.get_const(left_arg.left) or h.get_const(left_arg.right)
                                        const_right = h.get_const(const_node)

                                        if const_left is not None and const_right is not None and const_left == const_right: #check if c's are equal
                                                add_unique(10)
            
            #assert(f(x op y) == f(x) op f(y))
            if strictness == 1 or strictness == 2 or strictness == 3: #low, medium and high
                if (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
                    left, right = test.left, test.comparators[0]

                    if (isinstance(left, ast.Call) and len(left.args) == 1 and
                        isinstance(left.args[0], ast.BinOp)): #left side: f(x op y)
                        binop = left.args[0]
                        op_type = type(binop.op)

                        if (isinstance(right, ast.BinOp) and isinstance(right.op, op_type) and
                            all(isinstance(side, ast.Call) and len(side.args) == 1 for side in [right.left, right.right])): #right side: f(x) op f(y)

                            if (h.functions_equal(left.func, right.left.func) and 
                                h.functions_equal(left.func, right.right.func)): #check if f's are equal

                                args_match = (
                                    (ast.dump(right.left.args[0]) == ast.dump(binop.left) and
                                    ast.dump(right.right.args[0]) == ast.dump(binop.right)) or
                                    (ast.dump(right.left.args[0]) == ast.dump(binop.right) and
                                    ast.dump(right.right.args[0]) == ast.dump(binop.left))
                                ) #check if x's and y's are equal

                                if args_match:
                                    add_unique(10)
                                    
            if strictness == 4: #classification is off
                detected_categories = []
            results.append([line_no] + detected_categories)
                
    return list(results)

def analyse_test_case(strictness, log_file_path, func_node, file_name, project_name, file_path):
    body_result = check_body(func_node, strictness)
    assertion_results = check_assertions(func_node, strictness)
    function_name = func_node.name
    h.log_csv(body_result, log_file_path, file_path, project_name, file_name, function_name, "Body")

    for assertion in assertion_results:
        h.log_csv(assertion, log_file_path, file_path, project_name, file_name, function_name, "Assertion")
    

