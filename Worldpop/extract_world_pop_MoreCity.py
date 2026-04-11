import os

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds

# Upstream metadata and satellite image list files.
CITY_TABLE_PATH = '../UrbanAtlas/European_Countries_VS_Cities.csv'
DOWNLOAD_SAT_OUTPUT_ROOT = '../download_sat/outputs'
WORLDPOP_RASTER_DIR = 'outputs/worldpop_rasters'
OUTPUT_DIR = 'outputs/output_popu_dir'
YEARS = range(2014, 2021)
ZOOM_LEVEL = 16
DATE_TEMPLATE = '{year}-07-31'


def main():
    city_csv = pd.read_csv(CITY_TABLE_PATH)
    failed_country_list = []
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(len(city_csv)):
        city_name = city_csv.at[i, 'city_name']
        country_name = city_csv.at[i, 'country_name']
        country_code = city_csv.at[i, 'country_code']

        for year in YEARS:
            tif_file = os.path.join(WORLDPOP_RASTER_DIR, f'{country_code}_ppp_{year}_UNadj.tif')
            if not os.path.exists(tif_file):
                failed_country_list.append(country_name)
                continue

            out_csv_path = os.path.join(OUTPUT_DIR, f'{city_name}_ppp_{year}.csv')
            if os.path.exists(out_csv_path):
                continue

            date = DATE_TEMPLATE.format(year=year)
            destination_directory = os.path.join(
                DOWNLOAD_SAT_OUTPUT_ROOT,
                f'downloaded_sat_{year}_zoom_{ZOOM_LEVEL}',
                city_name,
                date,
                city_name,
                'img_info',
            )
            destination_file = os.path.join(destination_directory, f'{city_name}_list1.txt')
            if not os.path.exists(destination_file):
                print(f'Missing satellite list file: {destination_file}')
                continue

            with rasterio.open(tif_file) as src:
                if not src.crs.is_geographic:
                    raise ValueError(f'Unexpected CRS: {src.crs}')

                df_img = pd.read_csv(destination_file, delim_whitespace=True)
                df_img['ImageFileName'] = df_img['ImageFileName'].str.replace(':', '', regex=False)

                data_arr = []
                for _, img_row in df_img.iterrows():
                    image_name = img_row['ImageFileName']
                    lat_min = img_row['Bottom_Edge_Latitude']
                    lat_max = img_row['Top_Edge_Latitude']
                    lon_min = img_row['Left_Edge_Longitude']
                    lon_max = img_row['Right_Edge_Longitude']

                    window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
                    data = src.read(1, window=window)
                    data = np.where(data < 0, np.nan, data)
                    total_population = np.nansum(data)
                    data_arr.append([city_name, image_name, total_population])

                df_out = pd.DataFrame(data_arr, columns=['identifier', 'best_image_name', 'population'])
                df_out.to_csv(out_csv_path, index=False)

    print(set(failed_country_list))


if __name__ == '__main__':
    main()
