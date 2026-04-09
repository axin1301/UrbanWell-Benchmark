import geopandas as gpd
import numpy as np
from shapely.geometry import box
import pandas as pd
import os
import tqdm
from exclude_non_commercial_pois import *
# ====
def shannon_entropy(counts):
    p = counts / counts.sum()
    return -np.sum(p * np.log(p))

# ====
city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
new_row = {
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "finland"
}

#
new_row_df = pd.DataFrame([new_row])
#
city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

for i in range(len(city_csv)):  #
    city_name = city_csv.at[i, 'city_name']
    city_full_name = city_csv.at[i, 'city_full_name']
    province = city_csv.at[i, 'province']
    note = city_csv.at[i, 'note']
    country_name = city_csv.at[i, 'country_name']

    for year in range(2014,2025):
        # year = 2023
        year_str = str(year - 2000 + 1) + "0101"
        zoom_level = 16
        date = f"{year}-07-31"

        out_dir = 'outputs/output_economic_dir_update/'
        os.makedirs(out_dir, exist_ok=True)
        # if os.path.exists(os.path.join(out_dir, f"{city_name}_economic_urbancore_{year}.csv")):
        #     continue
        # åˆ¤æ–­ place_name
        if os.path.exists(f"outputs/osm_raw_data/{city_full_name}-{year_str}-free.shp.zip"):
            place_name = city_full_name
        elif os.path.exists(f"outputs/osm_raw_data/{province.lower()}-{year_str}-free.shp.zip"):
            place_name = province.lower()
        elif os.path.exists(f"outputs/osm_raw_data/{country_name}-{year_str}-free.shp.zip"):
            place_name = country_name
        else:
            place_name = note

        a = exclude_non_commercial_pois(place_name, year_str)
        if a == -1:
            continue
        
        poi_file = f"outputs/processed_osm_data/{place_name}-{year_str}_poi_economic_only.shp"
        if not os.path.exists(poi_file):
            continue
        pois = gpd.read_file(poi_file)

        if pois.crs is None or pois.crs.to_epsg() != 4326:
            pois = pois.to_crs(epsg=4326)

        pois_sindex = pois.sindex

        category_field = "fclass"
        
        economic_fclass = {
            "restaurant", "fast_food", "cafe", "bar", "pub",

            "supermarket", "convenience", "mall", "clothes", "shoes", "electronics", "jeweller",
            "bakery", "butcher", "florist", "bookshop",

            "hairdresser", "beauty_shop", "laundry", "repair", "photo",
            "travel_agent", "car_rental", "car_wash",

            "hotel", "motel", "guesthouse", "hostel", "camp_site",

            "cinema", "theatre", "museum", "gallery",
            "nightclub", "casino", "sports_centre", "fitness_centre"
        }


        input_csv = f"../UrbanAtlas/outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv"
        df_bbox = pd.read_csv(input_csv)
        rows_to_process = [0]

        results = []

        for idx in rows_to_process:
            row = df_bbox.loc[idx]
            identifier = city_name #str(row['identifier'])
            destination_directory = f'../download_sat/outputs/downloaded_sat_{year}_zoom_{zoom_level}/{identifier}/{date}/{identifier}/img_info/'
            new_file_name = identifier + "_list1.txt"
            destination_file = os.path.join(destination_directory, new_file_name)

            df_img = pd.read_csv(destination_file, delim_whitespace=True)
            df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

            for _, img_row in tqdm.tqdm(df_img.iterrows()):
                image_name = img_row['ImageFileName']
                lat_min = img_row['Bottom_Edge_Latitude']
                lat_max = img_row['Top_Edge_Latitude']
                lon_min = img_row['Left_Edge_Longitude']
                lon_max = img_row['Right_Edge_Longitude']

                bbox = box(lon_min, lat_min, lon_max, lat_max)

                candidate_idx = list(pois_sindex.intersection(bbox.bounds))
                pois_in_bbox = pois.iloc[candidate_idx]
                pois_in_bbox = pois_in_bbox[pois_in_bbox.intersects(bbox)]

                pois_in_bbox = pois_in_bbox[pois_in_bbox[category_field].isin(economic_fclass)]

                # Shannon entropy
                if len(pois_in_bbox) > 0:
                    counts = pois_in_bbox[category_field].value_counts()
                    diversity = shannon_entropy(counts)
                else:
                    diversity = 0

                results.append([identifier, image_name, diversity])

        # å†™ç»“æžœ
        df_out = pd.DataFrame(results, columns=['identifier', 'best_image_name', 'economic'])
        out_csvPath = os.path.join(out_dir, f"{city_name}_economic_urbancore_{year}.csv")
        df_out.to_csv(out_csvPath, index=False)


