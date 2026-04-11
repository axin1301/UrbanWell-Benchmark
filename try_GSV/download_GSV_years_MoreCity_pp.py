import math
import os
import pickle
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
import streetview
from tqdm import tqdm

from configs import GOOGLE_KEY_MY

# Google Street View API key.
MAPS_API_KEY = GOOGLE_KEY_MY
# Upstream inputs from UrbanAtlas, download_sat, and generate_stv_points_MoreCity.py.
CITY_LIST_PATH = '../UrbanAtlas/City_list.csv'
LANDUSE_CHANGE_DIR = '../download_sat/outputs/Landuse_Change_2012_2018_urbancore'
GENERATED_GRID_POINTS_ROOT = 'outputs/generated_grid_points'
# Output folders produced by this script.
PANO_CACHE_ROOT = 'outputs/PANO_ID_PKL'
DOWNLOADED_STV_ROOT = 'outputs/downloaded_stv_selected'
# Download behavior.
HEADINGS = [0, 90, 180, 270]
MAX_FETCH_WORKERS = 32
MAX_DATE_FILL_WORKERS = 32
MAX_DOWNLOAD_WORKERS = 32
DATE_FILL_QPS = 10
MAX_PANOS_PER_POINT = 4
MAX_PANOS_PER_YEAR = 4


def fetch_pano(lat, lon):
    try:
        panos = streetview.search_panoramas(lat=lat, lon=lon)
        return lat, lon, panos
    except Exception:
        return lat, lon, []


def get_pano_date(pano_id, api_key=MAPS_API_KEY, retries=3, delay=1):
    url = 'https://maps.googleapis.com/maps/api/streetview/metadata'
    params = {'pano': pano_id, 'key': api_key}
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('date', None)
        except requests.RequestException:
            attempt += 1
            time.sleep(delay)
        except ValueError:
            return None
    return None


def collect_all_panos_parallel(pd_csv, max_workers=8, cache_file=None, max_panos_per_point=4):
    min_lat, max_lat = pd_csv['latitude'].min(), pd_csv['latitude'].max()
    min_lon, max_lon = pd_csv['longitude'].min(), pd_csv['longitude'].max()

    def in_bbox(pano):
        return (min_lat <= pano.lat <= max_lat) and (min_lon <= pano.lon <= max_lon)

    if cache_file and os.path.exists(cache_file):
        with open(cache_file, 'rb') as file_handle:
            latlon_to_panos = pickle.load(file_handle)
    else:
        latlon_to_panos = {}

    latlon_list = [(row['latitude'], row['longitude']) for _, row in pd_csv.iterrows()]
    new_fetch_needed = []
    for lat, lon in latlon_list:
        if (lat, lon) not in latlon_to_panos:
            new_fetch_needed.append((lat, lon))
        elif any(pano.date is None for pano in latlon_to_panos[(lat, lon)]):
            new_fetch_needed.append((lat, lon))

    if new_fetch_needed:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for lat, lon, panos in tqdm(
                executor.map(lambda xy: fetch_pano(*xy), new_fetch_needed),
                total=len(new_fetch_needed),
            ):
                panos = [pano for pano in panos if in_bbox(pano)]
                panos_with_date = [pano for pano in panos if pano.date]
                panos_none_date = [pano for pano in panos if not pano.date]
                latlon_to_panos[(lat, lon)] = (panos_with_date + panos_none_date)[:max_panos_per_point]

    if cache_file:
        with open(cache_file, 'wb') as file_handle:
            pickle.dump(latlon_to_panos, file_handle)

    return latlon_to_panos


def fill_missing_dates_parallel(latlon_to_panos, max_workers=16, qps=10):
    pano_list = []
    for panos in latlon_to_panos.values():
        for pano in panos:
            if pano.date is None:
                pano_list.append(pano)
    print(f'{len(pano_list)} panos')

    semaphore = threading.Semaphore(qps)

    def task(pano):
        with semaphore:
            pano.date = get_pano_date(pano.pano_id)
            time.sleep(1.0 / qps)
        return pano

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(tqdm(executor.map(task, pano_list), total=len(pano_list)))

    return latlon_to_panos


def haversine(lat1, lon1, lat2, lon2):
    radius_km = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def select_diverse_panos(year_panos, k=4):
    if len(year_panos) <= k:
        return year_panos

    selected = [year_panos[0]]
    candidates = year_panos[1:]

    while len(selected) < k and candidates:
        distances = []
        for pano in candidates:
            min_distance = min(haversine(pano.lat, pano.lon, selected_pano.lat, selected_pano.lon) for selected_pano in selected)
            distances.append((min_distance, pano))

        distances.sort(reverse=True, key=lambda item: item[0])
        selected.append(distances[0][1])
        candidates.remove(distances[0][1])

    return selected


def select_panos_by_years(latlon_to_panos, pd_csv, already_df=None, max_panos_per_year=4):
    min_lat, max_lat = pd_csv['latitude'].min(), pd_csv['latitude'].max()
    min_lon, max_lon = pd_csv['longitude'].min(), pd_csv['longitude'].max()

    def in_bbox(pano):
        return (min_lat <= pano.lat <= max_lat) and (min_lon <= pano.lon <= max_lon)

    existing_year_counts = {}
    if already_df is not None and not already_df.empty:
        existing_year_counts = already_df.groupby('year')['id'].nunique().to_dict()

    year_counter = Counter()
    for panos in latlon_to_panos.values():
        for pano in panos:
            if pano.date:
                try:
                    year_counter[int(pano.date[:4])] += 1
                except Exception:
                    pass

    sorted_years = [year for year, _ in year_counter.most_common()]
    selected_panos = []

    for year in sorted_years:
        if year in existing_year_counts and 2 <= existing_year_counts[year] <= 4:
            continue

        year_panos = [
            pano
            for panos in latlon_to_panos.values()
            for pano in panos
            if pano.date and int(pano.date[:4]) == year and in_bbox(pano)
        ]
        if len(year_panos) >= 4:
            selected_panos.extend(select_diverse_panos(year_panos, k=max_panos_per_year))
        elif len(year_panos) in [2, 3]:
            selected_panos.extend(year_panos)

    return selected_panos


def download_one_image(pano, heading, base_dir, formatted_lat, formatted_lon):
    try:
        response = streetview.get_streetview(
            pano_id=pano.pano_id,
            heading=heading,
            fov=90,
            pitch=0,
            api_key=MAPS_API_KEY,
        )
        image_name = (
            f'street_view_{formatted_lat}_{formatted_lon}_{pano.lat}_{pano.lon}_'
            f'{pano.date[:4]}_{pano.date}_{pano.pano_id}_{heading}.jpg'
        )
        file_path = os.path.join(base_dir, image_name)
        response.save(file_path, 'jpeg')
        return {
            'id': pano.pano_id,
            'query_lat': formatted_lat,
            'query_lon': formatted_lon,
            'returned_lat': pano.lat,
            'returned_lon': pano.lon,
            'date': pano.date,
            'year': int(pano.date[:4]),
            'heading': heading,
            'image_name': image_name,
        }
    except Exception:
        return None


def download_selected_panos(city_name, identifier, selected_panos, max_workers=16):
    base_dir = os.path.join(DOWNLOADED_STV_ROOT, city_name, identifier, 'street_view_images')
    os.makedirs(base_dir, exist_ok=True)
    existing_files = set(os.listdir(base_dir))

    tasks = []
    for pano in selected_panos:
        for heading in HEADINGS:
            image_name = f'street_view_{pano.lat}_{pano.lon}_{pano.date[:4]}_{pano.date}_{pano.pano_id}_{heading}.jpg'
            if image_name not in existing_files:
                tasks.append((pano, heading, base_dir, pano.lat, pano.lon))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(lambda args: download_one_image(*args), tasks), total=len(tasks)))

    return [result for result in results if result]


def main():
    city_list = list(pd.read_csv(CITY_LIST_PATH)['city_name'])
    for city_name in city_list:
        input_csv = os.path.join(
            LANDUSE_CHANGE_DIR,
            f'{city_name}_sat_image_landuse_change_2012_2018_urbancore.csv',
        )
        if not os.path.exists(input_csv):
            print(f'Missing input file: {input_csv}')
            continue

        df_input = pd.read_csv(input_csv).drop_duplicates(subset=['best_image_name']).reset_index(drop=True)

        for idx in range(len(df_input)):
            row = df_input.iloc[idx]
            identifier = str(row['fua_code'])
            generated_grid_points_csv = os.path.join(GENERATED_GRID_POINTS_ROOT, city_name, f'{identifier}.csv')
            if not os.path.exists(generated_grid_points_csv):
                print(f'Missing grid-point CSV: {generated_grid_points_csv}')
                continue
            pd_csv = pd.read_csv(generated_grid_points_csv)

            cache_dir = os.path.join(PANO_CACHE_ROOT, city_name)
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, f'pano_cache_{identifier}.pkl')

            latlon_to_panos = collect_all_panos_parallel(
                pd_csv,
                max_workers=MAX_FETCH_WORKERS,
                cache_file=cache_file,
                max_panos_per_point=MAX_PANOS_PER_POINT,
            )
            latlon_to_panos = fill_missing_dates_parallel(
                latlon_to_panos,
                max_workers=MAX_DATE_FILL_WORKERS,
                qps=DATE_FILL_QPS,
            )

            out_csv = os.path.join(DOWNLOADED_STV_ROOT, city_name, identifier, 'street_image_list.csv')
            os.makedirs(os.path.dirname(out_csv), exist_ok=True)
            if os.path.exists(out_csv) and os.path.getsize(out_csv) > 20:
                already_df = pd.read_csv(out_csv)
            else:
                already_df = pd.DataFrame({})

            selected_panos = select_panos_by_years(
                latlon_to_panos,
                pd_csv,
                already_df=already_df,
                max_panos_per_year=MAX_PANOS_PER_YEAR,
            )
            final_pd = download_selected_panos(city_name, identifier, selected_panos, max_workers=MAX_DOWNLOAD_WORKERS)
            pd.concat([already_df, pd.DataFrame(final_pd)], ignore_index=True).to_csv(out_csv, index=False)


if __name__ == '__main__':
    main()
