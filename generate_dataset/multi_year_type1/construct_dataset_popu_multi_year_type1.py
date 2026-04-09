import json
import pandas as pd
import random
import os
from collections import defaultdict

random.seed(42)

used_year_num = 4
max_stv_images = 4
num_with_multiple_images_t = 2

indicator = 'population'

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

    sat_stv_corr_csv = pd.read_csv(f"../inputs/sat_stv_list_dir/{city_name}_sat_stv_list.csv")
    # city_name,identifier,sat_image_name,year,stv_image_name

    output_dir = f'../outputs/multi_year_type1/{city_name}/'
    import os
    os.makedirs(output_dir, exist_ok=True)

    single_year_data_path = output_dir + f"{city_name}_{indicator}_single_year_stv_{max_stv_images}.json"

    with open(single_year_data_path, 'r', encoding='utf-8') as file:
        single_year_data = json.load(file)

    # print(single_year_data[1])

    # 1.
    grouped_data = defaultdict(list)
    for item in single_year_data :
        grouped_data[item['sat_image_name']].append(item)

    count = 0
    limit = 2
    # 2.
    reconstructed_data = []
    remained_items = []
    for sat_image_name, items in grouped_data.items():
        #
        top_n_items = []
        if len(items) >= used_year_num:
            years = sorted([item['year'] for item in items])

            sorted_items = sorted(items, key=lambda x: len(x['images']), reverse=True)
            top_n_items.extend(sorted_items[:used_year_num])
            selected_items = sorted(top_n_items, key=lambda x: x['year'])
            num_with_multiple_images = sum(len(item['images']) > 1 for item in selected_items)

            if num_with_multiple_images < num_with_multiple_images_t:
                continue

            all_references = [item['reference'] for item in selected_items]
            all_years = [item['year'] for item in selected_items]
            
            all_images_output = [item['images'] for item in selected_items[-1:]]

            merged_images = [] #[img for item in selected_items for img in item['images']]

            # question_template = f'''
            # Suppose you are a vision expert. You are given a series of images for a region.
            # There are a total of {used_year_num} years of data, from {all_years[0]} to {all_years[-1]}.

            # **Here are the images and data for each year:**
            # '''

            header_templates = [
f"""Suppose you are a vision expert specializing in socioeconomic estimation. You are given a series of images for a region. There are a total of {used_year_num} years of data, from {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below. **Here are the images and data for each year:**""",

f"""You are an analyst specializing in socioeconomic estimation and tasked with examining satellite and street-view images of a region over time. The dataset spans {used_year_num} years, ranging from {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below. The following lists the imagery and {indicator} values for each year:""",

f"""As a remote-sensing specialist specializing in socioeconomic estimation, you are provided with {used_year_num} years of imagery of a region, covering the period {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below.Below you will find the available images and historical {indicator} numbers by year:""",

f"""Imagine you are studying urban change using geospatial data for a region. The dataset includes {used_year_num} yearly snapshots, from {all_years[0]} through {all_years[-1]}. The images are provided to you as per the instructions below. Each yearâ€™s imagery and the corresponding {indicator} number are given below:""",

f"""You are provided with temporal visual data of a region, covering {used_year_num} years ({all_years[0]} â†’ {all_years[-1]}). The images are provided to you as per the instructions below. For each year, the following imagery and the reported {indicator} values are listed:"""
            ]

            question_template = random.choice(header_templates)

            #
            for item in selected_items[:-1]:
                # remained_items.append(item)
                year = item['year']
                lst = item['images']
                not_valid_target = "no_stv_image"
                lst = [name for name in lst if not_valid_target not in name]
                item['images'] = lst

                sat_image = item['images'][0] #
                if len(item['images']) > 1:
                    street_view_images = item['images'][1:max_stv_images+1] #
                    #
                    image_description = f"1 satellite image and {min(max_stv_images, len(item['images'])-1)} street view image(s)"
                else:
                    street_view_images = []
                    image_description = "1 satellite image"
    
                #
                question_template += f'''
Year {year}:
    - Images provided: {image_description}
    - Corresponding {indicator} number: {int(item['reference'])}
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

            item = selected_items[-1]
            remained_items.append(item)
            #
            year = item['year']
            lst = item['images']
            not_valid_target = "no_stv_image"
            lst = [name for name in lst if not_valid_target not in name]
            item['images'] = lst
            #
            sat_image = item['images'][0] #
            if len(item['images']) > 1:
                street_view_images = item['images'][1:max_stv_images+1] #

                image_description = f"1 satellite image and {min(max_stv_images, len(item['images'])-1)} street view image(s)"
            else:
                street_view_images = []
                image_description = "1 satellite image"

            sat_image_row = sat_image.split('_')[1]
            sat_image_stem = sat_image.split('.')[0]
            tmp_identifier = item['identifier']
            question_template += f'''
Year {year}:
    - Images provided: {image_description}
                '''
            sat_image_path = '../../download_sat/outputs/' + f'downloaded_sat_{year}_zoom_{16}/{city_name}/{year}-07-31/{city_name}/{16}/{sat_image_row}/{sat_image}'
            merged_images.append(sat_image_path)

            if item['identifier'] == 'none':
                stv_root_path = f'../../try_GSV/outputs/downloaded_stv_selected/{city_name}/{sat_image_stem}/street_view_images/'
            else:
                stv_root_path = f'../../try_GSV/outputs/downloaded_stv_selected/{city_name}/{tmp_identifier}/street_view_images/'

            street_view_images_paths = [stv_root_path + x for x in street_view_images]
            merged_images = merged_images + street_view_images_paths

            question_part_final_list = [
f'''
Please analyze the images for year {all_years[-1]}. Using the {indicator} numbers from the earlier years as context, provide your estimate of the {indicator} value for year {all_years[-1]} for this area.
Return only the numeric value, without any explanation.''',

f'''
Focus on the imagery from year {all_years[-1]}. The historical {indicator} values given above are your reference.
Predict the {indicator} value for {all_years[-1]} for this area and output just the number.''',

f'''
Now consider the data for year {all_years[-1]}. Refer to the {indicator} values in the preceding years to guide your reasoning. Provide only the estimated {indicator} for year {all_years[-1]} for this area as a number.''',

f'''
Look at the images corresponding to year {all_years[-1]}. You may use the prior yearsâ€™ {indicator} values for context. Estimate the {indicator} for {all_years[-1]} for this area and give only the numeric answer.''',

f'''
Evaluate the imagery for year {all_years[-1]}. The earlier yearsâ€™ {indicator} values serve as historical background. Based on this, estimate the {indicator} value for this area for {all_years[-1]}.
Do not add any explanationâ€”output the number only.''']

            question_part_final = random.choice(question_part_final_list)
            question_template += question_part_final

            new_element = {
                'sat_image_name': sat_image,
                'years': all_years,
                'city':city_name,
                'ids': f"{indicator}_{count}",
                'images': merged_images, # 
                'prompt': question_template, #
                'references': int(all_references[-1]) #
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
    with open(output_dir + f"{city_name}_{indicator}_multi_year_type1_stv_num_{max_stv_images}_year_num_{used_year_num}.json", "w", encoding="utf-8") as f:
        json.dump(reconstructed_data, f, indent=4, ensure_ascii=False)

    with open(output_dir + f"{city_name}_{indicator}_single_year_selected_type1_stv_num_{max_stv_images}_year_num_{used_year_num}.json", "w", encoding="utf-8") as f:
        json.dump(remained_items, f, indent=4, ensure_ascii=False)

    print("saved to output.json")





