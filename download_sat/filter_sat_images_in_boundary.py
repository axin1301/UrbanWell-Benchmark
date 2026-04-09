import pandas as pd
import numpy as np
import tqdm
import os

def is_small_box_well_inside(
    left_longitude, right_longitude, bottom_latitude, top_latitude,
    lon_min, lon_max, lat_min, lat_max
):

    box_width = lon_max - lon_min
    box_height = lat_max - lat_min

    inside = (
        (lon_min >= left_longitude) and
        (lon_max <= right_longitude) and
        (lat_min >= bottom_latitude) and
        (lat_max <= top_latitude)
    )

    margin_ok = (
        (lon_min - left_longitude   >= box_width)  and
        (right_longitude - lon_max  >= box_width)  and
        (lat_min - bottom_latitude  >= box_height) and
        (top_latitude - lat_max     >= box_height)
    )

    return inside and margin_ok

city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
new_row = {
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "New Country"
}

new_row_df = pd.DataFrame([new_row])

city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

valid_sat_image_list = []

for i in tqdm.tqdm(range(len(city_csv))): 
    city_name = city_csv.at[i, 'city_name']

    city_bound = pd.read_csv(f"../UrbanAtlas/outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")
    identifier = city_name

    city_bound_one = city_bound.iloc[0]
    left_longitude = city_bound_one['min_lon']
    right_longitude = city_bound_one['max_lon']
    top_latitude = city_bound_one['max_lat']
    bottom_latitude = city_bound_one['min_lat']
    
    # area_identifier = city_bound_one['identifier']

    year = 2023
    zoom_level = 16
    date = f"{year}-07-31"
    destination_directory = (
        f"outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier}\\{date}" + "/" + identifier + "/img_info/")
    new_file_name = identifier + "_list1.txt"
    destination_file = os.path.join(destination_directory, new_file_name)

    df_img = pd.read_csv(destination_file, delim_whitespace=True)
    df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

    for _, img_row in df_img.iterrows():
        image_name = img_row["ImageFileName"]
        lat_min = img_row["Bottom_Edge_Latitude"]
        lat_max = img_row["Top_Edge_Latitude"]
        lon_min = img_row["Left_Edge_Longitude"]
        lon_max = img_row["Right_Edge_Longitude"]

        check_result = is_small_box_well_inside(
            left_longitude, right_longitude, bottom_latitude, top_latitude,
            lon_min, lon_max, lat_min, lat_max
        )

        if check_result:
            valid_sat_image_list.append(image_name)

pd_dict = pd.DataFrame({'valid_image_name': valid_sat_image_list})
os.makedirs('outputs/valid_image_lists', exist_ok=True)
pd_dict.to_csv('outputs/valid_image_lists/valid_image_lists.csv', index = False) ### filters out the images on the boundary



