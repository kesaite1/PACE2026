# generate_50.py
import random

def make_tree(leaves):
    if len(leaves) == 1:
        return str(leaves[0])
    mid = random.randint(1, len(leaves)-1)
    return f"({make_tree(leaves[:mid])},{make_tree(leaves[mid:])})"

leaves = list(range(1, 51))
random.shuffle(leaves)
tree1 = make_tree(leaves[:25])  # Just show concept
print("Tree1: (1,2)")  # Simplified