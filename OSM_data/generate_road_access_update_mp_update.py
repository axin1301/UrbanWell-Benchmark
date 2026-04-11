import os
from pyproj import Geod

import geopandas as gpd
import numpy as np
import pandas as pd
import tqdm
from shapely.geometry import box
from sklearn.neighbors import BallTree

GEOD = Geod(ellps='WGS84')

# Upstream inputs from UrbanAtlas, download_sat, and OSM preprocessing.
CITY_TABLE_PATH = '../UrbanAtlas/European_Countries_VS_Cities.csv'
URBANCORE_BBOX_DIR = '../UrbanAtlas/outputs/urbancore_bbox_dir'
DOWNLOAD_SAT_OUTPUT_ROOT = '../download_sat/outputs'
OSM_RAW_DIR = 'outputs/osm_raw_data'
UNZIPPED_OSM_DIR = 'outputs/unzipped_osm_files'
PROCESSED_OSM_DIR = 'outputs/processed_osm_data'
# Output folder produced by this script.
OUTPUT_DIR = 'outputs/road-output'
# Optional image filter used in the research workspace.
URBANFORM_IMAGE_FILTER_CSV = 'urbanform_images.csv'
USE_IMAGE_FILTER = os.path.exists(URBANFORM_IMAGE_FILTER_CSV)
# Processing behavior.
YEARS = range(2014, 2025)
ZOOM_LEVEL = 16
DATE_TEMPLATE = '{year}-07-31'
POI_TYPES = ['restaurant', 'supermarket']
SPECIAL_PLACE_SKIPS = {('MADRID', 'before_or_equal_2020')}
SPECIAL_RAW_PATH_OVERRIDES = {
    ('AMSTERDAM', 2021): {
        'road_shp': os.path.join('outputs', 'economic_previous', 'noord-holland-220101-free_shp', 'gis_osm_roads_free_1.shp'),
        'poi_shp': os.path.join(PROCESSED_OSM_DIR, 'noord-holland-220101_poi_economic_only.shp'),
    }
}


def calculate_geodesic_length(geom):
    if geom.is_empty:
        return 0.0
    return GEOD.geometry_length(geom)


def compute_accessibility_metrics_fast(bbox_values, roads_city, pois_city, poi_trees, poi_types):
    left_lon, bottom_lat, right_lon, top_lat = bbox_values
    region_poly = box(left_lon, bottom_lat, right_lon, top_lat)
    roads_small = gpd.clip(roads_city, region_poly)
    roads_small['length_m'] = roads_small.geometry.apply(calculate_geodesic_length)

    total_road_km = roads_small['length_m'].sum() / 1000
    area_m2, _ = GEOD.geometry_area_perimeter(region_poly)
    area_km2 = abs(area_m2) / 1e6 if area_m2 != 0 else np.nan
    network_density = total_road_km / area_km2 if area_km2 and area_km2 > 0 else np.nan

    idx = list(pois_city.sindex.intersection(region_poly.bounds))
    pois_small = pois_city.iloc[idx]
    poi_counts = {
        poi_type: pois_small[pois_small['fclass'] == poi_type].shape[0]
        for poi_type in poi_types
    }

    center = region_poly.centroid
    center_rad = np.radians([[center.y, center.x]])
    avg_distances = {}
    for poi_type in poi_types:
        tree = poi_trees.get(poi_type)
        if tree is None:
            avg_distances[poi_type] = np.nan
            continue
        dist_rad, _ = tree.query(center_rad, k=1)
        avg_distances[poi_type] = (dist_rad[0][0] * 6371000) / 1000

    return {
        'pois_within': poi_counts,
        'avg_distance_to_nearest_poi_by_type': avg_distances,
        'road_length': total_road_km,
        'network_density_km_per_km2': network_density,
    }


def preprocess_city(roads_all, pois_all, city_bbox):
    city_poly = box(*city_bbox)
    roads_city = gpd.clip(roads_all, city_poly)
    pois_city = gpd.clip(pois_all, city_poly)

    poi_trees = {}
    for poi_type in pois_city['fclass'].unique():
        subset = pois_city[pois_city['fclass'] == poi_type]
        if len(subset) == 0:
            poi_trees[poi_type] = None
            continue
        coords = np.radians(np.vstack([subset.geometry.y, subset.geometry.x]).T)
        poi_trees[poi_type] = BallTree(coords, metric='haversine')

    return roads_city, pois_city, poi_trees


def resolve_place_name(city_full_name, province, note, country_name, year_str):
    if os.path.exists(os.path.join(OSM_RAW_DIR, f'{city_full_name}-{year_str}-free.shp.zip')):
        return city_full_name
    if os.path.exists(os.path.join(OSM_RAW_DIR, f'{province.lower()}-{year_str}-free.shp.zip')):
        return province.lower()
    if os.path.exists(os.path.join(OSM_RAW_DIR, f'{country_name}-{year_str}-free.shp.zip')):
        return country_name
    return note


def build_city_bbox(city_name):
    city_bound_path = os.path.join(URBANCORE_BBOX_DIR, f'{city_name}_urbancore_bbox.csv')
    city_bound = pd.read_csv(city_bound_path)
    return (
        city_bound.at[0, 'min_lon'],
        city_bound.at[0, 'min_lat'],
        city_bound.at[0, 'max_lon'],
        city_bound.at[0, 'max_lat'],
    )


def build_sat_list_path(city_name, year):
    date = DATE_TEMPLATE.format(year=year)
    return os.path.join(
        DOWNLOAD_SAT_OUTPUT_ROOT,
        f'downloaded_sat_{year}_zoom_{ZOOM_LEVEL}',
        city_name,
        date,
        city_name,
        'img_info',
        f'{city_name}_list1.txt',
    )


def load_image_filter():
    if not USE_IMAGE_FILTER:
        return None
    df = pd.read_csv(URBANFORM_IMAGE_FILTER_CSV)
    return set(df['image_name'])


def main():
    image_filter = load_image_filter()
    city_csv = pd.read_csv(CITY_TABLE_PATH)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for year in YEARS:
        year_str = str(year - 2000 + 1) + '0101'

        for i in tqdm.tqdm(range(len(city_csv))):
            city_name = city_csv.at[i, 'city_name']
            city_full_name = city_csv.at[i, 'city_full_name']
            province = city_csv.at[i, 'province']
            note = city_csv.at[i, 'note']
            country_name = city_csv.at[i, 'country_name']

            output_csv = os.path.join(OUTPUT_DIR, f'{city_name}_{year_str}_update.csv')
            if os.path.exists(output_csv):
                continue
            if city_name == 'MADRID' and year <= 2020:
                continue

            place_name = resolve_place_name(city_full_name, province, note, country_name, year_str)
            if place_name in ['centro', 'mazowieckie'] and year == 2014:
                continue

            road_shp = os.path.join(UNZIPPED_OSM_DIR, f'{place_name}-{year_str}-free_shp', 'gis_osm_roads_free_1.shp')
            poi_shp = os.path.join(PROCESSED_OSM_DIR, f'{place_name}-{year_str}_poi_economic_only.shp')

            override = SPECIAL_RAW_PATH_OVERRIDES.get((city_name, year))
            if override:
                road_shp = override['road_shp']
                poi_shp = override['poi_shp']

            sat_list_path = build_sat_list_path(city_name, year)
            bbox_path = os.path.join(URBANCORE_BBOX_DIR, f'{city_name}_urbancore_bbox.csv')
            if not all(os.path.exists(path) for path in [road_shp, poi_shp, sat_list_path, bbox_path]):
                print(f'Skipping {city_name} {year} because one or more inputs are missing.')
                continue

            roads_all = gpd.read_file(road_shp).to_crs(4326)
            pois_all = gpd.read_file(poi_shp).to_crs(4326)
            roads_city, pois_city, pois_tree = preprocess_city(roads_all, pois_all, build_city_bbox(city_name))

            df_img = pd.read_csv(sat_list_path, delim_whitespace=True)
            df_img['ImageFileName'] = df_img['ImageFileName'].str.replace(':', '', regex=False)

            all_records = []
            for _, row in tqdm.tqdm(df_img.iterrows()):
                if image_filter is not None and row['ImageFileName'] not in image_filter:
                    continue

                metrics = compute_accessibility_metrics_fast(
                    (
                        row['Left_Edge_Longitude'],
                        row['Bottom_Edge_Latitude'],
                        row['Right_Edge_Longitude'],
                        row['Top_Edge_Latitude'],
                    ),
                    roads_city,
                    pois_city,
                    pois_tree,
                    POI_TYPES,
                )

                out = {'image_name': row['ImageFileName']}
                out.update(metrics['pois_within'])
                for poi_type in POI_TYPES:
                    out[f'avg_dist_to_{poi_type}'] = metrics['avg_distance_to_nearest_poi_by_type'][poi_type]
                out['road_length'] = metrics['road_length']
                out['network_density_km_per_km2'] = metrics['network_density_km_per_km2']
                all_records.append(out)

            pd.DataFrame(all_records).to_csv(output_csv, index=False)
            print(f'saved {city_name}')


if __name__ == '__main__':
    main()
