import pandas as pd
from pyproj import Geod

def bbox_area(row):
    min_lon, max_lon, min_lat, max_lat = row["min_lon"], row["max_lon"], row["min_lat"], row["max_lat"]

    lons = [min_lon, max_lon, max_lon, min_lon]
    lats = [min_lat, min_lat, max_lat, max_lat]

    geod = Geod(ellps="WGS84")
    area, _ = geod.polygon_area_perimeter(lons, lats)
    return abs(area) / 1e6 

city_list = list(pd.read_csv('City_list.csv')['city_name'])

for city_name in city_list:
    df = pd.read_csv(f"outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")

    df["area_km2"] = df.apply(bbox_area, axis=1)

    print(city_name, df.iloc[0]["area_km2"])

