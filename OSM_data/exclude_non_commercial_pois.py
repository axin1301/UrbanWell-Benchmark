import geopandas as gpd
import os
import zipfile
import pandas as pd


def exclude_non_commercial_pois(place_name, year_str):
    if not os.path.exists(f"outputs/processed_osm_data/{place_name}-"+year_str+"_poi_economic_only.shp"):
        zip_path = f"outputs/osm_raw_data/{place_name}-"+year_str+"-free.shp.zip"        # ZIP
        if not os.path.exists(zip_path):
            print(zip_path)
            return -1
        extract_dir = f"outputs/unzipped_osm_files/{place_name}-"+year_str+"-free_shp"  #

        os.makedirs(extract_dir, exist_ok=True)

        print(zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # gdf = gpd.read_file(f"unzipped_osm_files/{place_name}-"+year_str+"-free_shp/gis_osm_pois_a_free_1.shp")
        gdf1 = gpd.read_file(f"outputs/unzipped_osm_files/{place_name}-"+year_str+"-free_shp/gis_osm_pois_a_free_1.shp")
        gdf2 = gpd.read_file(f"outputs/unzipped_osm_files/{place_name}-"+year_str+"-free_shp/gis_osm_pois_free_1.shp")
        gdf = pd.concat([gdf1, gdf2], ignore_index=True)

        economic_fclass = [
        # --- 
        "restaurant", "fast_food", "cafe", "bar", "pub",
        # --- 
        "supermarket", "convenience", "mall", "clothes", "shoes", "electronics", "jeweller",
        "bakery", "butcher", "florist", "bookshop",
        # --- 
        "hairdresser", "beauty_shop", "laundry", "repair", "photo",
        "travel_agent", "car_rental", "car_wash",
        # --- 
        "hotel", "motel", "guesthouse", "hostel", "camp_site",
        # --- 
        "cinema", "theatre", "museum", "gallery",
        "nightclub", "casino", "sports_centre", "fitness_centre"
    ]

        gdf_filtered = gdf[gdf["fclass"].isin(economic_fclass)]
        gdf_filtered["geometry"] = gdf_filtered["geometry"].centroid

        gdf_filtered.to_file(f"outputs/processed_osm_data/{place_name}-"+year_str+"_poi_economic_only.shp")
        return 1