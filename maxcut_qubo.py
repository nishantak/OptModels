import time, math, random, heapq
from typing import List, Tuple
import numpy as np

Edge = Tuple[int, int, float]  # (u, v, w), 0-based

def read_gset(path: str) -> Tuple[int, List[Edge]]:
    # n_v, n_e
    # i, k, w_ik
    with open(path) as f:
        n, m = map(int, f.readline().split())
        edges: List[Edge] = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 0-indexed
            u, v, *w = line.split()
            u = int(u) - 1
            v = int(v) - 1
            if u == v:
                continue
            if u > v:
                u, v = v, u
            w = float(w[0]) if w else 1.0
            edges.append((u, v, w))
        assert len(edges) == m, f"Expected {m} edges, got {len(edges)}"
    return n, edges


# ---- Graph -> adjacency lists ----
def to_adj_lists(n: int, edges: List[Edge]):
    nbr = [[] for _ in range(n)]
    wts = [[] for _ in range(n)]
    for i, j, w in edges:
        nbr[i].append(j); wts[i].append(w)
        nbr[j].append(i); wts[j].append(w)
    return nbr, wts


# ---- Cut and initialization ----
def cut_from_spin(nbr, wts, s: np.ndarray) -> float:
    cut = 0.0
    for i, (N, W) in enumerate(zip(nbr, wts)):
        si = s[i]
        for j, w in zip(N, W):
            if j > i:
                cut += 0.5 * w * (1.0 - si * s[j])
    return cut


def init_state(nbr, wts, rng: random.Random):
    n = len(nbr)
    s = np.where(np.random.RandomState(rng.randrange(1 << 30)).randn(n) >= 0, 1, -1).astype(np.int8)
    t = np.zeros(n, dtype=np.float64)
    for i in range(n):
        t[i] = sum(w * s[j] for j, w in zip(nbr[i], wts[i]))
    g = s.astype(np.float64) * t
    cur_cut = cut_from_spin(nbr, wts, s)
    return s, t, g, cur_cut


# ---- Tabu + Breakout Local Search ----
def tabu_bls_maxcut(
    nbr, wts,
    iters: int = 10240,
    tenure_min: int = 4,
    tenure_max: int = 16,
    plateau: int = 1024,
    perturb_k: int = 8,
    seed: int = 22
):
    rng = random.Random(seed)
    n = len(nbr)
    s, t, g, cur_cut = init_state(nbr, wts, rng)
    best_s = s.copy(); best_cut = cur_cut

    tabu_until = np.zeros(n, dtype=np.int64)
    heap = []
    ver = np.zeros(n, dtype=np.int64)
    for i in range(n):
        heapq.heappush(heap, (-g[i], i, ver[i]))

    def push(i):
        heapq.heappush(heap, (-g[i], i, ver[i]))

    no_improve = 0
    for step in range(1, iters + 1):
        # select best admissible move (aspiration enabled)
        move_i = -1
        move_gain = -math.inf
        while heap:
            neg_gain, i, v = heapq.heappop(heap)
            if v != ver[i]:
                continue
            gain_i = -neg_gain
            is_tabu = tabu_until[i] > step
            if is_tabu and (cur_cut + gain_i) <= best_cut:
                continue
            move_i = i
            move_gain = gain_i
            break
        if move_i == -1:
            cand = [i for i in range(n) if tabu_until[i] <= step] or list(range(n))
            move_i = rng.choice(cand)
            move_gain = g[move_i]

        # apply flip
        s[move_i] = -s[move_i]
        cur_cut += move_gain
        tabu_until[move_i] = step + rng.randint(tenure_min, tenure_max)

        # update neighbors
        si_new = s[move_i]
        for j, w in zip(nbr[move_i], wts[move_i]):
            t[j] += 2.0 * w * si_new
            g[j] = s[j] * t[j]
            ver[j] += 1
            push(j)
        g[move_i] = -g[move_i]
        ver[move_i] += 1
        push(move_i)

        if cur_cut > best_cut:
            best_cut = cur_cut
            best_s = s.copy()
            no_improve = 0
        else:
            no_improve += 1

        # breakout
        if no_improve >= plateau:
            k = min(perturb_k, n)
            worst = np.argpartition(g, k - 1)[:k]
            for i in worst:
                s[i] = -s[i]
                cur_cut += g[i]
                si_new = s[i]
                for j, w in zip(nbr[i], wts[i]):
                    t[j] += 2.0 * w * si_new
                    g[j] = s[j] * t[j]
                    ver[j] += 1
                    push(j)
                g[i] = -g[i]
                ver[i] += 1
                push(i)
                tabu_until[i] = step + rng.randint(tenure_min, tenure_max)
            no_improve = 0

    return best_s, float(best_cut)


def solve_maxcut(path: str, iters=10240, plateau=1024, perturb_k=8, seed=22):
    n, edges = read_gset(path)
    nbr, wts = to_adj_lists(n, edges)
    t0 = time.time()
    s_best, cut_best = tabu_bls_maxcut(
        nbr, wts,
        iters=iters,
        plateau=plateau,
        perturb_k=perturb_k,
        seed=seed
    )
    t1 = time.time()
    x = ((s_best + 1) // 2).astype(np.int32)
    print(f"Best cut: {float(cut_best)}")
    print(f"Time: {t1 - t0:.3f} s")
    # print(f"x[0:{n}]:", ''.join(map(str, x[:{n}].tolist())))

if __name__ == "__main__":
    solve_maxcut("gset_instances/G1.txt", iters=2048, plateau=512, perturb_k=8)
