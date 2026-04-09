import rasterio
import numpy as np
from rasterio.windows import from_bounds
import pandas as pd
import os
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
from rasterio.crs import CRS

def reproject_raster_to_memory(input_path, dst_crs="EPSG:4326"):
    with rasterio.open(input_path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        kwargs = src.meta.copy()
        kwargs.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        dest = np.zeros((src.count, height, width), dtype=src.dtypes[0])

        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=dest[i - 1],
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest
            )

    return dest, kwargs

city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
new_row = {
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "New Country"
}

#DataFrame
new_row_df = pd.DataFrame([new_row])

#DataFrame
city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

failed_country_list = []
for i in range(len(city_csv)-1,len(city_csv)):
    city_name = city_csv.at[i, 'city_name']
    city_full_name = city_csv.at[i, 'city_full_name']
    province = city_csv.at[i, 'province']
    note = city_csv.at[i, 'note']
    country_name = city_csv.at[i, 'country_name']
    country_code = city_csv.at[i, 'country_code']

    for year in range(2014,2024):
        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16
        year_in_dir = year - 2000

        tif_file = f"outputs/eea_raw_data/ODIAC/odiac2024_1km_excl_intl_{year_in_dir}07.tif/odiac2024_1km_excl_intl_{year_in_dir}07.tif"
        print(tif_file)
        if not os.path.exists(tif_file):
            failed_country_list.append(country_name)
            continue
        input_csv = f"../UrbanAtlas/outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv"
        df_bbox = pd.read_csv(input_csv)
        rows_to_process = [0]

        out_dir = f'outputs/generated_CO2/{city_name}'
        os.makedirs(out_dir, exist_ok=True)
        df_columns = ["ImageFileName", 'CO2_mean']
        data_arr = []

        with rasterio.open(tif_file) as src:
            if src.crs != CRS.from_string("EPSG:4326"):
                raise ValueError(f"{src.crs}")

            for idx in rows_to_process:
                row = df_bbox.loc[idx]
                identifier = city_name

                destination_directory = (
                    f'../download_sat/outputs/downloaded_sat_{year}_zoom_{zoom_level}/'
                    f'{identifier}/{date}/{identifier}/img_info/'
                )
                new_file_name = identifier + "_list1.txt"
                destination_file = os.path.join(destination_directory, new_file_name)

                df_img = pd.read_csv(destination_file, delim_whitespace=True)
                df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

                for _, img_row in df_img.iterrows():
                    image_name = img_row['ImageFileName']
                    lat_min = img_row['Bottom_Edge_Latitude']
                    lat_max = img_row['Top_Edge_Latitude']
                    lon_min = img_row['Left_Edge_Longitude']
                    lon_max = img_row['Right_Edge_Longitude']

                    window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)

                    data = src.read(1, window=window)

                    data = np.where(data < 0, np.nan, data)

                    non_zero_data = data[data != 0]

                    mean_CO2 = np.nanmean(non_zero_data)

                    data_arr.append([image_name, mean_CO2])

        # ====CSV ====
        df_out = pd.DataFrame(data_arr, columns=df_columns)
        out_csvPath = os.path.join(out_dir, f"{city_name}_CO2_{year}.csv")
        df_out.to_csv(out_csvPath, index=False)

print(set(failed_country_list))
