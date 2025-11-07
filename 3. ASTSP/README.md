# 3. MILP Solver and benchmark on ATSP (TSPLIB)

## Linear Programming

**Goal:**

To minimize an objective/cost function, say $F(x)$ of the form $c^Tx$, i.e

$$
\min_{x} F(x) = \min_{x} c^Tx
$$

over a convex *solution space* (polyhedron). [because continuous] 

s.t. $Ax \leq b\;;\; x\in{\mathbb{R}^n}$, all constraints are linear.

Feasible Region: $P = \{x: Ax\leq b\}$ is a convex polyhedron.

Then,

**Feasible:** $\exist \; x$ that satisfies all constraints.

**Bounded:** $\text{inf} \; c^Tx > -\infty$ over $P$.

If feasible AND bounded, then the otpimal solution is attained at a vertex of the polyhedron.

### Dual vs Primal:

Given an LP (primal), there exists an LP (dual), s.t objective value of the dual LP at any feasible solution is always a bound on the objective of the primal LP at any feasible solution. (lower bound for minimisation problem.) [weak duality theorem]

The dual of a given LP is another LP that is derived from the original (the primal) LP:

- Each variable in the primal LP becomes a constraint in the dual LP;

- Each constraint in the primal LP becomes a variable in the dual LP;

- The objective direction is inversed – maximum in the primal becomes minimum in the dual and vice versa.

### Motivation: What is a lower bound on $\min⁡c^⊤x$ ?

$$
(something) \leq c^Tx
$$

**Goal:** Maximise $(something)$ (under some constraints)

Suppose a constraint: $A_ix = b_i$

Let $y_i$ be the dual variable $\in \mathbb{R}$

Multiply,

$$
\sum_i y_i(A_ix) = \sum_i y_ib_i
\implies (A^Ty)^Tx = b^Ty
$$

If we can prove,

$$
(A^Ty)^Tx \leq c^Tx \implies b^Ty \text{ is a lower bound.} \quad \text{(for all feasible x)}
$$

So, we need to maximise $b^Ty$, under the constraint $A^Ty \le c.$

Thus, the Dual LP becomes

$$
\max_y b^Ty\;;\; s.t.\; A^Ty \le c 
$$

Furthermore, if there exists an optimal solution for the primal, there must exist an optimal solution for the dual, s.t they both coincide. [Strong duality theorem]

Thus,
$$
\min_x c^Tx = \max_y b^Ty 
$$
proving optimality.

---

## Mixed-Integer Linear Programing (MILP)

= linear objective + linear constraints + some integer variables.

A problem becomes a mixed-integer linear program when at least one variable is forced to be integer.

Formally,
$$
\min c^Tx \;; \quad Ax\le b,\;\; l \leq x \leq u,\;\; {x_i \in \mathbb{Z} \;\;\forall i \in I}
$$

$I$ is the index set of points in $x$ that are integers:

- $I = \phi$: Linear programming
- some of the $j$ (of $x_j$) $\in I$: Mixed-integer
- all $j \in I$: Integer linear programming

So, this added constraint that some components of $x$ are integer-restricted makes it MILP and NP-Hard. Integrality makes this set non-convex. (We will use branch-and-bound technique to solve this here.) 

### LP Relaxation

Removes the integrality constraint making the problem easier. Thus, we have
$$
\min c^Tx \;;\; s.t. \; Ax\le b,\; x\in \mathbb{R}^n
$$
Let the optimal value for this be $p^*$.

Let the optimal value for the [unrelaxed] MILP be $p$.

Since, feasible set of LP $\supseteq$ feasible set of MILP (ofc, geometry)
$$
\implies p^*\leq p
$$

(duality, similarly, proves optimality of this.)

### For branch-and-bound:
This means that we can check the LP relaxation of a branch - if it gives a cost worse than the current best integer solution, we can prune that branch as it will not improve.

- Root LP: solve the relaxation. If infeasible --> MILP infeasible. If integer --> done.

- Branching: pick a variable $x_k$ with fractional value $v$. Create two child nodes: $x_k \leq \lfloor v\rfloor$, $x_k \geq \lceil v\rceil$.

- Bounding: solve LP at each node to get a bound. If bound >= incumbent, prune.

- Incumbent update: whenever you find an integer-feasible solution with better objective, update incumbent.

- Node selection: choose next node (e.g., best-bound, depth-first).

- Terminate when no nodes remain. Incumbent is optimal.

---

## Assymetric Travelling Salesman Problem (ATSP)

Given a complete, directed graph $G = (V, E)$ with $|V|=n$ and arc (edge) cost $d_{ij} > 0$, find a minimal-cost Hamiltonian directed cycle.

Meaning, to form a tour, without subtours, that has the minimum cost.

## ASTP as MILP

### DFJ Formulation
$$
x_{ij} =
\begin{cases}
1; & \text{if arc(i, j) in tour} ,\; i \ne j \\
0; & \text{otherwise}
\end{cases}
$$

Objective function then becomes,

$$
F(x) = \sum_{(i,j) \in E}c_{ij} = \sum_{(i,j) \in E}d_{ij}x_{ij}
$$

**Goal:** $\min F(x)$

**Constraints:**

- Ensure all nodes visited only once: $2n$ constraints

$$
\text{For node } k \in V
$$

$$
\underbrace{\sum_{i\ne k\;;\; i\in V} x_{ik} = 1}_{incoming} \;\; and \;\; \underbrace{\sum_{k\ne j\;;\;j\in V} x_{kj} = 1}_{outgoing}
$$

- Forbid subtours (Subtour elimination constraints (SEC)): $2^n$ total $-  2$ not included ($|S|=0$ and $|S|=n$) $- n$ (singular nodes $|S|=1$) $= 2^n - n - 2$ constraints.
$$
\sum_{i\in S}\sum_{j\in S\;;\;j\ne i} x_{ij} \leq |S| - 1 \;;\quad \forall\; S \subsetneq V (\implies |S| \le n-1), |S| \ge 2 
$$

However, as we can see total constraints are exponential, in $O(2^n)$. 

Total Constraints $= 2n + 2^n - n - 2 \;=\; 2^n + n- 2$

### MTZ Formulation

Uses order variables $u_i$ to break subtours.

The following remains the same,

$$
x_{ij} \in \{0,1\}
$$

Objective function then becomes,

$$
F(x) = \sum_{(i,j) \in E}d_{ij}x_{ij}
$$

**Goal:** $\min F(x)$

**Constraints:**
- Ensure all nodes visited only once: $2n$ constraints

$$
\text{For node } k \in V
$$

$$
\sum_{i\ne k\;;\; i\in V} x_{ik} = 1\;\; and \;\; \sum_{k\ne j\;;\;j\in V} x_{kj} = 1
$$

- SEC:

We define order vairable, $u_i = k$ if node $i$  is the $k^{th}$ node to be visited. 

$1 \le u_i \le n-1,\;\forall\;i\ne1\quad$: $2(n-1)$ constraints.

Then using a Big-M constraint (boolean switch-type logic to deactivate constraint when $x_{ij}=0$, --> M becomes nonbinding),
$$
u_i+1 \le u_j + M(1-x_{ij})
$$

Given the bounds, largest possible gap between $u_i$ and $u_j$ is $(n-1)-1 = n-2$. $\implies M = (n-1)$ is sufficiently large M.

Thus,
$$
u_i+1 \le u_j + (n-1)(1-x_{ij}) \quad\\
$$ 

: $n-2$ pairs for each chosen $n-1$ nodes $= (n-1)(n-2)$ constraints.

Solving which we get,
$$
u_i - u_j + nx_{ij} \le n-1
$$

**Total Constraints =** Polynomial, $O(n^2)$: $2n + (n-1)(n-2) + 2(n-1) = n^2 + n$

<br>

> Intrestingly, DFJ is shown to outperform MTZ. This is because When $x_{ij}$ are allowed to take fractional values (LP relaxation), MTZ constraints do not tightly restrict them because of the numeric *ordering*. DFJ has stronger relaxation; its constraints describe the convex hull of all tours much more accurately. This does not allow fractional subtours. Thus, the LP performs much tighter and closer to integer solution, despite the exponential constraints. However, the exponential constraints are not added all at once and added *when needed*.

---

