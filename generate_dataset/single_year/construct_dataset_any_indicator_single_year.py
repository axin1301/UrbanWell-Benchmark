import os
import json
import random
import pandas as pd
import tqdm
from indicator_col_name_in_prompt import *  # col_name_dict, indicator_name_dict, add_info_indicator

random.seed(42)

def get_path(city_name, indicator, year):
    if indicator == 'CO2':
        if year < 2014:
            return None
        return f"../../extract_EEA/outputs/generated_CO2/{city_name}/{city_name}_CO2_{year}.csv"

    elif indicator == 'NO2':
        if year < 2014:
            return None
        return f"../../extract_EEA/outputs/generated_NO2/{city_name}/{city_name}_NO2_{year}.csv"

    elif indicator == 'QSI':
        if year != 2016:
            return None
        return f"../../extract_EEA/outputs/generated_QSI/{city_name}/{city_name}_QSI_{year}.csv"

    elif indicator == 'PM25':
        if year < 2014:
            return None
        return f"../../extract_EEA/outputs/generated_PM25/{city_name}/{city_name}_PM25_{year}.csv"

    elif indicator in ['network_density_km_per_km2', 'road_length']:
        if year < 2014 or year > 2024:
            return None
        year_str = str(year - 2000 + 1) + "0101"
        return f"../../OSM_data/outputs/road-output/{city_name}_{year_str}.csv"
    
    elif indicator in ['avg_dist_to_restaurant','avg_dist_to_supermarket']:
        if year < 2014 or year > 2024:
            return None
        year_str = str(year - 2000 + 1) + "0101"
        return f"../../OSM_data/outputs/accessability_output_only_POI_update/{city_name}_{year_str}.csv"

    elif indicator == 'landuse_mix':
        if year not in [2012, 2018]:
            return None
        return f'../../UrbanAtlas/outputs/output_LU_mix_dir/{city_name}_LU_mix_{year}.csv'

    elif indicator == 'economic':
        if year < 2014:
            return None
        return f'../../OSM_data/outputs/output_economic_dir_update/{city_name}_economic_urbancore_{year}.csv'


    elif indicator == 'NDVI':
        if year not in [2018, 2020, 2022, 2024]:
            return None
        return f"../../extract_EEA/outputs/generated_NDVI/{city_name}/{city_name}_NDVI_{year}.csv"

    return None

def single_image_templates(year, prompt_indicator):
    return [
        f"Suppose you are a vision expert. You are given a satellite image of a region from year {year}. Using the observable features in the image, please estimate the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert. Examine the satellite image content from year {year}. Provide your estimation of the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert. Consider the satellite image provided for the region. Estimate the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert. You are given a satellite image for the region. Based on that, estimate the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert. Analyze the satellite image content from year {year}, and estimate the {prompt_indicator} for this area."
    ]


def multi_image_templates(num_stv_actual, year, prompt_indicator):
    return [
        f"Suppose you are a vision expert specializing in socioeconomic and environmental analysis. You are given {num_stv_actual + 1} images of a region: the first is a satellite image from year {year}, followed by {num_stv_actual} street views from the same year. Using the observable features in the images, estimate the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert specializing in socioeconomic and environmental analysis. Examine {num_stv_actual + 1} images from the same region: 1 satellite image from year {year}, and {num_stv_actual} street views from the same year. Consider the imagery content, and provide your estimation of the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert specializing in socioeconomic and environmental analysis. Consider the {num_stv_actual + 1} images provided for the region: the first is a satellite image from year {year}, and the remaining {num_stv_actual} are street views from the same year. Using the observable features in the images, estimate the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert specializing in socioeconomic and environmental analysis. You are given {num_stv_actual + 1} images for the same region, including 1 satellite and {num_stv_actual} street views from year {year}. Using the observable features in the images, estimate the {prompt_indicator} for this area.",
        f"Suppose you are a vision expert specializing in socioeconomic and environmental analysis. Analyze {num_stv_actual + 1} images from the region: first a satellite image from year {year}, then {num_stv_actual} street views from the same year. Using the observable features in the images, estimate the {prompt_indicator} for this area."
    ]

#
restriction_list = [
    "Answer only with the numeric value. Do not explain or write anything else.",
    "Provide strictly the number representing the indicator. No extra text or explanation.",
    "Reply only with the numeric value. Nothing else should be included.",
    "Your answer must be exactly the numeric value of the indicator, without any words or explanation.",
    "Output only the numeric value. Do not include any other text."
]

#
for number_of_stv in [4]:# [10]:
    city_csv = pd.read_csv('../../UrbanAtlas/European_Countries_VS_Cities.csv')
    new_row = {
        "city_name": "HELSINKI",
        "city_full_name": "New City Full Name",
        "province": "New Province",
        "note": "Some note",
        "country_name": "New Country"
    }

    #
    new_row_df = pd.DataFrame([new_row])

    # 
    city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

    #
    # city_csv.loc[len(city_csv)] = ["HELSINKI", "New City Full Name", "New Province", "Some note", "New Country"]

    for city in tqdm.tqdm(city_csv.itertuples(index=False)):
        if city.city_name in ['PRISTINA', 'LEFKOSIA', 'SARAJEVO']:
            continue

        #
        try:
            sat0 = pd.read_csv(f"../inputs/sat_stv_list_dir/{city.city_name}_sat_stv_list.csv")
            sat1 = pd.read_csv(f"../inputs/sat_stv_list_dir/{city.city_name}_sat_stv_list_no_stv.csv")
            # sat_stv_corr_csv0 = pd.read_csv(f"../inputs/sat_stv_list_dir/{city.city_name}_sat_stv_list.csv")
            sat_stv_corr_csv_full = pd.concat([sat0, sat1], ignore_index=True)
            valid_sat_image_names = list(pd.read_csv('../../download_sat/outputs/valid_image_lists/valid_image_lists.csv')['valid_image_name'])
            sat_stv_corr_csv = sat_stv_corr_csv_full[sat_stv_corr_csv_full['sat_image_name'].isin(valid_sat_image_names)].reset_index(drop = True)

        except FileNotFoundError:
            continue

        # output_dir = f'generated_QA/{city.city_name}/'
        output_dir = f'generated_QA_update/{city.city_name}/'
        os.makedirs(output_dir, exist_ok=True)

        indicator_list =  [
            'CO2', 'NO2', 'PM25', 'QSI', 'NDVI',
            'network_density_km_per_km2','avg_dist_to_restaurant',
            'avg_dist_to_supermarket',
            'economic', 'landuse_mix'
        ]

        # indicator_list = ['network_density_km_per_km2', 'road_length', 'avg_dist_to_restaurant', 'avg_dist_to_supermarket','economic']
        # [
        #     'CO2', 'NO2', 'QSI', 'NDVI',
        #     'network_density_km_per_km2', 'intersection_density_per_km2',
        #     'avg_dist_to_restaurant', 'avg_dist_to_hotel',
        #     'avg_dist_to_supermarket', 'avg_dist_to_hospital',
        #     'economic', 'landuse_mix'
        # ] #'PM25', 

        for indicator in indicator_list:
            data = []
            for year in range(2012, 2025):
                input_csv_path = get_path(city.city_name, indicator, year)
                if not input_csv_path or not os.path.exists(input_csv_path):
                    continue

                df = pd.read_csv(input_csv_path)

                col_indicator = col_name_dict.get(indicator, indicator)
                prompt_indicator = indicator_name_dict.get(indicator, indicator.replace('_', ' '))
                need_add_info = add_info_indicator.get(indicator, '')

                for row in df.itertuples(index=False):
                    image_name_1 = getattr(row, 'image_name', None) or getattr(row, 'ImageFileName', None) or row.best_image_name
                    value1_ = round(getattr(row, col_indicator), 3)
                    if indicator == 'NDVI':
                        if value1_ < -1 or value1_ > 1:
                            continue

                    if indicator == 'QSI' and pd.isna(value1_):
                        continue

                    sat_stv_matched = sat_stv_corr_csv.query("sat_image_name == @image_name_1 and year == @year")
                    if sat_stv_matched.empty:
                        continue

                    stv_list = list(sat_stv_matched['stv_image_name'])
                    if len(stv_list) >= number_of_stv:
                        stv_random = random.sample(stv_list, number_of_stv)
                    else:
                        stv_random = stv_list
                    num_stv_actual = len(stv_random)

                    identifier = sat_stv_matched['identifier'].iloc[0]

                    if num_stv_actual <= 1:
                        pairwise_templates = single_image_templates(year, prompt_indicator)
                    else:
                        pairwise_templates = multi_image_templates(num_stv_actual, year, prompt_indicator)

                    entry = {
                        "id": f"{indicator}_{len(data)}",
                        "sat_image_name": image_name_1,
                        "identifier": identifier,
                        "year": year,
                        "images": [image_name_1] + stv_random,
                        "prompt": f"{random.choice(pairwise_templates)}\n{need_add_info}\n{random.choice(restriction_list)}",
                        "reference": value1_,
                    }
                    data.append(entry)


            with open(os.path.join(output_dir, f"{city.city_name}_{indicator}_single_year_stv.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)