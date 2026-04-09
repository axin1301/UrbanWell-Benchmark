import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely import wkt
import os

def create_bbox_polygon(row):
    minx = row['Left_Edge_Longitude']
    miny = row['Bottom_Edge_Latitude']
    maxx = row['Right_Edge_Longitude']
    maxy = row['Top_Edge_Latitude']
    return Polygon([(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy), (minx, miny)])


city_list = list(pd.read_csv('../UrbanAtlas/City_list.csv')['city_name'])
for city_name in city_list:
    city_bound = pd.read_csv(f"../UrbanAtlas/outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")
    # city_bound.at[0,'identifier'] = city_name

    csv_file_path = '../UrbanAtlas/outputs/urbanchange_centroids_dir/' + f"{city_name}_urban_filtered_centroids_wgs84.csv"
    attr_file_path = '../UrbanAtlas/outputs/urbanchange_centroids_dir/' + f"{city_name}_output_bboxes_with_all_attributes.csv"
    df_city = pd.read_csv(csv_file_path)
    df_attr = pd.read_csv(attr_file_path)
    zoom_level = 16
    identifier_urbancore = city_name

    # print(f"outputs/Landuse_Change_2012_2018_urbancore/{city_name}_sat_image_landuse_change_2012_2018_urbancore.csv")
    results = []

    for _, attr_row in df_attr.iterrows():
        identifier = attr_row['identifier']
        class_2012 = attr_row.get('class_2012', None)
        class_2018 = attr_row.get('class_2018', None)

        city_match = df_city[df_city['identifier'] == identifier]
        if city_match.empty:
            print(f"identifier={identifier}")
            continue

        city_row = city_match.iloc[0]
        # city_name = city_row['fua_name']
        multipolygon = wkt.loads(city_row['geometry'])

        for year in [2018]:
            year_str = str(year)
            date = f"{year_str}-07-31"
            destination_directory = f'outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier_urbancore}\\{date}'+'/'+ identifier_urbancore + '/img_info/'   
            new_file_name = identifier_urbancore+ "_list1.txt"
            destination_file = os.path.join(destination_directory, new_file_name)

            print(f"Processing identifier={identifier_urbancore}, year={year}, city={city_name}")

            if not os.path.exists(destination_file):
                continue

            df_images = pd.read_csv(destination_file, sep=r'\s+')
            df_images['ImageFileName'] = df_images['ImageFileName'].str.rstrip(':')
            df_images['geometry'] = df_images.apply(create_bbox_polygon, axis=1)
            gdf_images = gpd.GeoDataFrame(df_images, geometry='geometry', crs="EPSG:4326")

            max_overlap_ratio = 0
            best_image = None
            best_row = None

            for _, row in gdf_images.iterrows():
                bbox_polygon = row['geometry']
                if bbox_polygon.intersects(multipolygon):
                    intersection = bbox_polygon.intersection(multipolygon)
                    overlap_ratio = intersection.area / multipolygon.area if multipolygon.area > 0 else 0
                    if overlap_ratio > max_overlap_ratio:
                        max_overlap_ratio = overlap_ratio
                        best_image = row['ImageFileName']
                        best_row = row

            if best_image and best_row is not None:
                results.append({
                    'identifier': identifier,
                    'year': year,
                    'fua_code': identifier,
                    'class_2012': class_2012,
                    'class_2018': class_2018,
                    'best_image_name': best_image,
                    'overlap_ratio': max_overlap_ratio,
                    'Left_Edge_Longitude': best_row['Left_Edge_Longitude'],
                    'Bottom_Edge_Latitude': best_row['Bottom_Edge_Latitude'],
                    'Right_Edge_Longitude': best_row['Right_Edge_Longitude'],
                    'Top_Edge_Latitude': best_row['Top_Edge_Latitude'],
                    'bbox_wkt': best_row['geometry'].wkt
                })
                # print(f"Found best image {best_image} with overlap {max_overlap_ratio:.4f}")
            else:
                pass
                # print("No intersection found")

    results_df = pd.DataFrame(results)
    results_df.to_csv(f"outputs/Landuse_Change_2012_2018_urbancore/{city_name}_sat_image_landuse_change_2012_2018_urbancore.csv", index=False, encoding="utf-8-sig")



