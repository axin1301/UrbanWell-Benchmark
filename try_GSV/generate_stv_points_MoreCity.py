import os

import numpy as np
import pandas as pd

# Upstream files from UrbanAtlas and download_sat.
CITY_LIST_PATH = '../UrbanAtlas/City_list.csv'
LANDUSE_CHANGE_DIR = '../download_sat/outputs/Landuse_Change_2012_2018_urbancore'
# Output folder storing one grid-point CSV per selected satellite-image region.
OUTPUT_ROOT = 'outputs/generated_grid_points'
NUM_ROWS = 5
NUM_COLS = 5


def generate_grid_points(top_left, top_right, bottom_left, bottom_right, rows, cols):
    lon_start = top_left[0]
    lon_end = top_right[0]
    lat_start = top_left[1]
    lat_end = bottom_left[1]

    lons = np.linspace(lon_start, lon_end, cols)
    lats = np.linspace(lat_start, lat_end, rows)

    points = []
    for lat in lats:
        for lon in lons:
            points.append({'longitude': lon, 'latitude': lat})

    return pd.DataFrame(points)


def main():
    city_list = list(pd.read_csv(CITY_LIST_PATH)['city_name'])

    for city_name in city_list:
        input_csv = os.path.join(
            LANDUSE_CHANGE_DIR,
            f'{city_name}_sat_image_landuse_change_2012_2018_urbancore.csv',
        )
        output_dir = os.path.join(OUTPUT_ROOT, city_name)
        os.makedirs(output_dir, exist_ok=True)

        if not os.path.exists(input_csv):
            print(f'Missing input file: {input_csv}')
            continue

        df = pd.read_csv(input_csv)
        required_cols = [
            'fua_code',
            'Left_Edge_Longitude',
            'Bottom_Edge_Latitude',
            'Right_Edge_Longitude',
            'Top_Edge_Latitude',
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(str(missing_cols))

        for _, row in df.iterrows():
            image_name = str(row['fua_code'])
            grid_df = generate_grid_points(
                (row['Left_Edge_Longitude'], row['Top_Edge_Latitude']),
                (row['Right_Edge_Longitude'], row['Top_Edge_Latitude']),
                (row['Left_Edge_Longitude'], row['Bottom_Edge_Latitude']),
                (row['Right_Edge_Longitude'], row['Bottom_Edge_Latitude']),
                NUM_ROWS,
                NUM_COLS,
            )

            output_csv_path = os.path.join(output_dir, f'{image_name}.csv')
            grid_df.to_csv(output_csv_path, index=False)
            print(f'{NUM_ROWS}x{NUM_COLS} points to {output_csv_path}')


if __name__ == '__main__':
    main()
