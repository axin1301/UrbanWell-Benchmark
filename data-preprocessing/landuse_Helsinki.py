import geopandas as gpd
from shapely.geometry import box
from pyproj import CRS
import numpy as np
import os
import pandas as pd
import glob
from pathlib import Path
import os
import fiona

# --- 分类函数 ---
def classify_land_use(value, land_use_keywords):
    if not isinstance(value, str):
        return None
    value_lower = value.lower()
    for category, keywords in land_use_keywords.items():
        if any(k in value_lower for k in keywords):
            return category
    return None


# --- 示例用法 ---
if __name__ == "__main__":

    for year in [2018]:#,2012]: 
        land_use_col_name = f"class_{year}"
        # land_use_col_name = "class_2012"

        # ---------------------------
        # 1. 文件路径 & 参数
        # ---------------------------
        if year == 2012:
            gpkg_path = r"10017\\Results\\FI001L3_HELSINKI_UA2012_revised_v021\\FI001L3_HELSINKI_UA2012_revised_v021\\Data\\FI001L3_HELSINKI_UA2012_revised_v021.gpkg"
            layer_name = "FI001L3_HELSINKI_UA2012_revised"
        else:
            gpkg_path = r"7443\\Results\\FI001L3_HELSINKI_UA2018_v013\\FI001L3_HELSINKI_UA2018_v013\\Data\\FI001L3_HELSINKI_UA2018_v013.gpkg"
            layer_name = "FI001L3_HELSINKI_UA2018"

        # --- 一次性读数据 (WGS84) ---
        print("读取数据中...")
        gdf = gpd.read_file(gpkg_path, layer=layer_name).to_crs(4326)
        # city_name = Path(gpkg_path).parts[1]
        city_name = 'HELSINKI'

        layers = fiona.listlayers(gpkg_path)
        # 查找包含 "urbancore" 的图层名（忽略大小写）
        urbancore_layers = [ly for ly in layers if "urbancore" in ly.lower()]
        urban_boundary_layer_name = urbancore_layers[0]
        LU_layer_name = min(layers, key=len)


        # --- 一次性读数据 (WGS84) ---
        # print("读取数据中...")
        # gdf = gpd.read_file(gpkg_path, layer=LU_layer_name).to_crs(4326)
        print(f"数据准备完成，共 {len(gdf)} 个要素")

        # --- CSV 输入输出 ---

        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16

        # input_csv = "../UrbanAtlas/Henlsinki_urbancore_bbox.csv"
        city_bound = pd.read_csv("../UrbanAtlas/Helsinki_urbancore_bbox.csv") #f"../UrbanAtlas/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")
        city_bound.at[0,'identifier'] = city_name
        df = city_bound  #pd.read_csv(input_csv)
        rows_to_process = [0]  # 只跑一部分测试

        out_dir = "output_LU_single_year/"
        os.makedirs(out_dir, exist_ok=True)

        df_columns = ["best_image_name", 'class_'+str(year), 'year']
        data_arr = []

        for ridx in rows_to_process:
            row = df.loc[ridx]
            identifier = 'urbancore'# str(row["identifier"])

            destination_directory = (
                f"../download_sat/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier}\\{date}"
                + "/" + identifier + "/img_info/"
            )
            new_file_name = identifier + "_list1.txt"
            destination_file = os.path.join(destination_directory, new_file_name)

            df_img = pd.read_csv(destination_file, delim_whitespace=True)
            df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

            # 预建空间索引
            gdf_sindex = gdf.sindex  

            for _, img_row in df_img.iterrows():
                image_name = img_row["ImageFileName"]
                lat_min = img_row["Bottom_Edge_Latitude"]
                lat_max = img_row["Top_Edge_Latitude"]
                lon_min = img_row["Left_Edge_Longitude"]
                lon_max = img_row["Right_Edge_Longitude"]

                img_bbox = box(lon_min, lat_min, lon_max, lat_max)

                # 先用索引过滤候选几何
                candidate_idx = list(gdf_sindex.intersection(img_bbox.bounds))
                candidates = gdf.iloc[candidate_idx]

                if candidates.empty:
                    continue

                # 计算真正的交集
                candidates = candidates.copy()
                candidates["geometry"] = candidates.geometry.intersection(img_bbox)
                candidates = candidates[~candidates.is_empty]

                if candidates.empty:
                    continue

                candidates["intersect_area"] = candidates.geometry.area
                idx = candidates["intersect_area"].idxmax()
                dominant_landuse = candidates.loc[idx, land_use_col_name]

                data_arr.append([image_name, dominant_landuse, year])

        # --- 一次性输出 ---
        df_out = pd.DataFrame(data_arr, columns=df_columns)

        # out_dir = "output_LU_single_year/"
        out_csvPath = out_dir + city_name + "_LU_" + str(year) + ".csv"
        df_out.to_csv(out_csvPath, index=False)
        print(f"结果已保存：{out_csvPath}")