import argparse
from _data_generation import DataGenerator
from ortools_solver import ORToolsSolver


def parse_arguments():
    parser = argparse.ArgumentParser(description="VRPTW Solver")
    parser.add_argument('--V', type=int, default=4, help='Number of vehicles')
    parser.add_argument('--v_cap', type=int, default=4, help='Vehicle capacity')
    parser.add_argument('--I', type=int, default=15, help='Number of customers')
    parser.add_argument('--r', type=float, default=10, help='Network radius (miles)')
    parser.add_argument('--loc_depot', type=float, nargs=2, default=[40.943, -75.501], 
                        metavar=('LAT', 'LON'), help='Depot coordinates [lat, lon]')
    parser.add_argument('--delta', type=float, default=0.25, help='Service time (hours)')
    parser.add_argument('--day_start', type=int, default=9, help='Business day start time')
    parser.add_argument('--day_end', type=int, default=17, help='Business day end time')
    parser.add_argument('--demand_per_customer', type=int, default=1, help='Demand per customer')
    parser.add_argument('--max_time_window_length', type=int, default=4, 
                        help='Max time window length (hours)')
    parser.add_argument('--travel_time_factor', type=float, default=2, 
                        help='Travel time scaling factor')
    parser.add_argument('--time_windows', type=int, choices=[0, 1], default=1,
                        help='Enable time windows (1) or not (0)')
    parser.add_argument('--capacity', type=int, choices=[0, 1], default=1,
                        help='Enable capacity constraints (1) or not (0)')
    
    args = parser.parse_args()
    return {
        'V': args.V,
        'v_cap': args.v_cap,
        'I': args.I,
        'r': args.r,
        'loc_depot': args.loc_depot,
        'delta': args.delta,
        'day_start': args.day_start,
        'day_end': args.day_end,
        'demand_per_customer': args.demand_per_customer,
        'max_time_window_length': args.max_time_window_length,
        'travel_time_factor': args.travel_time_factor,
        'time_windows': args.time_windows,
        'capacity': args.capacity
    }

if __name__ == '__main__':
    args = parse_arguments()
    data = DataGenerator(args)
    print(
        '\nnum of vehicles = {} \nnum of customers = {}'.format(
            data.args['V'], data.args['I']
        )
    )
    print('Using OR-Tools solver...')
    model = ORToolsSolver(data)
    model.solve()
    
    data._plot_routes(model._routes)