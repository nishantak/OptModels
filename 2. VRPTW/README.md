# VRPTW - MILP Formulation and OR-Tools Solver

## Problem Statement

A logistics company must deliver goods from a single depot to multiple customers. Each customer has a delivery time window, and each vehicle has a limited capacity. The goal is to minimize total travel distance while satisfying delivery constraints.

**Given:**
- A depot (node 0) and $I$ customers (nodes $1, 2, \ldots, I$)
- $V$ identical vehicles, each with capacity $Q$
- Distance matrix $d_{ij}$ between all pairs of nodes $(i,j)$
- For each customer $i$: demand $q_i$, time window $[e_i, l_i]$, service time $\delta_i$
- Travel time matrix $t_{ij}$ between nodes

**Find:** Routes for vehicles that:
- Start and end at the depot
- Visit each customer exactly once
- Respect vehicle capacity constraints
- Respect customer time windows

**Goal:** Minimize total distance traveled

---

## VRPTW as MILP

### Decision Variables

$$
x_{ij} = \begin{cases}
1 & \text{if a vehicle travels from node } i \text{ to node } j,\ i \neq j \\
0 & \text{otherwise}
\end{cases}
\qquad \forall i,j \in \{0,\ldots,I\},\ i\neq j
$$

$$
s_i \ge 0 \quad \text{service start time at node } i \quad \forall i \in \{0,\ldots,I\}
$$

$$
u_i \ge 0 \quad \text{vehicle load after serving } i \quad \forall i \in \{0,\ldots,I\}
$$


### Objective Function

Minimize total distance traveled:

$$
\min \sum_{i=0}^{I} \sum_{\substack{j=0\\j \neq i}}^{I} d_{ij} x_{ij}
$$


### Constraints

#### 1. Depot Exit Constraint
Exactly $V$ vehicles leave the depot:
$$
\sum_{j=1}^{I} x_{0j} = V
$$

#### 2. Depot Return Constraint
Exactly $V$ vehicles return to the depot:
$$
\sum_{i=1}^{I} x_{i0} = V
$$

#### 3. Customer Visit Constraints
Each customer must be visited exactly once (incoming and outgoing):
$$
\sum_{\substack{i=0\\i \neq k}}^{I} x_{ik} = 1 \quad \forall k \in \{1,\ldots,I\}
$$
$$
\sum_{\substack{k=0\\k \neq j}}^{I} x_{kj} = 1 \quad \forall j \in \{1,\ldots,I\}
$$

#### 4. Capacity Constraints
If a vehicle travels from $i$ to $j$ and serves $j$, load increases by $q_j$.  
Bounds prevent infeasible negative/oversized loads.

$$
u_0 = 0
$$

$$
q_i \le u_i \le Q \quad \forall i \in \{1,\ldots,I\}
$$

$$
u_j \ge u_i + q_j - Q(1 - x_{ij}) \quad \forall i \ne j,\ \{i,j\} \in \{0,\ldots,I\}
$$

#### 5. Time Window Constraints
If a vehicle travels from $i$ to $j$, service at $j$ must start after finishing service at $i$ and traveling:

$$
s_j \ge s_i + \delta_i + t_{ij} - M(1 - x_{ij}) \quad \forall i \ne j,\ \{i,j\}\in\{0,\ldots,I\}\\
\delta_0 = 0
$$

Time window bounds:

$$
e_i \le s_i \le l_i \quad \forall i \in \{0,\ldots,I\}
$$

Return:

$$
s_i + \delta_i + t_{i0} \le l_0 + M(1 - x_{i0}) \quad \forall i \in \{1,\ldots,I\}
$$

A sufficient bound (maybe a bit loose):
$$
M = l_0 - e_0
$$

#### 6. No Self-Loops
$$
x_{ii} = 0 \quad \forall i \in \{0,\ldots,I\}
$$

### Complete MILP Formulation

$$
\begin{aligned}
\min \quad &
\sum_{i=0}^{I} \sum_{\substack{j=0 \\ j \neq i}}^{I} d_{ij} x_{ij} \\
\text{s.t.} \quad
& \sum_{j=1}^{I} x_{0j} = V \\
& \sum_{i=1}^{I} x_{i0} = V \\
& \sum_{\substack{i=0 \\ i \neq k}}^{I} x_{ik} = 1 \quad \forall k \in \{1,\ldots,I\} \\
& \sum_{\substack{k=0 \\ k \neq j}}^{I} x_{kj} = 1 \quad \forall j \in \{1,\ldots,I\} \\
& u_0 = 0 \\
& q_h \le u_h \le Q \quad \forall h \in \{1,\ldots,I\} \\
& u_j \ge u_i + q_j - Q(1 - x_{ij}) \quad \forall i \ne j,\ \{i,j\}\in\{0,\ldots,I\} \\
& e_i \le s_i \le l_i \quad \forall i\in\{0,\ldots,I\} \\
& s_j \ge s_i + \delta_i + t_{ij} - M(1 - x_{ij}) \quad \forall i \ne j,\ \{i,j\}\in\{0,\ldots,I\} \\
& s_i + \delta_i + t_{i0} \le l_0 + M(1 - x_{i0}) \quad \forall i \in \{1,\ldots,I\} \\
& x_{ii} = 0 \quad \forall i\in\{0,\ldots,I\} \\
& x_{ij} \in \{0,1\} \quad \forall i \ne j \\
& s_i, u_i \ge 0 \quad \forall i\in\{0,\ldots,I\}
\end{aligned}
$$

**Total Constraints:** $O(I^2)$  
**Complexity:** Single-commodity arc formulation. NP-Hard.



---

## Implementation

The implementation consists of four main components:

1. **Data Generation** (`_data_generation.py`): Generates synthetic VRPTW instances
2. **OR-Tools Solver** (`ortools_solver.py`): Solves VRPTW using constraint programming
3. **Utilities** (`_utils.py`): Helper functions for distance calculation and parameter parsing
4. **Main Solver** (`solve.py`): Orchestrates data generation, solving, and visualization

### Data Generation

The `DataGenerator` class generates synthetic VRPTW instances:

**Location Generation:**
- Depot location: Fixed at coordinates $(lat_0, lon_0)$
- Customer locations: Randomly generated within radius $r$ miles of depot using uniform distribution in polar coordinates:
  - Distance: $r \cdot \sqrt{U}$ where $U \sim \text{Uniform}(0,1)$
  - Angle: $\theta \sim \text{Uniform}(0, 2\pi)$

**Distance Matrix:**
- Computed using geodesic distance (great-circle distance on Earth's surface)
- $d_{ij} = \text{geodesic}((lat_i, lon_i), (lat_j, lon_j))$ in miles

**Time Windows:**
- Start time $e_i$: Randomly chosen from $[T_{\text{start}}, T_{\text{end}} - 1]$
- Window duration: Randomly chosen from $[0, \text{max windoow length}]$
- End time: $l_i = \min(e_i + \text{duration}, T_{\text{end}})$

**Travel Time:**
- $t_{ij} = \alpha \cdot \frac{d_{ij}}{r}$ where $\alpha$ is a travel time factor

**Dataset Export:**
- Exports to CSV and JSON formats with all required fields:
  - Customer ID
  - Coordinates (X, Y)
  - Demand (units)
  - Time Window Start
  - Time Window End
  - Service Time
  - Vehicle Capacity
  - Depot Coordinates

### OR-Tools Solver

OR-Tools uses constraint programming (CP) rather than direct MILP solving. The CP approach:

**Routing Model:**
- Creates a routing index manager for $I+1$ nodes (depot + customers) and $V$ vehicles
- Uses callback functions to define:
  - **Distance callback**: Returns $d_{ij}$ for arc $(i,j)$
  - **Demand callback**: Returns $q_i$ for node $i$
  - **Time callback**: Returns $t_{ij} + \delta$ for arc $(i,j)$ (includes service time)

**Constraints:**
- **Capacity Dimension**: Tracks cumulative demand along routes
  - $z_j \geq z_i + q_i$ if vehicle travels from $i$ to $j$
  - $z_i \leq Q$ for all nodes
- **Time Dimension**: Tracks cumulative time along routes
  - $s_j \geq s_i + t_{ij} + \delta$ if vehicle travels from $i$ to $j$
  - $e_i \leq s_i \leq l_i$ for all customers

**Search Strategy:**
- First solution strategy: AUTOMATIC (OR-Tools selects best heuristic)
- Local search metaheuristic: AUTOMATIC (guided local search, simulated annealing, etc.)
- Time limit: 60 seconds

**Solution Extraction:**
- Extracts routes by following the solution's next variables
- Each route: $[0, i_1, i_2, \ldots, i_k, 0]$ (depot → customers → depot)

### Visualization

**Network Plot:**
- Shows depot (red star) and customers (blue triangles) on geographic map
- Uses contextily for basemap (OpenStreetMap tiles)

**Solution Plot:**
- Overlays vehicle routes on network plot
- Each route shown in different color with directional arrows
- Routes displayed as: Depot → Customer sequence → Depot

---

## Usage

```bash
python solve.py [OPTIONS]
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--V` | Number of vehicles | 4 |
| `--I` | Number of customers | 15 |
| `--v_cap` | Vehicle capacity | 4 |
| `--r` | Network radius (miles) | 10 |
| `--loc_depot` | Depot coordinates [lat, lon] | [40.943, -75.501] |
| `--delta` | Service time (hours) | 0.25 |
| `--day_start` | Business day start time | 9 |
| `--day_end` | Business day end time | 17 |
| `--demand_per_customer` | Demand per customer | 1 |
| `--max_time_window_length` | Max time window (hours) | 4 |
| `--travel_time_factor` | Travel time scaling factor | 2 |
| `--time_windows` | Enable time windows (0/1) | 1 |
| `--capacity` | Enable capacity constraints (0/1) | 1 |

### Example

```bash
 python solve.py --V 5 --I 10 --v_cap 6
```

This generates a VRPTW instance with:
- 5 vehicles
- 10 customers
- Vehicle capacity of 6 units
- Time windows enabled
- Capacity constraints enabled

### Output Files

Generated in `output/` directory:
- `dataset_num_vehicle{V}_num_customers{I}.csv`: Dataset in CSV format
- `dataset_num_vehicle{V}_num_customers{I}.json`: Dataset in JSON format
- `network_num_vehicle{V}_num_customers{I}.PNG`: Network visualization
- `solution_num_vehicle{V}_num_customers{I}.PNG`: Solution visualization

---

## Solution Validation

To ensure the solution is correct, the implementation includes comprehensive validation that verifies all constraints are satisfied:

### Validation Checks

1. **Customer Visit Constraint**
   - Verifies each customer is visited exactly once
   - Checks no customer is visited multiple times
   - Ensures no customers are missing from routes

2. **Depot Constraints**
   - Verifies all routes start at depot (node 0)
   - Verifies all routes end at depot (node 0)

3. **Capacity Constraints**
   - For each route, tracks cumulative demand along the route
   - Verifies cumulative demand never exceeds vehicle capacity $Q$
   - Checks total fleet capacity $\geq$ total customer demand

4. **Time Window Constraints**
   - Simulates vehicle travel along each route
   - Tracks arrival time at each customer
   - Verifies arrival time is within time window $[e_i, l_i]$
   - Accounts for waiting time if vehicle arrives early
   - Adds service time $\delta$ after each customer visit

5. **Route Connectivity**
   - Verifies routes form valid paths (no disconnected segments)
   - Ensures routes are properly extracted from solver solution


### Optimality vs Feasibility
The validation verifies **feasibility** (solution satisfies all constraints), not **optimality** (solution is the best possible).

- **Feasible solution**: Satisfies all constraints (what we verify)
- **Optimal solution**: Feasible solution with minimum objective value


**Current Implementation (OR-Tools with Heuristics):**
- **Does NOT guarantee optimality**
- Finds feasible solutions quickly
- Uses heuristic search (guided local search, simulated annealing)
- May find good solutions but cannot prove they're optimal

## Complexity Analysis

**Problem Size:**
- Variables: $O(I^2)$ binary variables $x_{ij}$ + $O(I)$ continuous variables $(s_i, z_i)$
- Constraints: $O(I^2)$ constraints (mainly from capacity and time window flow constraints)

**Computational Complexity:**
- VRPTW is NP-Hard (generalization of TSP)
- OR-Tools uses constraint programming with heuristics
- Time limit: 60 seconds (configurable)

**Feasibility:**
- Ensure total capacity $\geq$ total demand: $V \cdot Q \geq \sum_{i=1}^{I} q_i$
- Ensure time windows are feasible (sufficient vehicles and time)
- Some instances may be infeasible if constraints are too tight

**Trade-Offs:**

- Shorter total distance often conflicts with tight windows. A vehicle may detour or wait. 

- Capacity is modeled by cumulative demand. Time windows are modeled by node service intervals and propagation. Total distance minimization pushes routes to follow short chains of customers. Time windows restrict feasible order. If a spatially close customer is only available later, the route may wait or reorder. That increases total distance or idle time. Capacity limits route length in terms of total demand. If many high-demand customers cluster, we need more vehicles or split routing. Time windows and capacity define feasibility. Distance defines cost.

- MILP is exact but scales poorly. Heuristics scale but lose optimality. MILP complexity grows badly. Runtime becomes unstable. Heuristics scale to more stops. Solution quality is close to optimal when time windows are loose. As time windows tighten, heuristic search needs more iterations but remains practical.
