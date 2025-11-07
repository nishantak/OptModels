from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np


class ORToolsSolver:
    def __init__(self, data):
        self._dt = data
        self._routes = []
        self._manager = None
        self._routing = None
        self._solution = None
        
    def solve(self):
        # index managers
        num_vehicles = self._dt.args['V']
        num_nodes = self._dt.args['I'] + 1  # +1 for depot
        depot = 0
        
        self._manager = pywrapcp.RoutingIndexManager(
            num_nodes, num_vehicles, depot
        )
        
        self._routing = pywrapcp.RoutingModel(self._manager)
        
        def distance_callback(from_index, to_index):
            from_node = self._manager.IndexToNode(from_index)
            to_node = self._manager.IndexToNode(to_index)
            return int(self._dt.dist_matrix[from_node, to_node] * 1000) # metres
        
        transit_callback_index = self._routing.RegisterTransitCallback(distance_callback)
        self._routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # capacity constraint
        if self._dt.args['capacity'] == 1:
            def demand_callback(from_index):
                from_node = self._manager.IndexToNode(from_index)
                if from_node == 0:
                    return 0  # Depot has no demand
                return self._dt.demand[from_node - 1]
            
            demand_callback_index = self._routing.RegisterUnaryTransitCallback(demand_callback)
            self._routing.AddDimensionWithVehicleCapacity(
                demand_callback_index,
                0,  # null capacity slack
                [self._dt.args['v_cap']] * num_vehicles,  # vehicle maximum capacities
                True,  # start cumul to zero
                'Capacity'
            )
        
        # time window constraint
        if self._dt.args['time_windows'] == 1:
            def time_callback(from_index, to_index):
                from_node = self._manager.IndexToNode(from_index)
                to_node = self._manager.IndexToNode(to_index)
                # travel_time_matrix includes depot at index 0
                travel_time = self._dt.travel_time_matrix[from_node, to_node]
                # service time if leaving a customer (not depot)
                if from_node != 0:
                    service_time = self._dt.args['delta']
                    return int((travel_time + service_time) * 3600)  # seconds
                else:
                    return int(travel_time * 3600)  # drom depot
            
            time_callback_index = self._routing.RegisterTransitCallback(time_callback)
            self._routing.AddDimension(
                time_callback_index,
                int(self._dt.args['day_end'] * 3600),  # maximum time per vehicle (slack max)
                int(self._dt.args['day_end'] * 3600),  # maximum time per vehicle (capacity max)
                False,
                'Time'
            )
            
            time_dimension = self._routing.GetDimensionOrDie('Time')
            
            # time window constraints for each customer
            for customer_idx in range(1, num_nodes):
                index = self._manager.NodeToIndex(customer_idx)
                # Time window: earliest and latest service start time
                time_dimension.CumulVar(index).SetRange(
                    int(self._dt.e_t[customer_idx - 1] * 3600),
                    int(self._dt.l_t[customer_idx - 1] * 3600)
                )
            
            # depot time window for all vehicles
            for vehicle_id in range(num_vehicles):
                start_index = self._routing.Start(vehicle_id)
                end_index = self._routing.End(vehicle_id)
                time_dimension.CumulVar(start_index).SetRange(
                    int(self._dt.args['day_start'] * 3600),
                    int(self._dt.args['day_end'] * 3600))
                time_dimension.CumulVar(end_index).SetRange(
                    int(self._dt.args['day_start'] * 3600),
                    int(self._dt.args['day_end'] * 3600))
        
        # search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC
        )
        search_parameters.time_limit.seconds = 60
        search_parameters.log_search = False
        
        # SOLVE!
        self._solution = self._routing.SolveWithParameters(search_parameters)
        
        if self._solution:
            self._extract_routes()
            self._print_solution()
        else:
            raise RuntimeError("No solution found!")
    

    def _extract_routes(self):
        self._routes = []
        
        for vehicle_id in range(self._dt.args['V']):
            route = [0]  # Start at depot
            index = self._routing.Start(vehicle_id)
            
            while not self._routing.IsEnd(index):
                node = self._manager.IndexToNode(index)
                if node != 0:  # Skip depot in middle
                    route.append(node)
                index = self._solution.Value(self._routing.NextVar(index))
            
            route.append(0)  # Return to depot
            
            # non-empty routes
            if len(route) > 2:
                self._routes.append(route)
    
    def _validate_solution(self):
        num_customers = self._dt.args['I']
        num_vehicles = self._dt.args['V']
        vehicle_capacity = self._dt.args['v_cap']
        
        errors = []
        warnings = []
        
        # all customers are visited exactly once
        visited_customers = set()
        for route in self._routes:
            for node in route[1:-1]:  # depot start end
                if node in visited_customers:
                    errors.append(f"Customer {node} is visited more than once!")
                visited_customers.add(node)
        
        missing_customers = set(range(1, num_customers + 1)) - visited_customers
        if missing_customers:
            errors.append(f"Customers not visited: {sorted(missing_customers)}")
        
        # all routes start and end at depot
        for i, route in enumerate(self._routes):
            if route[0] != 0:
                errors.append(f"Route {i} does not start at depot: {route}")
            if route[-1] != 0:
                errors.append(f"Route {i} does not end at depot: {route}")
        
        # capacity constraints
        if self._dt.args['capacity'] == 1:
            for i, route in enumerate(self._routes):
                cumulative_demand = 0
                for node in route[1:-1]:  # excl depot
                    customer_idx = node - 1  # 0-ind
                    cumulative_demand += self._dt.demand[customer_idx]
                    if cumulative_demand > vehicle_capacity:
                        errors.append(
                            f"Route {i} exceeds capacity at customer {node}: "
                            f"cumulative demand {cumulative_demand} > capacity {vehicle_capacity}"
                        )
        
        # time window constraints
        if self._dt.args['time_windows'] == 1:
            for i, route in enumerate(self._routes):
                current_time = self._dt.args['day_start'] 
                
                for j in range(len(route) - 1):
                    from_node = route[j]
                    to_node = route[j + 1]
                    
                    # Travel time
                    travel_time = self._dt.travel_time_matrix[from_node, to_node]
                    current_time += travel_time
                    
                    # arriving at a customer
                    if to_node != 0:
                        customer_idx = to_node - 1
                        e_t = self._dt.e_t[customer_idx]
                        l_t = self._dt.l_t[customer_idx]
                        # early
                        if current_time < e_t:
                            current_time = e_t
                            warnings.append(
                                f"Route {i}: Vehicle arrives early at customer {to_node}, "
                                f"waits until {e_t:.2f}"
                            )
                        elif current_time > l_t:
                            errors.append(
                                f"Route {i}: Vehicle arrives late at customer {to_node}: "
                                f"arrival time {current_time:.2f} > latest time {l_t:.2f}"
                            )
                        
                        current_time += self._dt.args['delta'] # service time
        
        # total capacity vs total demand
        total_demand = sum(self._dt.demand)
        total_capacity = num_vehicles * vehicle_capacity
        if total_demand > total_capacity:
            errors.append(
                f"Total demand {total_demand} exceeds total capacity {total_capacity}"
            )
        
        if errors:
            print('\n' + '='*60)
            print('VALIDATION FAILED - Solution has errors:')
            print('='*60)
            for error in errors:
                print(f"  ERROR: {error}")
            print('='*60)
            raise ValueError("Solution validation failed! See errors above.")
        else:
            print('\n' + '='*60)
            print('VALIDATION PASSED - Solution is correct!')
            print('='*60)

            if warnings:
                print(f"\nWarnings ({len(warnings)}); mostly early & waiting:")
                for warning in warnings[:5]:
                    print(f"  WARNING: {warning}")
                if len(warnings) > 5:
                    print(f"  ... and {len(warnings) - 5} more warnings")
            print('='*60)
    
    def _print_solution(self):
        print('\n', '-'*5, 'The Solution', '-'*5, '\n')
        total_distance = 0
        
        for i, route in enumerate(self._routes):
            route_distance = 0
            for j in range(len(route) - 1):
                route_distance += self._dt.dist_matrix[route[j], route[j + 1]]
            total_distance += route_distance
            print(f'Route for vehicle {i}: {route} (Distance: {route_distance:.2f} miles)')
        
        print(f'\nTotal distance: {total_distance:.2f} miles')
        self._validate_solution()

