#!/usr/bin/env python3


import sys
import signal
import random
from typing import List, Tuple

POP_SIZE = 40
DEBUG = False

Graph = List[List[int]]


def read_gr_file(stream) -> Graph:
    adj: Graph = []
    for line in stream:
        line = line.strip()
        if not line or line[0] == 'c':
            continue
        if line[0] == 'p':
            # p <fmt> <n> <m>
            parts = line.split()
            n = int(parts[2])
            adj = [[] for _ in range(n)]
        else:
            u_str, v_str = line.split()[:2]
            u, v = int(u_str), int(v_str)
            adj[u - 1].append(v - 1)
            adj[v - 1].append(u - 1)
    return adj


def get_uncovered_vertices(adj: Graph, dom_set: List[bool]) -> List[int]:
    n = len(adj)
    covered = [False] * n
    for u in range(n):
        if dom_set[u]:
            covered[u] = True
            for v in adj[u]:
                covered[v] = True
    return [u for u in range(n) if not covered[u]]


class Individual:
    __slots__ = ("dom_set", "fitness")

    def __init__(self, dom_set=None, fitness: int = 0):
        self.dom_set: List[bool] = dom_set if dom_set is not None else []
        self.fitness: int = fitness

    def copy(self) -> "Individual":
        return Individual(self.dom_set.copy(), self.fitness)


def update_fitness(ind: Individual) -> None:
    ind.fitness = sum(ind.dom_set)  # bools sum like ints


def tournament_select(pop: List[Individual], k: int = 2) -> Individual:
    best = None
    for _ in range(k):
        cand = pop[random.randrange(len(pop))]
        if best is None or cand.fitness < best.fitness:
            best = cand
    return best


def best_select_idx(pop: List[Individual]) -> int:
    return min(range(len(pop)), key=lambda i: pop[i].fitness)


def worst_select_idx(pop: List[Individual]) -> int:
    return max(range(len(pop)), key=lambda i: pop[i].fitness)


def greedy_random_repair(adj: Graph, dom_set: List[bool]) -> None:
    uncovered = get_uncovered_vertices(adj, dom_set)
    # index_map: vertex -> position in `uncovered`
    index_map = {v: i for i, v in enumerate(uncovered)}

    def remove_at(idx: int) -> None:
        last = uncovered[-1]
        v = uncovered[idx]
        uncovered[idx] = last
        index_map[last] = idx
        uncovered.pop()
        index_map.pop(v, None)

    while uncovered:
        idx = random.randrange(len(uncovered))
        new_v = uncovered[idx]
        dom_set[new_v] = True
        remove_at(idx)

        for neigh in adj[new_v]:
            if neigh in index_map:
                remove_at(index_map[neigh])


def greedy_priority_bucket_repair(adj: Graph, dom_set: List[bool]) -> None:
    n = len(adj)
    covered = [False] * n

    for v in range(n):
        if dom_set[v]:
            covered[v] = True
            for neigh in adj[v]:
                covered[neigh] = True

    max_deg = 0
    gain = [0] * n
    for v in range(n):
        if len(adj[v]) > max_deg:
            max_deg = len(adj[v])
        g = 1
        for neigh in adj[v]:
            if not covered[neigh]:
                g += 1
        gain[v] = g

    buckets: List[List[int]] = [[] for _ in range(max_deg + 2)]
    position: List[Tuple[int, int]] = [(0, 0)] * n

    for v in range(n):
        g = gain[v]
        buckets[g].append(v)
        position[v] = (g, len(buckets[g]) - 1)

    def remove_from_bucket(v: int) -> None:
        g, idx = position[v]
        bucket = buckets[g]
        last = bucket[-1]
        bucket[idx] = last
        position[last] = (g, idx)
        bucket.pop()

    def update_gain(v: int, new_gain: int) -> None:
        if gain[v] == new_gain:
            return
        remove_from_bucket(v)
        buckets[new_gain].append(v)
        position[v] = (new_gain, len(buckets[new_gain]) - 1)
        gain[v] = new_gain

    def get_max_gain_bucket() -> List[int]:
        for g in range(max_deg + 1, -1, -1):
            if buckets[g]:
                return buckets[g]
        raise RuntimeError("no bucket left")

    covered_count = sum(covered)
    while covered_count < n:
        bucket = get_max_gain_bucket()
        v = bucket[random.randrange(len(bucket))]
        remove_from_bucket(v)
        dom_set[v] = True

        if not covered[v]:
            covered[v] = True
            covered_count += 1

        for neigh in adj[v]:
            if not covered[neigh]:
                covered[neigh] = True
                covered_count += 1
                for w in adj[neigh]:
                    if not covered[w]:
                        update_gain(w, gain[w] - 1)

        for neigh in adj[v]:
            if not covered[neigh]:
                update_gain(neigh, gain[neigh] - 1)


def greedy_local_removal(adj: Graph, dom_set: List[bool]) -> None:
    n = len(dom_set)
    coverage = [0] * n

    for u in range(n):
        if dom_set[u]:
            coverage[u] += 1
            for v in adj[u]:
                coverage[v] += 1

    candidates = [u for u in range(n) if dom_set[u]]
    random.shuffle(candidates)

    for u in candidates:
        if coverage[u] <= 1:
            continue
        removable = True
        for v in adj[u]:
            if coverage[v] <= 1:
                removable = False
                break
        if removable:
            dom_set[u] = False
            coverage[u] -= 1
            for v in adj[u]:
                coverage[v] -= 1


def set_intersection_crossover(a: Individual, b: Individual) -> Individual:
    n = len(a.dom_set)
    child = Individual([False] * n)
    for i in range(n):
        child.dom_set[i] = a.dom_set[i] and b.dom_set[i]
    return child


def replace_weakest(pop: List[Individual], child: Individual) -> None:
    idx = worst_select_idx(pop)
    if child.fitness < pop[idx].fitness:
        pop[idx] = child


best = Individual()


def signal_handler(signum, frame):
    print(sum(best.dom_set))
    for j, v in enumerate(best.dom_set):
        if v:
            print(j + 1)
    sys.exit(0)


def debug(msg: str, end: str = "\n") -> None:
    if DEBUG:
        print(msg, end=end, file=sys.stderr, flush=True)


def main() -> None:
    global best

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    debug("Loading graph")
    adj = read_gr_file(sys.stdin)
    n = len(adj)

    # Initial fallback: everyone in. Guarantees a valid solution if we die early.
    best = Individual([True] * n)
    update_fitness(best)

    pop: List[Individual] = []
    for i in range(POP_SIZE):
        debug(f"Initializing population - {i + 1}", end="\r")
        ind = Individual([False] * n)
        greedy_priority_bucket_repair(adj, ind.dom_set)
        greedy_local_removal(adj, ind.dom_set)
        update_fitness(ind)
        pop.append(ind)
        if i == 0:
            best = ind.copy()

    debug("Starting optimization")

    i = 0
    while True:
        i += 1
        debug(f"{i} - {pop[best_select_idx(pop)].fitness}")

        p1 = tournament_select(pop)
        p2 = tournament_select(pop)

        child = set_intersection_crossover(p1, p2)
        greedy_priority_bucket_repair(adj, child.dom_set)
        greedy_local_removal(adj, child.dom_set)
        update_fitness(child)

        replace_weakest(pop, child)

        cur_best = pop[best_select_idx(pop)]
        if cur_best.fitness < best.fitness:
            best = cur_best.copy()


if __name__ == "__main__":
    main()