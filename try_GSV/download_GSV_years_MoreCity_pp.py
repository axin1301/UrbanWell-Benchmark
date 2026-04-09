from tqdm import tqdm
from configs import *
import os
import pickle
import pandas as pd
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import streetview
import requests
import time

Maps_API_KEY = GOOGLE_KEY_MY

def fetch_pano(lat, lon):
    try:
        panos = streetview.search_panoramas(lat=lat, lon=lon)
        return (lat, lon, panos)
    except Exception as e:
        return (lat, lon, [])

def get_pano_date(pano_id, api_key=Maps_API_KEY, retries=3, delay=1):
    url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    params = {"pano": pano_id, "key": api_key}
    attempt = 0
    while attempt < retries:
        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return data.get("date", None)
        except requests.RequestException:
            attempt += 1
            time.sleep(delay)
        except ValueError:
            return None
    return None

def collect_all_panos_parallel(pd_csv, max_workers=8, cache_file=None, max_panos_per_point=4):
    # bbox
    min_lat, max_lat = pd_csv['latitude'].min(), pd_csv['latitude'].max()
    min_lon, max_lon = pd_csv['longitude'].min(), pd_csv['longitude'].max()
    def in_bbox(pano):
        return (min_lat <= pano.lat <= max_lat) and (min_lon <= pano.lon <= max_lon)

    if cache_file and os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            latlon_to_panos = pickle.load(f)
    else:
        latlon_to_panos = {}

    latlon_list = [(row['latitude'], row['longitude']) for _, row in pd_csv.iterrows()]
    new_fetch_needed = []
    for lat, lon in latlon_list:
        if (lat, lon) not in latlon_to_panos:
            new_fetch_needed.append((lat, lon))
        else:
            if any(pano.date is None for pano in latlon_to_panos[(lat, lon)]):
                new_fetch_needed.append((lat, lon))

    if new_fetch_needed:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for lat, lon, panos in tqdm(executor.map(lambda xy: fetch_pano(*xy), new_fetch_needed),
                                        total=len(new_fetch_needed)):
                panos = [p for p in panos if in_bbox(p)]
                panos_with_date = [p for p in panos if p.date]
                panos_none_date = [p for p in panos if not p.date]
                panos = (panos_with_date + panos_none_date)[:max_panos_per_point]
                latlon_to_panos[(lat, lon)] = panos

    if cache_file:
        with open(cache_file, "wb") as f:
            pickle.dump(latlon_to_panos, f)

    return latlon_to_panos

# ----------------------------------------
def fill_missing_dates_parallel(latlon_to_panos, max_workers=16, qps=10):
    pano_list = []
    for panos in latlon_to_panos.values():
        for pano in panos:
            if pano.date is None:
                pano_list.append(pano)
    print(f"{len(pano_list)} panos")

    semaphore = threading.Semaphore(qps)  #
    def task(pano):
        with semaphore:
            pano.date = get_pano_date(pano.pano_id)
            time.sleep(1.0 / qps)  #
        return pano

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(tqdm(executor.map(task, pano_list), total=len(pano_list)))

    return latlon_to_panos

import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

def select_diverse_panos(year_panos, k=4):
    if len(year_panos) <= k:
        return year_panos  #

    selected = [year_panos[0]]  #
    candidates = year_panos[1:]

    while len(selected) < k and candidates:
        dists = []
        for pano in candidates:
            min_dist = min(haversine(pano.lat, pano.lon, s.lat, s.lon) for s in selected)
            dists.append((min_dist, pano))

        dists.sort(reverse=True, key=lambda x: x[0])
        selected.append(dists[0][1])
        candidates.remove(dists[0][1])

    return selected

def select_panos_by_years(latlon_to_panos, pd_csv, already_df=None, max_panos_per_year=4):
    #
    min_lat, max_lat = pd_csv['latitude'].min(), pd_csv['latitude'].max()
    min_lon, max_lon = pd_csv['longitude'].min(), pd_csv['longitude'].max()
    def in_bbox(pano):
        return (min_lat <= pano.lat <= max_lat) and (min_lon <= pano.lon <= max_lon)

    #
    existing_year_counts = {}
    if already_df is not None and not already_df.empty:
        existing_year_counts = already_df.groupby("year")["id"].nunique().to_dict()

    #
    year_counter = Counter()
    for panos in latlon_to_panos.values():
        for pano in panos:
            if pano.date:
                try:
                    year_counter[int(pano.date[:4])] += 1
                except:
                    pass
    sorted_years = [y for y, _ in year_counter.most_common()]

    selected_panos = []
    for year in sorted_years:
        #
        if year in existing_year_counts and 2 <= existing_year_counts[year] <= 4:
            continue

        year_panos = [p for panos in latlon_to_panos.values()
                      for p in panos if p.date and int(p.date[:4]) == year and in_bbox(p)]
        if len(year_panos) >= 4:
            chosen = select_diverse_panos(year_panos, k=max_panos_per_year)
            selected_panos.extend(chosen)
        elif len(year_panos) in [2, 3]:
            selected_panos.extend(year_panos)
        else:
            continue

    return selected_panos

def download_one_image(pano, head, base_dir, formatted_lat, formatted_lon):
    try:
        response = streetview.get_streetview(
            pano_id=pano.pano_id,
            heading=head,
            fov=90,
            pitch=0,
            api_key=Maps_API_KEY
        )
        image_name = f"street_view_{formatted_lat}_{formatted_lon}_{pano.lat}_{pano.lon}_{pano.date[:4]}_{pano.date}_{pano.pano_id}_{head}.jpg"
        file_path = os.path.join(base_dir, image_name)
        response.save(file_path, "jpeg")
        return {
            'id': pano.pano_id,
            'query_lat': formatted_lat,
            'query_lon': formatted_lon,
            'returned_lat': pano.lat,
            'returned_lon': pano.lon,
            'date': pano.date,
            'year': int(pano.date[:4]),
            'heading': head,
            'image_name': image_name
        }
    except:
        return None

def download_selected_panos(city_name, identifier, selected_panos, max_workers=16):
    base_dir = f"outputs/downloaded_stv_selected/{city_name}/{identifier}/street_view_images/"
    os.makedirs(base_dir, exist_ok=True)
    existing_files = set(os.listdir(base_dir))

    tasks = []
    for pano in selected_panos:
        for head in [0, 90, 180, 270]:
            image_name = f"street_view_{pano.lat}_{pano.lon}_{pano.date[:4]}_{pano.date}_{pano.pano_id}_{head}.jpg"
            if image_name not in existing_files:
                tasks.append((pano, head, base_dir, pano.lat, pano.lon))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(executor.map(lambda args: download_one_image(*args), tasks), total=len(tasks)))

    return [r for r in results if r]


city_list = list(pd.read_csv('../UrbanAtlas/City_list.csv')['city_name'])
for city_name in city_list:
    # if city_name == 'BERLIN':
    #     continue
    input_csv = f"../download_sat/outputs/Landuse_Change_2012_2018_urbancore/{city_name}_sat_image_landuse_change_2012_2018_urbancore.csv"
    df_input = pd.read_csv(input_csv).drop_duplicates(subset=["best_image_name"]).reset_index(drop=True)

    for idx in range(len(df_input)):
        row = df_input.iloc[idx]
        identifier = str(row['fua_code'])
        generated_grid_points_csv = f"outputs/generated_grid_points/{city_name}/{identifier}.csv"
        pd_csv = pd.read_csv(generated_grid_points_csv)

        os.makedirs(f"outputs/PANO_ID_PKL/{city_name}", exist_ok=True)
        cache_file = f"outputs/PANO_ID_PKL/{city_name}/pano_cache_{identifier}.pkl"

        latlon_to_panos = collect_all_panos_parallel(pd_csv, max_workers=32, cache_file=cache_file)
        latlon_to_panos = fill_missing_dates_parallel(latlon_to_panos, max_workers=32, qps=10)

        out_csv = f"outputs/downloaded_stv_selected/{city_name}/{identifier}/street_image_list.csv"
        os.makedirs(os.path.dirname(out_csv), exist_ok=True)
        if os.path.exists(out_csv) and os.path.getsize(out_csv) > 20:
            already_df = pd.read_csv(out_csv)
        else:
            already_df = pd.DataFrame({})

        selected_panos = select_panos_by_years(latlon_to_panos, pd_csv, already_df=already_df)

        final_pd = download_selected_panos(city_name, identifier, selected_panos, max_workers=32)

        pd.concat([already_df, pd.DataFrame(final_pd)], ignore_index=True).to_csv(out_csv, index=False)



