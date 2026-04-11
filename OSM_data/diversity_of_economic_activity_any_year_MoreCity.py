import os

import geopandas as gpd
import numpy as np
import pandas as pd
import tqdm
from shapely.geometry import box

from exclude_non_commercial_pois import exclude_non_commercial_pois

CITY_TABLE_PATH = '../UrbanAtlas/European_Countries_VS_Cities.csv'
URBANCORE_BBOX_DIR = '../UrbanAtlas/outputs/urbancore_bbox_dir'
DOWNLOAD_SAT_OUTPUT_ROOT = '../download_sat/outputs'
OSM_RAW_DIR = 'outputs/osm_raw_data'
PROCESSED_OSM_DIR = 'outputs/processed_osm_data'
OUTPUT_DIR = 'outputs/output_economic_dir_update'
YEARS = range(2014, 2025)
ZOOM_LEVEL = 16
DATE_TEMPLATE = '{year}-07-31'


def shannon_entropy(counts):
    p = counts / counts.sum()
    return -np.sum(p * np.log(p))


def resolve_place_name(city_full_name, province, note, country_name, year_str):
    if os.path.exists(os.path.join(OSM_RAW_DIR, f'{city_full_name}-{year_str}-free.shp.zip')):
        return city_full_name
    if os.path.exists(os.path.join(OSM_RAW_DIR, f'{province.lower()}-{year_str}-free.shp.zip')):
        return province.lower()
    if os.path.exists(os.path.join(OSM_RAW_DIR, f'{country_name}-{year_str}-free.shp.zip')):
        return country_name
    return note


def main():
    city_csv = pd.read_csv(CITY_TABLE_PATH)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(len(city_csv)):
        city_name = city_csv.at[i, 'city_name']
        city_full_name = city_csv.at[i, 'city_full_name']
        province = city_csv.at[i, 'province']
        note = city_csv.at[i, 'note']
        country_name = city_csv.at[i, 'country_name']

        for year in YEARS:
            year_str = str(year - 2000 + 1) + '0101'
            date = DATE_TEMPLATE.format(year=year)
            out_csv_path = os.path.join(OUTPUT_DIR, f'{city_name}_economic_urbancore_{year}.csv')

            place_name = resolve_place_name(city_full_name, province, note, country_name, year_str)
            if exclude_non_commercial_pois(place_name, year_str) == -1:
                continue

            poi_file = os.path.join(PROCESSED_OSM_DIR, f'{place_name}-{year_str}_poi_economic_only.shp')
            bbox_file = os.path.join(URBANCORE_BBOX_DIR, f'{city_name}_urbancore_bbox.csv')
            sat_list_file = os.path.join(
                DOWNLOAD_SAT_OUTPUT_ROOT,
                f'downloaded_sat_{year}_zoom_{ZOOM_LEVEL}',
                city_name,
                date,
                city_name,
                'img_info',
                f'{city_name}_list1.txt',
            )

            if not os.path.exists(poi_file) or not os.path.exists(bbox_file) or not os.path.exists(sat_list_file):
                continue

            pois = gpd.read_file(poi_file)
            if pois.crs is None or pois.crs.to_epsg() != 4326:
                pois = pois.to_crs(epsg=4326)
            pois_sindex = pois.sindex

            economic_fclass = {
                'restaurant', 'fast_food', 'cafe', 'bar', 'pub',
                'supermarket', 'convenience', 'mall', 'clothes', 'shoes', 'electronics', 'jeweller',
                'bakery', 'butcher', 'florist', 'bookshop',
                'hairdresser', 'beauty_shop', 'laundry', 'repair', 'photo',
                'travel_agent', 'car_rental', 'car_wash',
                'hotel', 'motel', 'guesthouse', 'hostel', 'camp_site',
                'cinema', 'theatre', 'museum', 'gallery',
                'nightclub', 'casino', 'sports_centre', 'fitness_centre',
            }

            pd.read_csv(bbox_file)
            df_img = pd.read_csv(sat_list_file, delim_whitespace=True)
            df_img['ImageFileName'] = df_img['ImageFileName'].str.replace(':', '', regex=False)

            results = []
            for _, img_row in tqdm.tqdm(df_img.iterrows()):
                image_name = img_row['ImageFileName']
                bbox = box(
                    img_row['Left_Edge_Longitude'],
                    img_row['Bottom_Edge_Latitude'],
                    img_row['Right_Edge_Longitude'],
                    img_row['Top_Edge_Latitude'],
                )

                candidate_idx = list(pois_sindex.intersection(bbox.bounds))
                pois_in_bbox = pois.iloc[candidate_idx]
                pois_in_bbox = pois_in_bbox[pois_in_bbox.intersects(bbox)]
                pois_in_bbox = pois_in_bbox[pois_in_bbox['fclass'].isin(economic_fclass)]

                diversity = 0
                if len(pois_in_bbox) > 0:
                    counts = pois_in_bbox['fclass'].value_counts()
                    diversity = shannon_entropy(counts)

                results.append([city_name, image_name, diversity])

            df_out = pd.DataFrame(results, columns=['identifier', 'best_image_name', 'economic'])
            df_out.to_csv(out_csv_path, index=False)


if __name__ == '__main__':
    main()
