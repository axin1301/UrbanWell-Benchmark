import numpy as np
import pandas as pd
import os
import xarray as xr
import tqdm
import shutil
import glob, os
import rasterio
import numpy as np

import rasterio
import numpy as np
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.crs import CRS

class TifStats:
    def __init__(self, tif_path, assume_input_crs="EPSG:4326", read_full=False):

        self.src = rasterio.open(tif_path)
        self.nodata = self.src.nodata
        self.input_crs = assume_input_crs
        self.read_full = read_full
        if read_full:
            self._arr = self.src.read(1)  # 
        else:
            self._arr = None

    def _bbox_to_window(self, lon_min, lon_max, lat_min, lat_max):

        src_crs = self.src.crs

        if src_crs and src_crs.to_string() != self.input_crs:
            lon_min, lat_min, lon_max, lat_max = transform_bounds(
                CRS.from_string(self.input_crs), src_crs,
                lon_min, lat_min, lon_max, lat_max, densify_pts=21
            )

        window = from_bounds(lon_min, lat_min, lon_max, lat_max, self.src.transform)

        if (
            window.row_off >= self.src.height
            or window.col_off >= self.src.width
            or window.row_off + window.height <= 0
            or window.col_off + window.width <= 0
        ):
            return None

        return window

    def get_mean(self, min_lon, max_lon, min_lat, max_lat):

        window = self._bbox_to_window(min_lon, max_lon, min_lat, max_lat)
        if window is None:
            return np.nan

        if self._arr is not None:
            row = int(np.floor(window.row_off))
            col = int(np.floor(window.col_off))
            h = int(np.ceil(window.height))
            w = int(np.ceil(window.width))
            arr = self._arr[row:row+h, col:col+w]
        else:
            arr = self.src.read(1, window=window)

        if self.nodata is not None:
            arr = arr[arr != self.nodata]

        return float(arr.mean()) if arr.size > 0 else np.nan

    def close(self):
        self.src.close()

# eea_r_3035_1_km_aq-interpolated-NO2_p_2017_v01_r00\eea_r_3035_1_km_aq-interpolated-NO2_p_2017_v01_r00\EEA_1kmgrid_2017_no2_avg.tif

city_csv = pd.read_csv('../UrbanAtlas/City_list.csv')
new_row = {
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "New Country"
}


new_row_df = pd.DataFrame([new_row])

city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)
city_list = list(city_csv['city_name'])

for city_name in tqdm.tqdm(city_list):
    output_dir = "outputs/generated_PM25/"+city_name
    os.makedirs(output_dir, exist_ok=True)
    # year = 2018
    for year in [2014,2015,2016,2018,2019,2020,2022,2023]:#[2017,2021,2024]:
        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16
        identifier = city_name

        if os.path.exists(os.path.join(output_dir, f"/{city_name}_PM25_{year}.csv")):
            continue
        
        # if year == 2017:
        #     tif_path = f"outputs/eea_raw_data/EEA/\eea_r_3035_1_km_aq-interpolated-pm25_p_2017_v01_r00\\eea_r_3035_1_km_aq-interpolated-pm25_p_2017_v01_r00\\EEA_1kmgrid_2017_pm25_avg.tif"
        # elif year == 2021:
        #     tif_path = tif_path = f"outputs/eea_raw_data/EEA/\eea_r_3035_1_km_aq-interpolated-pm25_p_2021_v01_r00\\eea_r_3035_1_km_aq-interpolated-pm25_p_2021_v01_r00\\EEA_1kmgrid_2021_pm25_avg.tif"
        # elif year == 2024:
        #     tif_path = f"outputs/eea_raw_data/EEA/\eea_r_3035_1_km_aq-interpolated-pm25_p_2024_v00_r00\\eea_r_3035_1_km_aq-interpolated-pm25_p_2024_v00_r00\\pm25_avg24_int.tif"

        tif_path_list = glob.glob(f"outputs/eea_raw_data/EEA/eea_r_3035_1_km_aq-interpolated-pm25_p_{year}_v*/eea_r_3035_1_km_aq-interpolated-pm25_p_{year}_v*/*.tif")
        tif_path = tif_path_list[0]

        ts = TifStats(tif_path)

        destination_directory = (
            f"../download_sat/outputs/downloaded_sat_{year}_zoom_{zoom_level}/{identifier}/{date}"
            + "/" + identifier + "/img_info/"
        )
        new_file_name = identifier + "_list1.txt"
        destination_file = os.path.join(destination_directory, new_file_name)

        df_img = pd.read_csv(destination_file, delim_whitespace=True)
        df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

        results = []

        for _, img_row in df_img.iterrows():
            image_name = img_row["ImageFileName"]
            # if image_name in already_done_image_list:
            #     continue
            # # -----------------------------

            min_lon = min(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            max_lon = max(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            min_lat = min(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])
            max_lat = max(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])

            mean_val = ts.get_mean(min_lon, max_lon, min_lat, max_lat)

            results.append({
                "ImageFileName": image_name,
                "PM25_value": mean_val
            })

        ts.close()

        df_out = pd.DataFrame(results)
        df_out.to_csv(output_dir + f"/{city_name}_PM25_{year}.csv", index=False)

### ------------------------------------------------------------------------------------------------------------------------------

for city_name in tqdm.tqdm(city_list):
    output_dir = "outputs/generated_PM25/"+city_name
    os.makedirs(output_dir, exist_ok=True)
    # year = 2018
    for year in [2017,2021,2024]:
        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16
        identifier = city_name

        if os.path.exists(os.path.join(output_dir, f"/{city_name}_PM25_{year}.csv")):
            continue
        
        if year == 2017:
            tif_path = f"outputs/eea_raw_data/EEA/eea_r_3035_1_km_aq-interpolated-pm25_p_2017_v01_r00/eea_r_3035_1_km_aq-interpolated-pm25_p_2017_v01_r00/EEA_1kmgrid_2017_pm25_avg.tif"
        elif year == 2021:
            tif_path = tif_path = f"outputs/eea_raw_data/EEA/eea_r_3035_1_km_aq-interpolated-pm25_p_2021_v01_r00/eea_r_3035_1_km_aq-interpolated-pm25_p_2021_v01_r00/EEA_1kmgrid_2021_pm25_avg.tif"
        elif year == 2024:
            tif_path = "outputs/eea_raw_data/EEA/eea_r_3035_1_km_aq-interpolated-pm25_p_2024_v00_r00/eea_r_3035_1_km_aq-interpolated-pm25_p_2024_v00_r00/pm25_avg24_int.tif"

        # tif_path_list = glob.glob(f"outputs/eea_raw_data/EEA/\eea_r_3035_1_km_aq-interpolated-pm25_p_{year}_v*\\eea_r_3035_1_km_aq-interpolated-pm25_p_{year}_v*/*.tif")
        # tif_path = tif_path_list[0]

        ts = TifStats(tif_path)
        if city_name == 'HELSINKI':
            identifier = 'urbancore'

        destination_directory = (
            f"../download_sat/outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier}\\{date}"
            + "/" + identifier + "/img_info/"
        )
        new_file_name = identifier + "_list1.txt"
        destination_file = os.path.join(destination_directory, new_file_name)

        df_img = pd.read_csv(destination_file, delim_whitespace=True)
        df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

        results = []

        for _, img_row in df_img.iterrows():
            image_name = img_row["ImageFileName"]
            # if image_name in already_done_image_list:
            #     continue
            # # -----------------------------

            min_lon = min(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            max_lon = max(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            min_lat = min(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])
            max_lat = max(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])

            mean_val = ts.get_mean(min_lon, max_lon, min_lat, max_lat)

            results.append({
                "ImageFileName": image_name,
                "PM25_value": mean_val
            })

        ts.close()

        df_out = pd.DataFrame(results)
        df_out.to_csv(output_dir + f"/{city_name}_PM25_{year}.csv", index=False)

