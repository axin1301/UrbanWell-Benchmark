import geopandas as gpd
import pandas as pd
import fiona
from pathlib import Path
import glob
import os

gpkg_list = glob.glob('unziped_files_LU_change/*/*/Data/*.gpkg')

for gpkg_path in gpkg_list:
    city_name = Path(gpkg_path).parts[1]

    layers = fiona.listlayers(gpkg_path)
    urbancore_layers = [ly for ly in layers if "urbancore" in ly.lower()]
    urban_boundary_layer_name = urbancore_layers[0]

    try:
        gdf_urban = gpd.read_file(gpkg_path, layer=urban_boundary_layer_name)

        wgs84 = "EPSG:4326"
        if gdf_urban.crs != wgs84:
            gdf_urban = gdf_urban.to_crs(wgs84)

        union_geom = gdf_urban.unary_union
        minx, miny, maxx, maxy = union_geom.bounds

        bbox_coords = {
            "identifier": ["urbancore"],
            "min_lon": [minx],
            "max_lon": [maxx],
            "max_lat": [maxy],
            "min_lat": [miny],
        }
        df_bbox = pd.DataFrame(bbox_coords)

        os.makedirs('outputs/urbancore_bbox_dir/', exist_ok=True)
        output_csv_path = f"outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv"
        df_bbox.to_csv(output_csv_path, index=False)

        print("export urbancore boundary done：", output_csv_path)
        print(df_bbox)

    except Exception as e:
        print(f"error: {e}")
