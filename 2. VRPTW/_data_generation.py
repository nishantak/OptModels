import numpy as np
import pandas as pd
import json
import os
from shapely.geometry import Point
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
from _utils import _dist_matrix, _generate_random_point
from matplotlib.cm import get_cmap

np.random.seed(42)

class DataGenerator:
    def __init__(self, args):
        self.args = args
        # Create output folder if it doesn't exist
        os.makedirs('output', exist_ok=True)
        self._construct_locations()
        self._generate_random_data()
        self._export_dataset()
        self.fig, self.ax = plt.subplots(figsize=(8, 8), dpi=100)

    def _generate_random_data(self):
        self.demand = [self.args['demand_per_customer']] * self.args['I']
        self.e_t = np.random.choice(
            range(self.args['day_start'], self.args['day_end'] - 1),
            self.args['I']
            ).tolist()
        time_duration = np.random.choice(
            list(range(self.args['max_time_window_length'])),
            self.args['I']
            )
        time_duration = time_duration.tolist()
        self.l_t = [min(s + d, self.args['day_end']) for s, d in
                    zip(self.e_t, time_duration)
                    ]
        self.travel_time_matrix = self.args['travel_time_factor'] * (
            self.dist_matrix / self.args['r']
        )

    def _construct_locations(self):
        self.loc_customers = [
            _generate_random_point(self.args['loc_depot'], self.args['r'])
            for _ in range(self.args['I'])
        ]
        self.locations = [self.args['loc_depot']] + self.loc_customers
        self.dist_matrix = _dist_matrix(self.locations)
        self.geoms = [Point(lon, lat) for (lat, lon) in self.locations]

    def _plot_locations(self):
        # Create GeoDataFrame
        labels = ['depot'] + ['customer' for _ in range(self.args['I'])]
        demand = [0] + self.demand
        gdf = gpd.GeoDataFrame({'label': labels, 'demand': demand})
        # Set the geometry column explicitly
        gdf = gdf.set_geometry(self.geoms)
        gdf.crs = 'EPSG:4326'  # Assign the CRS explicitly
        depot = gdf[gdf['label'] == 'depot']
        customers = gdf[gdf['label'] == 'customer']

        # Plot depot
        depot.plot(
            ax=self.ax,
            markersize=200,
            color='red',
            marker='*',
            label='Depot'
        )
        # Plot customers
        customers.plot(
            ax=self.ax,
            markersize=100,
            color='blue',
            marker='^',
            label='Customers'
        )
        ctx.add_basemap(ax=self.ax, crs=gdf.crs, attribution="")
        self.ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
        plt.tight_layout()
        plt.savefig(
            'output/network_num_vehicle{}_num_customers{}.PNG'.format(
                self.args['V'], self.args['I']),
            dpi=300,
            bbox_inches='tight'
        )

    def _plot_routes(self, routes):
        print('Plotting routes...')
        self._plot_locations()
        v = len(routes)
        cmap = get_cmap('copper', v)
        colors = [cmap(i) for i in range(cmap.N)]

        for v, route in enumerate(routes):
            customers_gis = np.array(self.locations)[route]
            customers_gis = customers_gis[:, [1, 0]]  # Flip to (long, lat)

            for i in range(len(customers_gis) - 1):
                start = customers_gis[i]
                end = customers_gis[i + 1]
                self.ax.plot(
                    [start[0], end[0]], [start[1], end[1]],
                    color=colors[v], linewidth=2, alpha=0.8,
                    label=f'Route {v}' if i == 0 else ""
                )
                self.ax.annotate(
                    '', xy=end, xycoords='data',
                    xytext=start, textcoords='data',
                    arrowprops=dict(
                        arrowstyle="->", color=colors[v], lw=2
                    )
                )
        self.ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
        plt.tight_layout()
        fig_path = 'output/solution_num_vehicle{}_num_customers{}.PNG'.format(
            self.args['V'], self.args['I']
            )
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        print(f'done!\nThe optimal routes are is available at{fig_path}')
    

    def _export_dataset(self):
        dataset = []
        
        # depot information
        depot_lat, depot_lon = self.args['loc_depot']
        dataset.append({
            'Customer ID': 0,
            'Type': 'Depot',
            'Coordinates_X': depot_lon,  # Longitude
            'Coordinates_Y': depot_lat,   # Latitude
            'Demand_units': 0,
            'Time_Window_Start': self.args['day_start'],
            'Time_Window_End': self.args['day_end'],
            'Service_Time': 0
        })
        
        # customer information
        for i in range(self.args['I']):
            customer_id = i + 1
            lat, lon = self.loc_customers[i]
            dataset.append({
                'Customer ID': customer_id,
                'Type': 'Customer',
                'Coordinates_X': lon,  # Longitude
                'Coordinates_Y': lat,   # Latitude
                'Demand_units': self.demand[i],
                'Time_Window_Start': self.e_t[i],
                'Time_Window_End': self.l_t[i],
                'Service_Time': self.args['delta']
            })
        
        df = pd.DataFrame(dataset)
        csv_path = f'output/dataset_num_vehicle{self.args["V"]}_num_customers{self.args["I"]}.csv'
        df.to_csv(csv_path, index=False)
        print(f'Dataset exported to: {csv_path}')
        
        json_data = {
            'Vehicle_Capacity': self.args['v_cap'],
            'Number_of_Vehicles': self.args['V'],
            'Depot_Coordinates': {
                'Latitude': depot_lat,
                'Longitude': depot_lon
            },
            'Customers': [
                {
                    'Customer_ID': row['Customer ID'],
                    'Coordinates': {
                        'X': row['Coordinates_X'],
                        'Y': row['Coordinates_Y']
                    },
                    'Demand_units': row['Demand_units'],
                    'Time_Window_Start': row['Time_Window_Start'],
                    'Time_Window_End': row['Time_Window_End'],
                    'Service_Time': row['Service_Time']
                }
                for idx, row in df.iterrows() if row['Type'] == 'Customer'
            ]
        }
        
        json_path = f'output/dataset_num_vehicle{self.args["V"]}_num_customers{self.args["I"]}.json'
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        print(f'Dataset metadata exported to: {json_path}')