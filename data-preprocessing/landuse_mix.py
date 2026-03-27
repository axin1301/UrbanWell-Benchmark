import geopandas as gpd
from shapely.geometry import box
from pyproj import CRS
import numpy as np
import os
import pandas as pd

# --- 分类函数 ---
def classify_land_use(value, land_use_keywords):
    if not isinstance(value, str):
        return None
    value_lower = value.lower()
    for category, keywords in land_use_keywords.items():
        if any(k in value_lower for k in keywords):
            return category
    return None


# --- 主计算函数 ---
def calculate_land_use_mix_from_gdf(
    gdf_wgs84,
    min_lon,
    min_lat,
    max_lon,
    max_lat,
    target_land_use_categories
):
    """
    输入在 WGS84 下的 GeoDataFrame，裁剪 bbox，
    再投影到等面积坐标系计算 Shannon 指数
    """
    # 1. 在 WGS84 下裁剪
    bbox_wgs84 = box(min_lon, min_lat, max_lon, max_lat)
    # gdf_clipped = gdf_wgs84[gdf_wgs84.intersects(bbox_wgs84)]
    bbox_gdf = gpd.GeoDataFrame(geometry=[bbox_wgs84], crs="EPSG:4326")
    gdf_clipped = gpd.clip(gdf_wgs84, bbox_gdf)

    if gdf_clipped.empty:
        return None

    # 2. 投影到等面积坐标系 (欧洲建议 EPSG:3035)
    gdf_proj = gdf_clipped.to_crs(3035)
    gdf_proj["area_sqm"] = gdf_proj.geometry.area

    total_area = gdf_proj["area_sqm"].sum()
    if total_area == 0:
        return None

    # 3. 计算 Shannon 指数
    area_by_landuse = gdf_proj.groupby("land_use_group")["area_sqm"].sum()
    p_dj = area_by_landuse / total_area

    nLUC = len(target_land_use_categories)
    sum_part = -np.sum(p_dj[p_dj > 0] * np.log(p_dj[p_dj > 0]))
    land_use_mix = sum_part / np.log(nLUC)

    return land_use_mix


# --- 示例用法 ---
if __name__ == "__main__":

    # land_use_col_name = "class_2018"
    land_use_col_name = "class_2012"

    # 定义类别关键词
    land_use_keywords = {
        "residential": ["residential"],
        "commercial_industrial_institutional_governmental": [
            "commercial", "industrial", "institutional", "governmental"
        ],
        "recreational_parks_water": [
            "recreational", "parks", "water"
        ]
    }

    # gpkg_path = r"7443\\Results\\FI001L3_HELSINKI_UA2018_v013\\FI001L3_HELSINKI_UA2018_v013\\Data\\FI001L3_HELSINKI_UA2018_v013.gpkg"
    # layer_name = "FI001L3_HELSINKI_UA2018"
    gpkg_path = r"10017\\Results\\FI001L3_HELSINKI_UA2012_revised_v021\\FI001L3_HELSINKI_UA2012_revised_v021\\Data\\FI001L3_HELSINKI_UA2012_revised_v021.gpkg"
    layer_name = "FI001L3_HELSINKI_UA2012_revised"

    # --- 一次性读数据 (WGS84) ---
    print("读取数据中...")
    gdf = gpd.read_file(gpkg_path, layer=layer_name).to_crs(4326)

    # 分类一次
    gdf["land_use_group"] = gdf[land_use_col_name].apply(lambda x: classify_land_use(x, land_use_keywords))
    gdf = gdf.dropna(subset=["land_use_group"])
    print(f"数据准备完成，共 {len(gdf)} 个要素")

    # --- CSV 输入输出 ---
    # year = 2018
    year = 2012
    year_str = str(year)
    date = f"{year_str}-07-31"
    zoom_level = 16

    input_csv = "../UrbanAtlas/Henlsinki_urbancore_bbox.csv"
    df = pd.read_csv(input_csv)
    rows_to_process = [0]  # 只跑一部分测试

    out_dir = "output_LU_mix_dir/"
    os.makedirs(out_dir, exist_ok=True)

    df_columns = ["best_image_name", "landuse_mix"]
    data_arr = []

    for ridx in rows_to_process:
        row = df.loc[ridx]
        identifier = str(row["identifier"])

        destination_directory = (
            f"../download_sat/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier}\\{date}"
            + "/" + identifier + "/img_info/"
        )
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

            mix_index = calculate_land_use_mix_from_gdf(
                gdf,
                lon_min, lat_min,
                lon_max, lat_max,
                land_use_keywords
            )

            data_arr.append([image_name, mix_index])

    # --- 一次性输出 ---
    df_out = pd.DataFrame(data_arr, columns=df_columns)
    # out_csvPath = out_dir + "HELSINKI_LU_mix_" + identifier + "_" + str(year) + ".csv"
    out_csvPath = out_dir + "HELSINKI_LU_mix_" + str(year) + ".csv"
    df_out.to_csv(out_csvPath, index=False)
    print(f"结果已保存：{out_csvPath}")