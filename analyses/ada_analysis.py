import sys
import os
import tree_sitter_ada
from tree_sitter import Language, Parser

def calculate_sloc(code_str):
    """Calculates SLOC by ignoring empty lines and full-line comments."""
    lines = code_str.splitlines()
    sloc = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('--'):
            sloc += 1
    return sloc

def count_tokens(node):
    """Counts leaf nodes in the AST as tokens, ignoring comments."""
    if len(node.children) == 0:
        if node.type == 'comment':
            return 0
        return 1
    return sum(count_tokens(child) for child in node.children)

def calculate_ccn(node):
    """
    Calculates Cyclomatic Complexity by traversing a subprogram's AST.
    Base complexity is 1. Adds 1 for every branching statement.
    """
    complexity = 1

    # Common Tree-sitter Ada node types that introduce control flow branches
    branching_nodes = {
        'if_statement',
        'elsif_clause',
        'case_statement_alternative',
        'loop_statement',
        'while_loop_statement',
        'for_loop_statement',
        'short_circuit_operation' # e.g., 'and then', 'or else'
    }

    def traverse(n):
        nonlocal complexity
        if n.type in branching_nodes:
            complexity += 1
        for child in n.children:
            traverse(child)

    traverse(node)
    return complexity

def get_subprograms(node):
    """Recursively finds all subprogram bodies in the AST."""
    subprograms = []
    # In Ada, functions and procedures are typically wrapped in subprogram_body
    if node.type in ('subprogram_body', 'function_body', 'procedure_body'):
        subprograms.append(node)
    else:
        for child in node.children:
            subprograms.extend(get_subprograms(child))
    return subprograms

def main():
    if len(sys.argv) < 2:
        print("Usage: python ada_analysis.py <file1.adb> <file2.ads> ...")
        sys.exit(1)

    # Initialize Tree-sitter parser for Ada
    ada_language = Language(tree_sitter_ada.language())
    parser = Parser(ada_language)

    total_sloc = 0
    total_tokens = 0
    total_ccn = 0
    total_functions = 0

    for filepath in sys.argv[1:]:
        if not os.path.isfile(filepath):
            print(f"Error: File '{filepath}' not found.")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            code_str = f.read()

        # Generate AST
        tree = parser.parse(bytes(code_str, 'utf8'))
        root_node = tree.root_node

        # Metrics for the current file
        sloc = calculate_sloc(code_str)
        tokens = count_tokens(root_node)
        subprograms = get_subprograms(root_node)

        total_sloc += sloc
        total_tokens += tokens

        print(f"File: {filepath}")
        print(f"  SLOC: {sloc}")
        print(f"  Tokens: {tokens}")

        for sp_node in subprograms:
            ccn = calculate_ccn(sp_node)
            total_ccn += ccn
            total_functions += 1
            # Using start_point[0] + 1 to get the 1-indexed line number of the function
            print(f"  - Subprogram starting at line {sp_node.start_point[0] + 1}: CCN = {ccn}")

        print("-" * 40)

    # Final summary statistics
    print("\n=== Overall Summary ===")
    print(f"Total Files Analyzed: {len(sys.argv[1:])}")
    print(f"Total SLOC: {total_sloc}")
    print(f"Total Tokens: {total_tokens}")
    print(f"Total Cyclomatic Complexity (CCN): {total_ccn}")

    if total_functions > 0:
        avg_ccn = total_ccn / total_functions
        print(f"Total Subprograms: {total_functions}")
        print(f"Average CCN per Subprogram: {avg_ccn:.2f}")
    else:
        print("Average CCN per Subprogram: N/A (No subprograms detected)")

if __name__ == "__main__":
    main()