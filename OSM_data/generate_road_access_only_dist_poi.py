import geopandas as gpd
import networkx as nx
import osmnx as ox
import numpy as np
from shapely.geometry import Point, Polygon
from collections import Counter
from joblib import Parallel, delayed
import os
import pandas as pd
from shapely.geometry import box
from shapely.geometry import Point, LineString, MultiLineString
import tqdm

#
if not hasattr(np, "int"):
    np.int = int

def compute_accessibility_metrics_shp(region_bbox, roads_gdf, pois_gdf,poi_types):
    """
    in:
      region_bbox: (minx, miny, maxx, maxy)
      roads_gdf: GeoDataFrame, (EPSG:3857)
      pois_gdf: GeoDataFrame, POI (EPSG:3857)
    
    out:
      dict
    """
    
    # GeoSeries
    minx, miny, maxx, maxy = region_bbox
    region_poly_wgs = Polygon([
        (minx, miny), (maxx, miny),
        (maxx, maxy), (minx, maxy)
    ])
    region_gdf = gpd.GeoDataFrame(index=[0], geometry=[region_poly_wgs], crs="EPSG:4326")
    
    # ------------------ 
    # roads_gdf EPSG:3857
    region_gdf = region_gdf.to_crs(roads_gdf.crs)
    
    # 
    roads_within = gpd.clip(roads_gdf, region_gdf.geometry.iloc[0])

    # roads_within = gpd.clip(roads_gdf, region_poly)
    # if len(roads_within) == 0:
        # print("no road")

    total_edge_length_km = roads_within.length.sum() / 1000
    area_km2 = region_gdf.geometry.iloc[0].area / 1e6
    network_density = total_edge_length_km / area_km2 if area_km2>0 else 0
    
    # ------------------ road density ----------------
    all_points = []
    for geom in roads_within.geometry:
        if geom.geom_type == "LineString":
            all_points.extend([Point(geom.coords[0]), Point(geom.coords[-1])])
        elif geom.geom_type == "MultiLineString":
            for line in geom.geoms:
                all_points.extend([Point(line.coords[0]), Point(line.coords[-1])])
    nodes_gdf = gpd.GeoDataFrame(geometry=all_points).drop_duplicates()
    intersection_density = len(nodes_gdf) / area_km2 if area_km2>0 else 0

    # ------------------ POI ------------------
    total_pois = len(pois_gdf)
    poi_counts = Counter()

    for poi_type in poi_types:
        if "fclass" in pois_gdf.columns:
            poi_counts[poi_type] = pois_gdf[pois_gdf["fclass"] == poi_type].shape[0]
        else:
            poi_counts[poi_type] = 0

    # ------------------ dist to POI ------------------
    # pois_gdf, region_gdf EPSG:3857
    center = region_gdf.geometry.iloc[0].centroid
    avg_distances = {}
    for poi_type in poi_types:
        group = pois_gdf[pois_gdf["fclass"] == poi_type] if "fclass" in pois_gdf.columns else gpd.GeoDataFrame(columns=pois_gdf.columns)
        
        if len(group) > 0:
            distances_m = group.geometry.distance(center)  #  m
            avg_distances[poi_type] = distances_m.min() / 1000  # km
        else:
            avg_distances[poi_type] = None
    
    results = {
        "total_pois": total_pois,
        "pois_within": dict(poi_counts),
        "avg_distance_to_nearest_poi_by_type": avg_distances,
        "network_density_km_per_km2": network_density,
        "intersection_density_per_km2": intersection_density,
    }
    
    return results

if __name__ == "__main__":

    # year = 2022
    for year in range(2014,2025):
        # for year in [2023,2018,2022]:
        year_str = str(year - 2000 + 1) + "0101"
        zoom_level = 16
        date = f"{year}-07-31"

        city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
        new_row = {
            "city_name": "HELSINKI",
            "city_full_name": "New City Full Name",
            "province": "New Province",
            "note": "finland",
            "country_name": "finland"
        }

        new_row_df = pd.DataFrame([new_row])
        city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

        output_dir = 'accessability_output_only_POI'
        os.makedirs(output_dir, exist_ok=True)

        for i in tqdm.tqdm(range(len(city_csv))): 
            all_records = []
            city_name = city_csv.at[i, 'city_name']
            city_full_name = city_csv.at[i, 'city_full_name']
            province = city_csv.at[i, 'province']
            note = city_csv.at[i, 'note']
            country_name = city_csv.at[i, 'country_name']

            # if city_name == 'MADRID' or city_name == 'ROMA' or city_name == 'SARAJEVO' or city_name == 'WARSZAWA':
            #     continue
            # if city_name not in ['MADRID', 'ROMA', 'SARAJEVO', 'WARSZAWA']:
            #     continue

            if os.path.exists(f"{output_dir}/{city_name}_accessibility_metrics_{year_str}.csv"):
                continue

            #  place_name
            if os.path.exists(f"outputs/osm_raw_data/{city_full_name}-{year_str}-free.shp.zip"):
                place_name = city_full_name
            elif os.path.exists(f"outputs/osm_raw_data/{province.lower()}-{year_str}-free.shp.zip"):
                place_name = province.lower()
            elif os.path.exists(f"outputs/osm_raw_data/{country_name}-{year_str}-free.shp.zip"):
                place_name = country_name
            else:
                place_name = note

            road_shp = f"outputs/unzipped_osm_files/{place_name}-{year_str}-free_shp/gis_osm_roads_free_1.shp"
            if not os.path.exists(road_shp):
                continue
            poi_shp = f"outputs/processed_osm_data/{place_name}-{year_str}_poi_economic_only.shp"

            #
            roads_all = gpd.read_file(road_shp)
            pois_all = gpd.read_file(poi_shp)

            city_bound = pd.read_csv(f"../UrbanAtlas/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")

            minx, miny, maxx, maxy = city_bound.at[0,'lon'],city_bound.at[1,'lat'],city_bound.at[1,'lon'],city_bound.at[0,'lat']
            helsinki_bbox = box(minx, miny, maxx, maxy)

            roads_helsinki = gpd.clip(roads_all, helsinki_bbox).to_crs(epsg=3857)
            pois_helsinki = gpd.clip(pois_all, helsinki_bbox).to_crs(epsg=3857)
            roads_all = roads_helsinki
            poi_all = pois_helsinki

            # os.makedirs("output_geojson", exist_ok=True)

            # roads_helsinki.to_file(f"roads_{city_name}.geojson", driver="GeoJSON")
            # pois_helsinki.to_file(f"pois_{city_name}.geojson", driver="GeoJSON")

            destination_directory = (
                f"../download_sat/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}"
                + "/" + city_name + "/img_info/"
                )
            new_file_name = city_name + "_list1.txt"
            destination_file = os.path.join(destination_directory, new_file_name)

            df_img = pd.read_csv(destination_file, delim_whitespace=True)
            df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

            for _, img_row in df_img.iterrows():
                image_name = img_row["ImageFileName"]
                # if image_name != 'gesh_16815_21147_16.jpg':
                #     continue

                bbox = (
                    img_row['Left_Edge_Longitude'],
                    img_row['Bottom_Edge_Latitude'],
                    img_row['Right_Edge_Longitude'],
                    img_row['Top_Edge_Latitude']
                )

                poi_types = ["restaurant", "supermarket"] #,"hotel", "convenience"]

                # metrics = compute_accessibility_metrics(bbox, road_shp, poi_shp, G_full)
                metrics = compute_accessibility_metrics_shp(bbox, roads_all, poi_all,poi_types)

                row = {"image_name": image_name}

                #
                row.update({
                    "total_pois": metrics["total_pois"],
                    "network_density_km_per_km2": metrics["network_density_km_per_km2"],
                    "intersection_density_per_km2": metrics["intersection_density_per_km2"],
                })

                #
                for poi_type in poi_types:
                    row[f"poi_{poi_type}"] = metrics["pois_within"].get(poi_type, 0)

                #
                for poi_type in poi_types:
                    row[f"avg_dist_to_{poi_type}"] = metrics["avg_distance_to_nearest_poi_by_type"].get(poi_type, None)

                all_records.append(row)

            df_out = pd.DataFrame(all_records)
            df_out.to_csv(f"{output_dir}/{city_name}_accessibility_metrics_{year_str}.csv", index=False, encoding="utf-8")
            print("accessibility_metrics.csv done")