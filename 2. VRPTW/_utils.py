import numpy as np
from geopy.distance import distance, geodesic
from geopy import Point as GeoPoint


def _dist_matrix(locations):
    assert len(locations) > 1, "At least two points are required"
    m = len(locations)
    dist_matrix = np.zeros((m, m))
    for i in range(m):
        for j in range(m):
            loc1, loc2 = locations[i], locations[j]
            dist_matrix[i, j] = geodesic(loc1, loc2).miles
    return dist_matrix


def _generate_random_point(center, radius):
    r = radius * np.sqrt(np.random.rand())
    theta = np.random.uniform(0, 2 * np.pi)
    origin = GeoPoint(center)
    destination = distance(miles=r).destination(
        point=origin, bearing=np.degrees(theta)
    )
    return destination.latitude, destination.longitude


