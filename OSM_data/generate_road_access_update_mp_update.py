import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point, box
from geopy.distance import geodesic
from pyproj import Geod
from collections import Counter
from sklearn.neighbors import BallTree
import os
import tqdm

GEOD = Geod(ellps='WGS84')

# ==============================

def calculate_geodesic_length(geom):
    if geom.is_empty:
        return 0.0
    return GEOD.geometry_length(geom)

def calculate_geodesic_area(polygon):
    if polygon.is_empty:
        return 0.0
    area, _ = GEOD.geometry_area_perimeter(polygon)
    return abs(area)


# ==============================

def compute_accessibility_metrics_fast(
    bbox, roads_city, pois_city, poi_trees, poi_types
):
    """
    for each region
    - road length km
    - road density km/km2

    """

    GEOD = Geod(ellps="WGS84")

    l, b, r, t = bbox
    region_poly = box(l, b, r, t)
    roads_small = gpd.clip(roads_city, region_poly)

    roads_small['length_m'] = roads_small.geometry.apply(calculate_geodesic_length)

    total_road_m = roads_small['length_m'].sum()
    total_road_km = total_road_m / 1000

    area_m2, _ = GEOD.geometry_area_perimeter(region_poly)
    area_km2 = abs(area_m2) / 1e6 if area_m2 != 0 else np.nan

    network_density = total_road_km / area_km2 if area_km2 and area_km2 > 0 else np.nan

    idx = list(pois_city.sindex.intersection(region_poly.bounds))
    pois_small = pois_city.iloc[idx]

    poi_counts = {
        poi_type: pois_small[pois_small["fclass"] == poi_type].shape[0]
        for poi_type in poi_types
    }

    # =====================

    center = region_poly.centroid
    center_rad = np.radians([[center.y, center.x]])

    avg_distances = {}
    for t in poi_types:
        tree = poi_trees.get(t)
        if tree is None:
            avg_distances[t] = np.nan
            continue
        dist_rad, _ = tree.query(center_rad, k=1)
        distance_m = dist_rad[0][0] * 6371000
        avg_distances[t] = distance_m / 1000  # km

    return {
        "total_pois": len(pois_small),
        "pois_within": poi_counts,
        "avg_distance_to_nearest_poi_by_type": avg_distances,
        "road_length": total_road_km,
        "network_density_km_per_km2": network_density,
        "intersection_density_per_km2": -1, #intersection_density,
    }

def preprocess_city(roads_all, pois_all, city_bbox):

    GEOD = Geod(ellps="WGS84")

    city_poly = box(*city_bbox)
    print("processing")
    roads_city = gpd.clip(roads_all, city_poly)
    pois_city = gpd.clip(pois_all, city_poly)

    poi_trees = {}
    for t in pois_city["fclass"].unique():
        subset = pois_city[pois_city["fclass"] == t]
        if len(subset) == 0:
            poi_trees[t] = None
            continue
        coords = np.radians(np.vstack([subset.geometry.y, subset.geometry.x]).T)
        poi_trees[t] = BallTree(coords, metric="haversine")

    return roads_city, pois_city, poi_trees


if __name__ == "__main__":

    old_images_names = list(pd.read_csv('urbanform_images.csv')['image_name'])
    old_images_names.append('gesh_16831_21140_16.jpg')

    for year in range(2014, 2025):
    # for year in [2021]:
        year_str = str(year - 2000 + 1) + "0101"
        zoom_level = 16
        date = f"{year}-07-31"
        # 
        city_csv = pd.read_csv("../UrbanAtlas/European_Countries_VS_Cities.csv")

        os.makedirs("road-output", exist_ok=True)

        for i in tqdm.tqdm(range(len(city_csv))):
            all_records = []
            city_name = city_csv.at[i, 'city_name']
            city_full_name = city_csv.at[i, 'city_full_name']
            province = city_csv.at[i, 'province']
            note = city_csv.at[i, 'note']
            country_name = city_csv.at[i, 'country_name']

            if os.path.exists(f"road-output/{city_name}_{year_str}.csv"):
                continue

            if city_name == 'MADRID' and year<=2020:
                continue

            if os.path.exists(f"outputs/osm_raw_data/{city_full_name}-{year_str}-free.shp.zip"):
                place_name = city_full_name
            elif os.path.exists(f"outputs/osm_raw_data/{province.lower()}-{year_str}-free.shp.zip"):
                place_name = province.lower()
            elif os.path.exists(f"outputs/osm_raw_data/{country_name}-{year_str}-free.shp.zip"):
                place_name = country_name
            else:
                place_name = note

            if place_name in ['centro', 'mazowieckie'] and year == 2014:
                continue

            # if os.path.exists(f"outputs/unzipped_osm_files/{place_name}-{year_str}-free_shp/gis_osm_roads_free_1.shp"):
            #     road_shp = f"outputs/unzipped_osm_files/{place_name}-{year_str}-free_shp/gis_osm_roads_free_1.shp"
            # else:
            road_shp = f"outputs/unzipped_osm_files/{place_name}-{year_str}-free_shp/gis_osm_roads_free_1.shp"
            poi_shp = f"outputs/processed_osm_data/{place_name}-{year_str}_poi_economic_only.shp"

            if city_name == 'AMSTERDAM' and year == 2021:
                road_shp = f"outputs/economic_previous/noord-holland-{year_str}-free_shp/gis_osm_roads_free_1.shp"
                poi_shp = f"outputs/processed_osm_data/noord-holland-{year_str}_poi_economic_only.shp"

            roads_all = gpd.read_file(road_shp).to_crs(4326)
            pois_all = gpd.read_file(poi_shp).to_crs(4326)

            # BBOX
            city_bound = pd.read_csv(f"../UrbanAtlas/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")
            
            city_bbox = (
                city_bound.at[0, "lon"],
                city_bound.at[1, "lat"],
                city_bound.at[1, "lon"],
                city_bound.at[0, "lat"],
            )

            roads_city, pois_city, pois_tree = preprocess_city(
                roads_all, pois_all, city_bbox
            )

            destination_directory = (
                f"../download_sat/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}"
                + "/" + city_name + "/img_info/"
            )
            new_file_name = city_name + "_list1.txt"
            destination_file = os.path.join(destination_directory, new_file_name)

            df_img = pd.read_csv(destination_file, delim_whitespace=True)
            df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

            poi_types = ["restaurant", "supermarket"] #, "hotel", "convenience"]

            all_records = []

            for _, row in tqdm.tqdm(df_img.iterrows()):
                if row["ImageFileName"] not in old_images_names:
                    continue

                bbox = (
                    row['Left_Edge_Longitude'],
                    row['Bottom_Edge_Latitude'],
                    row['Right_Edge_Longitude'],
                    row['Top_Edge_Latitude']
                )

                metrics = compute_accessibility_metrics_fast(
                    bbox, roads_all, pois_city, pois_tree, poi_types
                )

                out = {"image_name": row["ImageFileName"]}
                out.update(metrics["pois_within"])
                for t in poi_types:
                    out[f"avg_dist_to_{t}"] = metrics["avg_distance_to_nearest_poi_by_type"][t]
                out["road_length"] = metrics["road_length"]
                out["network_density_km_per_km2"] = metrics["network_density_km_per_km2"]
                # out["intersection_density_per_km2"] = metrics["intersection_density_per_km2"]

                all_records.append(out)

            pd.DataFrame(all_records).to_csv(
                f"road-output/{city_name}_{year_str}_update.csv",
                index=False
            )
            print(f"saved {city_name}")