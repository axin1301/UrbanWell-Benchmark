import numpy as np
import pandas as pd
import os

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

    df = pd.DataFrame(points)
    return df

# -----------------------------

city_list = list(pd.read_csv('../UrbanAtlas/City_list.csv')['city_name'])

for city_name in city_list[0:]:
    input_csv =f"../download_sat/outputs/Landuse_Change_2012_2018_urbancore/{city_name}_sat_image_landuse_change_2012_2018_urbancore.csv"
    output_dir = "outputs/generated_grid_points/"+city_name
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(input_csv)

    required_cols = ['fua_code', 'Left_Edge_Longitude', 'Bottom_Edge_Latitude',
                    'Right_Edge_Longitude', 'Top_Edge_Latitude']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"{missing_cols}")

    num_rows = 5  #
    num_cols = 5  #

    rows_to_process = list(range(0,len(df)))

    for idx in rows_to_process:
        row = df.loc[idx]
        image_name = str(row['fua_code'])
        
        top_left_coord = (row['Left_Edge_Longitude'], row['Top_Edge_Latitude'])
        top_right_coord = (row['Right_Edge_Longitude'], row['Top_Edge_Latitude'])
        bottom_left_coord = (row['Left_Edge_Longitude'], row['Bottom_Edge_Latitude'])
        bottom_right_coord = (row['Right_Edge_Longitude'], row['Bottom_Edge_Latitude'])
        
        grid_df = generate_grid_points(
            top_left_coord, 
            top_right_coord, 
            bottom_left_coord, 
            bottom_right_coord,
            num_rows,
            num_cols
        )
        
        output_csv_path = os.path.join(output_dir, f"{image_name}.csv")
        grid_df.to_csv(output_csv_path, index=False)
        
        print(f"{num_rows}x{num_cols} points to {output_csv_path}")

