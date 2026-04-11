import glob
import os
from pathlib import Path

import fiona
import geopandas as gpd
import pandas as pd

# Input Urban Atlas change packages. Keep the original unzip structure under this folder.
INPUT_GPKG_GLOB = 'unziped_files_LU_change/*/*/Data/*.gpkg'
# Output folder for the exported urban-core bbox CSV files.
OUTPUT_DIR = 'outputs/urbancore_bbox_dir'
WGS84 = 'EPSG:4326'


def main():
    gpkg_list = glob.glob(INPUT_GPKG_GLOB)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for gpkg_path in gpkg_list:
        city_name = Path(gpkg_path).parts[1]

        layers = fiona.listlayers(gpkg_path)
        urbancore_layers = [layer_name for layer_name in layers if 'urbancore' in layer_name.lower()]
        if not urbancore_layers:
            print(f'No urbancore layer found in {gpkg_path}')
            continue
        urban_boundary_layer_name = urbancore_layers[0]

        try:
            gdf_urban = gpd.read_file(gpkg_path, layer=urban_boundary_layer_name)

            if gdf_urban.crs != WGS84:
                gdf_urban = gdf_urban.to_crs(WGS84)

            union_geom = gdf_urban.unary_union
            minx, miny, maxx, maxy = union_geom.bounds

            df_bbox = pd.DataFrame(
                {
                    'identifier': ['urbancore'],
                    'min_lon': [minx],
                    'max_lon': [maxx],
                    'max_lat': [maxy],
                    'min_lat': [miny],
                }
            )

            output_csv_path = os.path.join(OUTPUT_DIR, f'{city_name}_urbancore_bbox.csv')
            df_bbox.to_csv(output_csv_path, index=False)

            print('export urbancore boundary done:', output_csv_path)
            print(df_bbox)

        except Exception as exc:
            print(f'error while processing {gpkg_path}: {exc}')


if __name__ == '__main__':
    main()
