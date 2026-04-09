import os
import json
import random
import pandas as pd
import numpy as np
import tqdm
from collections import defaultdict

random.seed(42)

city_csv = pd.read_csv('../../UrbanAtlas/European_Countries_VS_Cities.csv')
city_csv = pd.concat([city_csv, pd.DataFrame([{
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "New Country"
}])], ignore_index=True)

TARGET_CITIES = list(city_csv['city_name'])
INDICATORS = ['safety','lively','wealthy','beautiful','boring','depressing']
NUM_STV_LIST = [4]#, 10]
BASE_DIR1 = '../../placepulse_models/outputs/output_stv_selected'
BASE_DIR2 = '../../placepulse_models/outputs/output_stv_selected_urban_sup'

restriction_list = [
    "Provide a value between 0.0 and 10.0 with exactly one decimal place. Do not include any text or explanation.",
    "Output only a numerical value from 0.0 to 10.0 with one decimal place, nothing else.",
    "Respond strictly with a number between 0.0 and 10.0, rounded to one decimal. No further text.",
    "Give a single numeric value from 0.0 to 10.0 with one decimal place only, without explanation.",
    "Provide just one number in the range 0.0 to 10.0, rounded to one decimal. Do not write any other text."
]

pp2_context = (
    "PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images "
    "to judge perceptions of urban environments. It defines six perceptual dimensions: 'safe', 'lively', "
    "'beautiful', 'wealthy', 'boring', and 'depressing'. Each image receives a perceptual score derived from "
    "these pairwise comparisons, typically normalized. Interpret the indicator as the PlacePulse 2.0 perceptual score."
)

# === reference CSV ===
sat_reference_csv_path = "../inputs/generated_QA/all_cities_yearly_sat_scores.csv"   #
ref_df = pd.read_csv(sat_reference_csv_path)

ref_dict = {
    (r.city, int(r.year), r.sat_image_name, r.indicator, int(r.num_stv)): float(r.mean_score)
    for r in ref_df.itertuples(index=False)
}

score_cache = {ind: {} for ind in INDICATORS}
def preload_score_cache_for_city(city_name):
    for ind in INDICATORS:
        for base_dir in (BASE_DIR1, BASE_DIR2):
            dir_path = os.path.join(base_dir, city_name)
            if not os.path.isdir(dir_path):
                continue
            for fname in os.listdir(dir_path):
                suffix = f"_street_view_images_{ind}.csv"
                if not fname.endswith(suffix):
                    continue
                key_name = fname.replace(suffix, "") + "_street_view_images"
                fullpath = os.path.join(dir_path, fname)
                try:
                    df = pd.read_csv(fullpath, usecols=['img_path', f'{ind}_score'])
                except Exception:
                    continue
                basename_scores = {os.path.basename(p): float(s) for p, s in zip(df['img_path'], df[f'{ind}_score'])}
                score_cache[ind][key_name] = basename_scores

# ---------- ä¸»æµç¨‹ ----------
for city_row in tqdm.tqdm(city_csv.itertuples(index=False), desc="cities"):
    city_name = city_row.city_name
    if city_name not in TARGET_CITIES:
        continue

    sat0_path = f"../inputs/sat_stv_list_dir/{city_name}_sat_stv_list.csv"
    sat1_path = f"../inputs/sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv"
    if not os.path.exists(sat0_path) and not os.path.exists(sat1_path):
        print(f"[WARN] no sat-stv list for {city_name}")
        continue

    dfs = []
    if os.path.exists(sat0_path):
        dfs.append(pd.read_csv(sat0_path))
    if os.path.exists(sat1_path):
        dfs.append(pd.read_csv(sat1_path))
    sat_stv_corr_csv = pd.concat(dfs, ignore_index=True)

    grouped = sat_stv_corr_csv.groupby(['year', 'sat_image_name']).agg({
        'identifier': 'first',
        'stv_image_name': lambda x: list(x)
    }).reset_index()

    preload_score_cache_for_city(city_name)

    output_dir = f'../outputs/single_year/{city_name}/'
    os.makedirs(output_dir, exist_ok=True)
    entries_dict = {(ind, n): [] for ind in INDICATORS for n in NUM_STV_LIST}

    for grp in tqdm.tqdm(grouped.itertuples(index=False), total=len(grouped), desc=f"{city_name} sat_images"):
        year = grp.year
        sat_image_name = grp.sat_image_name
        identifier = grp.identifier
        stv_full_list = grp.stv_image_name
        stv_basenames = [os.path.basename(x) for x in stv_full_list]
        sat_image_stem = os.path.splitext(sat_image_name)[0]
        key = (identifier if str(identifier).lower() != 'none' else sat_image_stem) + "_street_view_images"

        for n in NUM_STV_LIST:
            for ind in INDICATORS:
                if key not in score_cache[ind]:
                    continue
                scores_dict = score_cache[ind][key]
                candidates = [b for b in stv_basenames if b in scores_dict]
                if len(candidates) < n:
                    continue

                sampled = random.sample(candidates, n)
                basename_to_full = {os.path.basename(x): x for x in stv_full_list}
                sampled_full_paths = [basename_to_full[b] for b in sampled]

                possible_refs = [
                    (k, v)
                    for k, v in ref_dict.items()
                    if k[0] == city_name and int(k[1]) == int(year)
                    and k[2] == sat_image_name and k[3] == ind
                    and int(k[4]) >= 4   #
                ]

                if not possible_refs:
                    continue

                ref_key, reference_value = random.choice(possible_refs)

                n = 4
                if key not in score_cache[ind]:
                    continue
                scores_dict = score_cache[ind][key]
                candidates = [b for b in stv_basenames if b in scores_dict]
                if len(candidates) < n:
                    continue
                sampled = random.sample(candidates, n)

                templates = [
f"Suppose you are a vision expert for sensing urban environment from human perspectives. You are given {n + 1} images of a region: the first is a satellite image from year {year}, followed by {n} street views from the same year. Using the observable features in the images together with the additional information provided, analyze the {ind} value using PlacePulse 2.0 dataset as the reference for this area.",
f"Suppose you are a vision expert for sensing urban environment from human perspectives. Examine {n + 1} images from the same region: 1 satellite image from year {year}, and {n} street views from the same year. Consider both the imagery content and the supplementary details given, provide your assessment of the {ind} value using PlacePulse 2.0 dataset as the reference for this area.",
f"Suppose you are a vision expert for sensing urban environment from human perspectives. Consider the {n + 1} images provided for the region: the first is a satellite image from year {year}, and the remaining {n} are street views from the same year. Using the observable features in the images together with the additional information provided, estimate the {ind} value for this area using PlacePulse 2.0 dataset as the reference.",
f"Suppose you are a vision expert for sensing urban environment from human perspectives. You are given {n + 1} images for the same region, including 1 satellite and {n} street views from year {year}. Using the observable features in the images together with the additional information provided, infer the {ind} value for this area using PlacePulse 2.0 dataset as the reference.",
f"Suppose you are a vision expert for sensing urban environment from human perspectives. Analyze {n + 1} images from the region: first a satellite image from year {year}, then {n} street views from the same year. Using the observable features in the images together with the additional information provided, determine the {ind} value for this area using PlacePulse 2.0 dataset as the reference."
                ]

                entry = {
                    "id": f"{ind}_{len(entries_dict[(ind, n)])}",
                    "sat_image_name": sat_image_name,
                    "identifier": identifier,
                    "year": year,
                    "images": [sat_image_name] + sampled_full_paths,
                    "prompt": f"{random.choice(templates)}\n{pp2_context}\n{random.choice(restriction_list)}",
                    "reference": round(reference_value, 1)
                }
                entries_dict[(ind, n)].append(entry)

    for (ind, n), entries in entries_dict.items():
        out_path = os.path.join(output_dir, f"{city_name}_{ind}_single_year_stv_num_{n}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=4, ensure_ascii=False)

    print(f"[DONE] {city_name} -> wrote JSONs to {output_dir}")