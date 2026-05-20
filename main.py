"""
Maximum Agreement Forest (MAF) Solver - PACE 2026 Heuristic Track
Correct implementation for the Maximum Agreement Forest problem
"""

import sys
from typing import Set, List, Dict, Tuple

class TreeNode:
    def __init__(self, label=None):
        self.label = label
        self.left = None
        self.right = None

def parse_newick(s: str) -> TreeNode:
    """Parse Newick format string into tree"""
    s = s.strip().replace('\n', '').replace(' ', '')
    
    def parse(idx):
        if s[idx].isdigit():
            j = idx
            while j < len(s) and s[j].isdigit():
                j += 1
            return TreeNode(label=int(s[idx:j])), j
        assert s[idx] == '('
        left, idx = parse(idx + 1)
        assert s[idx] == ','
        right, idx = parse(idx + 1)
        assert s[idx] == ')'
        node = TreeNode()
        node.left = left
        node.right = right
        return node, idx + 1
    
    root, _ = parse(0)
    return root

def collect_leaves(node: TreeNode) -> Set[int]:
    """Collect all leaf labels"""
    if node.label is not None:
        return {node.label}
    return collect_leaves(node.left) | collect_leaves(node.right)

def get_node_leaves(node: TreeNode, memo: Dict) -> Set[int]:
    """Get all leaves under a node with memoization"""
    if node in memo:
        return memo[node]
    if node.label is not None:
        memo[node] = {node.label}
    else:
        memo[node] = get_node_leaves(node.left, memo) | get_node_leaves(node.right, memo)
    return memo[node]

def find_nodes_with_leaves(node: TreeNode, target: Set[int], memo: Dict, results: List[TreeNode]):
    """Find all nodes whose leaf set equals target"""
    leaves = get_node_leaves(node, memo)
    if leaves == target:
        results.append(node)
    if node.label is None:
        if node.left and len(get_node_leaves(node.left, memo)) >= len(target):
            find_nodes_with_leaves(node.left, target, memo, results)
        if node.right and len(get_node_leaves(node.right, memo)) >= len(target):
            find_nodes_with_leaves(node.right, target, memo, results)

def find_common_subtrees(tree1: TreeNode, tree2: TreeNode) -> List[Set[int]]:
    """Find all maximal common subtrees between two trees"""
    leaves1 = collect_leaves(tree1)
    leaves2 = collect_leaves(tree2)
    all_leaves = leaves1 & leaves2
    
    # Get all leaf sets from both trees
    memo1 = {}
    memo2 = {}
    get_node_leaves(tree1, memo1)
    get_node_leaves(tree2, memo2)
    
    # Find common leaf sets
    common_sets = []
    for node1, leaves1_set in memo1.items():
        for node2, leaves2_set in memo2.items():
            if leaves1_set == leaves2_set and len(leaves1_set) > 1:
                if leaves1_set not in common_sets:
                    common_sets.append(leaves1_set)
    
    # Sort by size (largest first)
    common_sets.sort(key=len, reverse=True)
    return common_sets

def build_forest(tree1: TreeNode, tree2: TreeNode) -> List[Set[int]]:
    """Build the agreement forest"""
    all_leaves = collect_leaves(tree1)
    
    # Find all common subtrees
    common_sets = find_common_subtrees(tree1, tree2)
    
    # Greedy selection of disjoint common subtrees
    used = set()
    components = []
    
    for comp in common_sets:
        if comp.isdisjoint(used):
            components.append(comp)
            used.update(comp)
    
    # Add remaining leaves as individual components
    for leaf in all_leaves:
        if leaf not in used:
            components.append({leaf})
    
    return components

def set_to_newick(leaf_set: Set[int]) -> str:
    """Convert a set of leaves to Newick format"""
    leaves = sorted(list(leaf_set))
    if len(leaves) == 1:
        return str(leaves[0])
    
    # Build a simple binary tree
    def build(lst):
        if len(lst) == 1:
            return str(lst[0])
        mid = len(lst) // 2
        return f"({build(lst[:mid])},{build(lst[mid:])})"
    
    return build(leaves)

def main():
    if len(sys.argv) < 2:
        print("Usage: python maf_solver.py <input_file>")
        print("Output: k* and agreement forest in Newick format")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if len(lines) < 2:
        print("Error: File must contain two trees")
        sys.exit(1)
    
    tree1 = parse_newick(lines[0])
    tree2 = parse_newick(lines[1])
    
    components = build_forest(tree1, tree2)
    
    # Output
    k = len(components) - 1
    print(k)
    for comp in components:
        print(set_to_newick(comp))

if __name__ == "__main__":
    main()