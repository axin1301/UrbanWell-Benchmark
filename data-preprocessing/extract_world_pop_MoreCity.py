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
        # 计算目标栅格的空间参考和大小
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        # 新的元数据
        kwargs = src.meta.copy()
        kwargs.update({
            "crs": dst_crs,
            "transform": transform,
            "width": width,
            "height": height
        })

        # 在内存中创建 numpy 数组存放重投影结果
        dest = np.zeros((src.count, height, width), dtype=src.dtypes[0])

        # 对每个波段做重投影
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
    "country_name": "New Country",
    "country_code": "fin"
}

# 转为 DataFrame
new_row_df = pd.DataFrame([new_row])

# 拼接到原 DataFrame
city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

failed_country_list = []
for i in range(len(city_csv)):
    city_name = city_csv.at[i, 'city_name']
    city_full_name = city_csv.at[i, 'city_full_name']
    province = city_csv.at[i, 'province']
    note = city_csv.at[i, 'note']
    country_name = city_csv.at[i, 'country_name']
    country_code = city_csv.at[i, 'country_code']

    for year in range(2014,2021):
        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16

        # ==== 参数设置 ====
        tif_file = f"D:\\CitySense原始数据\\WorldPop\\data/{country_code}_ppp_{year}_UNadj.tif"
        if not os.path.exists(tif_file):
            failed_country_list.append(country_name)
            continue
        # input_csv = f"../UrbanAtlas/urbancore_bbox_dir2/{city_name}_urbancore_bbox.csv"
        # if city_name == 'HELSINKI':
        #     input_csv = f"../UrbanAtlas/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv"
        # df_bbox = pd.read_csv(input_csv)
        # rows_to_process = [0]

        out_dir = 'output_popu_dir/'
        os.makedirs(out_dir, exist_ok=True)
        df_columns = ['identifier', 'best_image_name', 'population']
        data_arr = []

        if os.path.exists(os.path.join(out_dir, f"{city_name}_ppp_{year}.csv")):
            continue

        # ==== 只打开一次 TIF ====
        with rasterio.open(tif_file) as src:
            if not src.crs.is_geographic:
                raise ValueError(f"数据投影是 {src.crs}, 不是经纬度坐标系，需要先重投影")
            # if src.crs != CRS.from_string("EPSG:4326"):
            #     raise ValueError(f"数据投影是 {src.crs}, 不是 WGS84 经纬度 (EPSG:4326)，需要先重投影")
            # if src.crs.to_string() != "EPSG:4326":
            #     # rasterio.crs.CRS.from_epsg(4326)  # 如果为空就假设是 WGS84
            #     raise ValueError(f"数据投影是 {src.crs}，不是经纬度，需要先重投影")
            #     src, meta = reproject_raster_to_memory(tif_file, dst_crs="EPSG:4326")

            # for idx in rows_to_process:
            #     row = df_bbox.loc[idx]
            if 1:
                identifier = city_name

                if city_name == 'HELSINKI':
                    identifier = 'urbancore'
                destination_directory = (
                    f'../download_sat/downloaded_sat_{year}_zoom_{zoom_level}/'
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

                    # 根据经纬度范围计算 window
                    window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)

                    # 读取该窗口数据
                    data = src.read(1, window=window)

                    # 清理无效值
                    data = np.where(data < 0, np.nan, data)

                    # 总人口
                    total_population = np.nansum(data)
                    data_arr.append([identifier, image_name, total_population])

        # ==== 一次性写 CSV ====
        df_out = pd.DataFrame(data_arr, columns=df_columns)
        out_csvPath = os.path.join(out_dir, f"{city_name}_ppp_{year}.csv")
        df_out.to_csv(out_csvPath, index=False)

print(set(failed_country_list))