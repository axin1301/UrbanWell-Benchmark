import json
import pandas as pd
import random
from similar_map_LU import *
random.seed(42)
from collections import defaultdict
import tqdm

def generate_landuse_change_options(lu_from, lu_to, lu_list, similar_map, n_wrong=3):
    """
        lu_from: previous year landuse
        lu_to: last year landuse
        lu_list: landuse list
        similar_map: similar land use (dict)
        n_wrong: max try times = 3

        options_str: (A. xxx\nB. xxx...)
        correct_idx: (A/B/C/D)
    """

    wrong_choices = []

    for _ in range(n_wrong):
        if random.random() < 0.5:

            possible_from = [lu for lu in lu_list if lu != lu_from and lu != lu_to]
            if possible_from:
                wrong_from = random.choice(possible_from)
                wrong_choices.append(f"from {wrong_from} to {lu_to}")
        else:

            similar_candidates = similar_map.get(lu_to, [])
            possible_to = [lu for lu in similar_candidates if lu != lu_to and lu != lu_from]
            if not possible_to:
                possible_to = [lu for lu in lu_list if lu != lu_to and lu != lu_from]
            wrong_to = random.choice(possible_to)
            wrong_choices.append(f"from {lu_from} to {wrong_to}")

    while len(wrong_choices) < n_wrong:
        possible_to = [lu for lu in lu_list if lu not in {lu_from, lu_to}]
        wrong_to = random.choice(possible_to)
        wrong_choices.append(f"from {lu_from} to {wrong_to}")

    correct_choice = f"from {lu_from} to {lu_to}"

    all_choices = wrong_choices + [correct_choice]
    random.shuffle(all_choices)

    options_str = "\n".join([f"{chr(65+i)}. {lu}" for i, lu in enumerate(all_choices)])
    correct_idx = chr(65 + all_choices.index(correct_choice))

    return options_str, correct_idx


#################################
number_of_stv = 4
used_year_num = 2
num_with_multiple_images_t = 1

city_csv = pd.read_csv('../../UrbanAtlas/European_Countries_VS_Cities.csv')
new_row = {
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "New Country"
}


new_row_df = pd.DataFrame([new_row])

city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

for i in range(len(city_csv)):  #
    city_name = city_csv.at[i, 'city_name']
    city_full_name = city_csv.at[i, 'city_full_name']
    province = city_csv.at[i, 'province']
    note = city_csv.at[i, 'note']
    country_name = city_csv.at[i, 'country_name']
    if city_name in ['PRISTINA','LEFKOSIA','SARAJEVO']:
        continue

    input_csv_path = f'generated_QA\\{city_name}/' + f"LU_{city_name}_MC_single_year.json"
    lu_list = landuse_list

    with open(input_csv_path, 'r', encoding='utf-8') as file:
        single_year_data = json.load(file)

    grouped_data = defaultdict(list)
    for item in single_year_data :
        grouped_data[item['sat_image_name']].append(item)

    count = 0

    reconstructed_data = []
    remained_items = []
    for sat_image_name, items in grouped_data.items():
       
        top_n_items = []
        if len(items) >= used_year_num:
            years = sorted([item['year'] for item in items])
            #
            sorted_items = sorted(items, key=lambda x: len(x['images']), reverse=True)
            #
            top_n_items.extend(sorted_items[:used_year_num])

            #
            #
            selected_items = sorted(top_n_items, key=lambda x: x['year'])

            #
            num_with_multiple_images = sum(len(item['images']) > 1 for item in selected_items)

            if num_with_multiple_images < num_with_multiple_images_t:
                #
                continue

            # for item in selected_items:
            #     print(item)
            # print('-----------------------------------------------')

            all_references = [item['landuse'] for item in selected_items]
            all_years = [item['year'] for item in selected_items]

            all_images_output = [item['images'] for item in selected_items[-1:]]

            #
            merged_images = [] #[img for item in selected_items for img in item['images']]
            options, correct_idx = generate_landuse_change_options(all_references[0], all_references[1], lu_list,similar_map)

            header_templates = [
                f"""Suppose you are a vision expert. You are given a series of images for a region.
            There are a total of {used_year_num} years of data, from {all_years[0]} to {all_years[-1]}.

            **Here are the images for each year:**""",

                f"""You are an analyst tasked with examining satellite and street-view images over time.
            The dataset spans {used_year_num} years, ranging from {all_years[0]} to {all_years[-1]}.

            The following lists the imagery for each year:""",

                f"""As a remote-sensing specialist, you are provided with {used_year_num} years of imagery,
            covering the period {all_years[0]} to {all_years[-1]}.

            Below you will find the available images by year:""",

                f"""Imagine you are studying urban change using geospatial data. The dataset includes {used_year_num} yearly snapshots,
            from {all_years[0]} through {all_years[-1]}.

            Each yearâ€™s imagery is given below:""",

                f"""You are provided with temporal visual data of a region, covering {used_year_num} years
            ({all_years[0]} â†’ {all_years[-1]}).

            For each year, the following images are listed:"""
            ]

            #
            question_template = random.choice(header_templates)

            #
            for item in selected_items:
                #
                year = item['year']
                #
                lst = item['images']
                target = "no_stv_image"
                lst = [item for item in lst if target not in item]
                item['images'] = lst
                sat_image = item['images'][0] #
                if len(item['images']) > 1:
                    street_view_images = item['images'][1:number_of_stv+1] #
                    #
                    image_description = f"1 satellite image and {min(number_of_stv, len(item['images'])-1)} street view image(s)"
                else:
                    street_view_images = []
                    image_description = "1 satellite image"
    
                #
                question_template += f'''
                Year {year}:
                    - Images provided: {image_description}
                '''
                sat_image_row = sat_image.split('_')[1]
                sat_image_stem = sat_image.split('.')[0]
                tmp_identifier = item['identifier']

                sat_image_path = '../../download_sat/outputs/' + f'downloaded_sat_{year}_zoom_{16}/{city_name}/{year}-07-31/{city_name}/{16}/{sat_image_row}/{sat_image}'
                merged_images.append(sat_image_path)

                if item['identifier'] == 'none':
                    stv_root_path = f'../../try_GSV/outputs/downloaded_stv_selected/{city_name}/{sat_image_stem}/street_view_images/'
                else:
                    stv_root_path = f'../../try_GSV/outputs/downloaded_stv_selected/{city_name}/{tmp_identifier}/street_view_images/'

                street_view_images_paths = [stv_root_path + x for x in street_view_images]
                merged_images = merged_images + street_view_images_paths

                remained_items.append(item)

            question_part_final_list = [
            f'''Please analyze the images and provide your estimate of the land use change that best matches the observed difference.''',
            f'''Focus on the imagery and choose the correct land use change type.''',
            f'''Now consider the data and determine the most suitable land use change.''',
            f'''Evaluate the imagery and identify the land use change that best describes the transition.''']

            question_part_final = random.choice(question_part_final_list)
            question_template += question_part_final

            restriction_list = [
                'Only output A, B, C, or D. Do not give any explanation.',
                'Choose the correct land use category from A, B, C, or D. Respond with the letter only.',
                'Answer strictly with A, B, C, or D, without any explanation.',
                'Reply only with one of: A, B, C, or D. No further text is required.',
                'Output only one choice among A, B, C, or D. Do not provide reasoning.'
            ]

            new_element = {
                'sat_image_name': sat_image,
                'years': all_years,
                'ids': f"LUChange_{count}",
                'images': merged_images, #
                'prompt': question_template + '\n' + options +'\n' + random.choice(restriction_list), #
                'references': correct_idx #
            }
            reconstructed_data.append(new_element)
            count+=1
            # if count >= limit:
            #     break  # 
        else:
            #
            # reconstructed_data.extend(items)
            continue

    # print(reconstructed_data)
    output_dir = f'../outputs/multi_year_type1/{city_name}/'
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_dir + f"LU_{city_name}_timeline.json", "w", encoding="utf-8") as f:
        json.dump(reconstructed_data, f, indent=4, ensure_ascii=False)

    print("saved output.json")



