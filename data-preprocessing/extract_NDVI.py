import numpy as np
import pandas as pd
import os
import xarray as xr
import tqdm
# -----------------------------
# 读取 CSV
# -----------------------------
import shutil
import glob, os

base_dir = "D:/CitySense原始数据/EEA"
folders = [
    f for f in glob.glob(os.path.join(base_dir, "*/"))
    if os.path.basename(os.path.normpath(f)).isdigit() 
    and len(os.path.basename(os.path.normpath(f))) == 5
]

print(folders)

dfs_2018 = []
for ddir in folders:
    src = ddir + "\\Results\\Normalised Difference Vegetation Index 2014-2020 (raster 300 m), global, 10-daily – version 1\\c_gls_NDVI300_201807110000_GLOBE_PROBAV_V1.0.1__NDVI.nc"
    if not os.path.exists(src):
        src = ddir + "\\Results\\Normalised Difference Vegetation Index 2014-2020 (raster 300 m), global, 10-daily – version 1\\c_gls_NDVI300_201808110000_GLOBE_PROBAV_V1.0.1__NDVI.nc"
    if not os.path.exists(src):
        continue
    
    ds = xr.open_dataset(src, engine="scipy")
    df = ds['NDVI'].to_dataframe().reset_index()
    dfs_2018.append(df)
    # 拼接
df_all_2018 = pd.concat(dfs_2018, ignore_index=True)

# dfs_2020 = []
# for ddir in folders:
#     src = ddir + "\\Results\\Normalised Difference Vegetation Index 2014-2020 (raster 300 m), global, 10-daily – version 1\\c_gls_NDVI300_202007110000_GLOBE_PROBAV_V1.0.1__NDVI.nc"
#     if not os.path.exists(src):
#         src = ddir + "\\Results\\Normalised Difference Vegetation Index 2014-2020 (raster 300 m), global, 10-daily – version 1\\c_gls_NDVI300_202008110000_GLOBE_PROBAV_V1.0.1__NDVI.nc"
#     if not os.path.exists(src):
#         continue
    
#     ds = xr.open_dataset(src, engine="scipy")
#     df = ds['NDVI'].to_dataframe().reset_index()
#     dfs_2020.append(df)
#     # 拼接
# df_all_2020 = pd.concat(dfs_2020, ignore_index=True)

# dfs_2024 = []
# for ddir in folders:
#     # ds = xr.open_dataset()#, engine="netcdf4"
#     src = ddir + "\\Results\\Normalised Difference Vegetation Index 2020-present (raster 300 m), global, 10-daily – version 2\\c_gls_NDVI300_202407110000_GLOBE_OLCI_V2.0.1__NDVI.nc"
#     if not os.path.exists(src):
#         src = ddir + "\\Results\\Normalised Difference Vegetation Index 2020-present (raster 300 m), global, 10-daily – version 2\\c_gls_NDVI300_202408110000_GLOBE_OLCI_V2.0.1__NDVI.nc"
#     if not os.path.exists(src):
#         continue

#     dst = r"D:\\temp_nc\\ndvi.nc"

#     os.makedirs(r"D:\\temp_nc", exist_ok=True)
#     shutil.copy(src, dst)

#     ds = xr.open_dataset(dst, engine="netcdf4")

#     df = ds['NDVI'].to_dataframe().reset_index()
#     dfs_2024.append(df)
#     # 拼接
# df_all_2024 = pd.concat(dfs_2024, ignore_index=True)

dfs_2022 = []
for ddir in folders:
    # ds = xr.open_dataset()#, engine="netcdf4"
    src = ddir + "\\Results\\Normalised Difference Vegetation Index 2020-present (raster 300 m), global, 10-daily – version 2\\c_gls_NDVI300_202207110000_GLOBE_OLCI_V2.0.2__NDVI.nc"
    if not os.path.exists(src):
        src = ddir + "\\Results\\Normalised Difference Vegetation Index 2020-present (raster 300 m), global, 10-daily – version 2\\c_gls_NDVI300_202208110000_GLOBE_OLCI_V2.0.2__NDVI.nc"
    if not os.path.exists(src):
        continue
    
    dst = r"D:\\temp_nc\\ndvi.nc"

    os.makedirs(r"D:\\temp_nc", exist_ok=True)
    shutil.copy(src, dst)

    ds = xr.open_dataset(dst, engine="netcdf4")

    df = ds['NDVI'].to_dataframe().reset_index()
    dfs_2022.append(df)
    # 拼接
df_all_2022 = pd.concat(dfs_2022, ignore_index=True)


city_csv = pd.read_csv('../UrbanAtlas/City_list_no_helsinki.csv')
new_row = {
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "New Country"
}

# 转为 DataFrame
new_row_df = pd.DataFrame([new_row])

# 拼接到原 DataFrame
city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)
city_list = list(city_csv['city_name'])

for city_name in tqdm.tqdm(city_list):
    output_dir = "generated_NDVI/"+city_name
    os.makedirs(output_dir, exist_ok=True)
    # year = 2018
    for year in [2018, 2022]:#[2020,2024]:
        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16
        identifier = city_name

        # if os.path.exists(output_dir + f"/{city_name}_NDVI_{year}.csv"):
            # continue
        pd_src = pd.read_csv(output_dir + f"/{city_name}_NDVI_{year}.csv")
        if len(pd_src)!=0:
            continue
            # print(city_name,year)

        if city_name == 'HELSINKI':
            identifier = 'urbancore'
        destination_directory = (
            f"../download_sat/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier}\\{date}"
            + "/" + identifier + "/img_info/"
        )
        new_file_name = identifier + "_list1.txt"
        destination_file = os.path.join(destination_directory, new_file_name)

        df_img = pd.read_csv(destination_file, delim_whitespace=True)
        df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

        # if year == 2020:
        #     df_ndvi = df_all_2020
        # elif year == 2024:
        #     df_ndvi = df_all_2024
        if year == 2018:
            df_ndvi = df_all_2018
        elif year == 2022:
            df_ndvi = df_all_2022
        results = []

        for _, img_row in df_img.iterrows():
            image_name = img_row["ImageFileName"]
            # if image_name in already_done_image_list:
            #     continue
            # # -----------------------------
            
            # 四个角落坐标
            # 获取矩形范围
            min_lon = min(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            max_lon = max(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            min_lat = min(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])
            max_lat = max(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])

            # 筛选落在矩形内的 NDVI 点  
            mask = (
                (df_ndvi["lon"] >= min_lon) & (df_ndvi["lon"] <= max_lon) &
                (df_ndvi["lat"] >= min_lat) & (df_ndvi["lat"] <= max_lat)
            )
            subset = df_ndvi[mask]

            # 计算均值
            ndvi_mean = subset["NDVI"].mean() if not subset.empty else -100

            results.append({
                "ImageFileName": image_name,
                "NDVI_mean": ndvi_mean,
                "Num_points": len(subset)   # 可选：记录点数，方便检查
            })

        # 保存结果
        df_out = pd.DataFrame(results)
        df_out = df_out[df_out["NDVI_mean"] != -100].reset_index(drop=True)
        df_out.to_csv(output_dir + f"/{city_name}_NDVI_{year}.csv", index=False)

### ------------------------------------------------------------------------------------------------------------------------------

# already_done_csv =f"../download_sat/sat_image_landuse_change_2012_2018_urbancore.csv"
# already_done_image_list = list(set(pd.read_csv(already_done_csv)['best_image_name']))
# city_name = 'HELSINKI'
# output_dir = "generated_NDVI/"+city_name
# os.makedirs(output_dir, exist_ok=True)
# # year = 2018
# for year in [2020,2024]:
#     year_str = str(year)
#     date = f"{year_str}-07-31"
#     zoom_level = 16
#     identifier = 'urbancore'

#     destination_directory = (
#         f"../download_sat/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier}\\{date}"
#         + "/" + identifier + "/img_info/"
#     )
#     new_file_name = identifier + "_list1.txt"
#     destination_file = os.path.join(destination_directory, new_file_name)

#     df_img = pd.read_csv(destination_file, delim_whitespace=True)
#     df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

    
#     if year == 2020:
#         df_ndvi = df_all_2020
#     elif year == 2024:
#         df_ndvi = df_all_2024

#     results = []

#     for _, img_row in df_img.iterrows():
#         image_name = img_row["ImageFileName"]
#         # if image_name in already_done_image_list:
#         #     continue
#         # # -----------------------------
        
#         # 四个角落坐标
#         # 获取矩形范围
#         min_lon = min(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
#         max_lon = max(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
#         min_lat = min(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])
#         max_lat = max(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])

#         # 筛选落在矩形内的 NDVI 点  
#         mask = (
#             (df_ndvi["lon"] >= min_lon) & (df_ndvi["lon"] <= max_lon) &
#             (df_ndvi["lat"] >= min_lat) & (df_ndvi["lat"] <= max_lat)
#         )
#         subset = df_ndvi[mask]

#         # 计算均值
#         ndvi_mean = subset["NDVI"].mean() if not subset.empty else -100

#         results.append({
#             "ImageFileName": image_name,
#             "NDVI_mean": ndvi_mean,
#             "Num_points": len(subset)   # 可选：记录点数，方便检查
#         })

#     # 保存结果
#     df_out = pd.DataFrame(results)
#     df_out = df_out[df_out["NDVI_mean"] != -100].reset_index(drop=True)
#     df_out.to_csv(output_dir + f"/{city_name}_NDVI_{year}.csv", index=False)