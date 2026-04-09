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


def classify_land_use(value, land_use_keywords):
    if not isinstance(value, str):
        return None
    value_lower = value.lower()
    for category, keywords in land_use_keywords.items():
        if any(k in value_lower for k in keywords):
            return category
    return None

def calculate_land_use_mix_from_gdf(
    gdf_wgs84,
    min_lon,
    min_lat,
    max_lon,
    max_lat,
    target_land_use_categories
):

    bbox_wgs84 = box(min_lon, min_lat, max_lon, max_lat)
    # gdf_clipped = gdf_wgs84[gdf_wgs84.intersects(bbox_wgs84)]
    bbox_gdf = gpd.GeoDataFrame(geometry=[bbox_wgs84], crs="EPSG:4326")
    gdf_clipped = gpd.clip(gdf_wgs84, bbox_gdf)

    if gdf_clipped.empty:
        return None

    gdf_proj = gdf_clipped.to_crs(3035)
    gdf_proj["area_sqm"] = gdf_proj.geometry.area

    total_area = gdf_proj["area_sqm"].sum()
    if total_area == 0:
        return None

    area_by_landuse = gdf_proj.groupby("land_use_group")["area_sqm"].sum()
    p_dj = area_by_landuse / total_area

    nLUC = len(target_land_use_categories)
    sum_part = -np.sum(p_dj[p_dj > 0] * np.log(p_dj[p_dj > 0]))
    land_use_mix = sum_part / np.log(nLUC)

    return land_use_mix


if __name__ == "__main__":

    land_use_col_name = "class_2018"
    # land_use_col_name = "class_2012"

    land_use_keywords = {
        "residential": ["residential"],
        "commercial_industrial_institutional_governmental": [
            "commercial", "industrial", "institutional", "governmental"
        ],
        "recreational_parks_water": [
            "recreational", "parks", "water"
        ]
    }

    # ---------------------------
    gpkg_list = glob.glob('unziped_files_LU_2018/*/*/Data/*.gpkg')
    # gpkg_list = glob.glob('unziped_files_LU_2012/*/*/Data/*.gpkg')
    for gpkg_path in gpkg_list:
        city_name = Path(gpkg_path).parts[1]
        # if city_name != 'GRAZ':
        #     continue
        # gpkg_path = r"7443\\Results\\FI001L3_HELSINKI_UA2018_v013\\FI001L3_HELSINKI_UA2018_v013\\Data\\FI001L3_HELSINKI_UA2018_v013.gpkg"
        # layer_name = "FI001L3_HELSINKI_UA2018"
        layers = fiona.listlayers(gpkg_path)

        urbancore_layers = [ly for ly in layers if "urbancore" in ly.lower()]
        urban_boundary_layer_name = urbancore_layers[0]
        LU_layer_name = min(layers, key=len)

        gdf = gpd.read_file(gpkg_path, layer=LU_layer_name).to_crs(4326)

        gdf["land_use_group"] = gdf[land_use_col_name].apply(lambda x: classify_land_use(x, land_use_keywords))
        gdf = gdf.dropna(subset=["land_use_group"])

        year = 2018
        # year = 2012
        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16

        # input_csv = "../UrbanAtlas/Henlsinki_urbancore_bbox.csv"
        city_bound = pd.read_csv(f"outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")
        city_bound.at[0,'identifier'] = city_name
        df = city_bound  #pd.read_csv(input_csv)
        rows_to_process = [0]

        out_dir = "outputs/output_LU_mix_dir/"
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

        df_out = pd.DataFrame(data_arr, columns=df_columns)
        df_out["landuse_mix"] = pd.to_numeric(df_out["landuse_mix"], errors="coerce")

        df_out = df_out.dropna(subset=["landuse_mix"])

        df_out = df_out[df_out["landuse_mix"] != 0.0]
        df_out = df_out.reset_index(drop=True)

        out_csvPath = out_dir + city_name + "_LU_mix_" + str(year) + ".csv"
        df_out.to_csv(out_csvPath, index=False)
        print(f"saved to {out_csvPath}")

