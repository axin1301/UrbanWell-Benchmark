import geopandas as gpd
import fiona
import pandas as pd
import os
import sys
print(f"Python Path: {sys.executable}")
print(f"geopandas version: {gpd.__version__}")

import glob
from pathlib import Path

gpkg_list = glob.glob('unziped_files_LU_change/*/*/Data/*.gpkg')

for gpkg_path in gpkg_list:
    city_name = Path(gpkg_path).parts[1]

    layers = fiona.listlayers(gpkg_path)
    urbancore_layers = [ly for ly in layers if "urbancore" in ly.lower()]
    urban_boundary_layer_name = urbancore_layers[0]
    change_layer_name = min(layers, key=len)

    try:
        layers = fiona.listlayers(gpkg_path)
        if change_layer_name not in layers:
            print(f"Error: the specified layer '{change_layer_name}' is not in the file. Available layers: {layers}")
            exit()
        else:
            print(f"The following layer was found in file '{gpkg_path}':")
            print(f"- {change_layer_name}")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        exit()

    try:
        gdf_changes = gpd.read_file(gpkg_path, layer=change_layer_name)
        gdf_urban_boundary = gpd.read_file(gpkg_path, layer=urban_boundary_layer_name)

        wgs84 = "EPSG:4326"
        if gdf_changes.crs != wgs84:
            gdf_changes = gdf_changes.to_crs(wgs84)
        if gdf_urban_boundary.crs != wgs84:
            gdf_urban_boundary = gdf_urban_boundary.to_crs(wgs84)

        utm_crs = "EPSG:32635"
        gdf_changes_projected = gdf_changes.to_crs(utm_crs)
        gdf_changes_projected['centroid_geom'] = gdf_changes_projected.geometry.centroid
        gdf_changes['centroid_geom'] = gdf_changes_projected['centroid_geom'].to_crs(wgs84)

        gdf_centroids = gdf_changes.set_geometry('centroid_geom')
        centroids_in_urban = gpd.sjoin(gdf_centroids, gdf_urban_boundary, how="inner", predicate="within")

        result_gdf = centroids_in_urban.drop(columns=[col for col in gdf_urban_boundary.columns if col != 'geometry'] + ['index_right'])
        result_gdf['latitude'] = centroids_in_urban.geometry.y
        result_gdf['longitude'] = centroids_in_urban.geometry.x

        print(f"\nFound {len(result_gdf)} centroids within the Urban boundary.")

        os.makedirs('outputs/urbanchange_centroids_dir/', exist_ok=True)
        output_csv_path = 'outputs/urbanchange_centroids_dir/' + f"{city_name}_urban_filtered_centroids_wgs84.csv"
        result_gdf.to_csv(output_csv_path, index=False)

        print(f"\nSuccessfully saved centroid coordinates and all attributes within the Urban boundary to the new CSV file: '{output_csv_path}'")
        print("\nFile preview:")
        print(result_gdf.head())

    except FileNotFoundError:
        print(f"Error: file '{gpkg_path}' was not found. Please check whether the path is correct.")
    except ValueError as e:
        print("Error: an error occurred while reading the file or executing the operation.")
        print(f"Detailed error message: {e}")
    except Exception as e:
        print(f"An unknown error occurred: {e}")

