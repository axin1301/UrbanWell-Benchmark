
import json
import pandas as pd
import random
import os
from indicator_col_name_in_prompt import *
# col_name_dict, indicator_name_dict
import tqdm
from similar_map_LU import *

def generate_landuse_options(correct_lu, lu_list, similar_map, n_wrong=3):
    similar_candidates = similar_map.get(correct_lu, [])
    
    similar_candidates = [lu for lu in similar_candidates if lu in lu_list and lu != correct_lu]
    
    wrong_choices = []
    if len(similar_candidates) >= n_wrong:
        wrong_choices = random.sample(similar_candidates, n_wrong)
    else:
        remaining = [lu for lu in lu_list if lu != correct_lu and lu not in similar_candidates]
        wrong_choices = similar_candidates + random.sample(remaining, n_wrong - len(similar_candidates))
    
    all_choices = wrong_choices + [correct_lu]
    random.shuffle(all_choices)

    options_str = "\n".join([f"{chr(65+i)}. {lu}" for i, lu in enumerate(all_choices)])
    correct_idx = chr(65 + all_choices.index(correct_lu))
    
    return options_str, correct_idx

random.seed(42)

# number_of_stv = 4
for number_of_stv in [4]:#[10]:#[2, 4, 8, 12]:
    # indicator = 'population'

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

    for i in tqdm.tqdm(range(len(city_csv))):  #
        city_name = city_csv.at[i, 'city_name']
        city_full_name = city_csv.at[i, 'city_full_name']
        province = city_csv.at[i, 'province']
        note = city_csv.at[i, 'note']
        country_name = city_csv.at[i, 'country_name']
        
        if city_name in ['PRISTINA','LEFKOSIA','SARAJEVO']:
            continue

        sat_stv_corr_csv0 = pd.read_csv(f"../inputs/sat_stv_list_dir/{city_name}_sat_stv_list.csv") ##
        sat_stv_corr_csv1 = pd.read_csv(f"../inputs/sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv") ##
        sat_stv_corr_csv = pd.concat([sat_stv_corr_csv0, sat_stv_corr_csv1], ignore_index=True)

        # city_name,identifier,sat_image_name,year,stv_image_name

        output_dir = f'../outputs/single_year/{city_name}/'
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for indicator in ['landuse']:
            cnt = 0
            data = []
            
            for year in [2012,2018]:
                input_csv_path = '../../UrbanAtlas/outputs/output_LU_single_year/' + f"{city_name}_LU_{year}.csv"

                # print(input_csv_path)
                if not os.path.exists(input_csv_path):
                    continue
                df = pd.read_csv(input_csv_path)
                num_records = len(df)

                restriction_list = [
                    'Only output A, B, C, or D. Do not give any explanation.',
                    'Choose the correct land use category from A, B, C, or D. Respond with the letter only.',
                    'Answer strictly with A, B, C, or D, without any explanation.',
                    'Reply only with one of: A, B, C, or D. No further text is required.',
                    'Output only one choice among A, B, C, or D. Do not provide reasoning.'
                ]

                for idx, row in df.iterrows():
                    if 'image_name' in df.columns:
                        image_name_1 = row['image_name']
                    elif 'ImageFileName' in df.columns:
                        image_name_1 = row['ImageFileName']
                    else:
                        image_name_1 = row["best_image_name"]
                    
                    lu_list = landuse_list
                    lu_class = row['class_'+str(year)]
                    options, correct_idx = generate_landuse_options(lu_class, lu_list,similar_map)

                    sat_stv_matched = sat_stv_corr_csv[(sat_stv_corr_csv['sat_image_name']==image_name_1) & (sat_stv_corr_csv['year']==year)]
                    # city_name,identifier,sat_image_name,year,stv_image_name

                    stv_image_list = list(sat_stv_matched['stv_image_name'])
                    if len(stv_image_list)>=number_of_stv:
                        number_of_stv_actual = number_of_stv
                        stv_image_random_items = random.sample(stv_image_list, number_of_stv)
                        question_list = [
                            f'Suppose you are a vision expert. You are given a satellite image and {number_of_stv} street view images. Select the most appropriate land use type for this region.',
                            
                            f'Suppose you are a vision expert. You are provided with one satellite image and {number_of_stv} street view images. Identify the land use type of the area.',
                            
                            f'Suppose you are a vision expert. Given the satellite image and {number_of_stv} street view images, determine the most suitable land use type.',
                            
                            f'Suppose you are a vision expert. Look at the satellite image together with {number_of_stv} street view images, and classify the region into the correct land use category.',
                            
                            f'Suppose you are a vision expert. From the satellite image and {number_of_stv} street view images, select the best matching land use type for this region.'
                        ]

                    elif len(stv_image_list) < number_of_stv and len(stv_image_list) > 1:
                        stv_image_random_items = stv_image_list
                        number_of_stv_actual = len(stv_image_list)
                        question_list = [
                            f'Suppose you are a vision expert. You are given a satellite image and {number_of_stv_actual} street view images. Select the most appropriate land use type for this region.',
                            
                            f'Suppose you are a vision expert. You are provided with one satellite image and {number_of_stv_actual} street view images. Identify the land use type of the area.',
                            
                            f'Suppose you are a vision expert. Given the satellite image and {number_of_stv_actual} street view images, determine the most suitable land use type.',
                            
                            f'Suppose you are a vision expert. Look at the satellite image together with {number_of_stv_actual} street view images, and classify the region into the correct land use category.',
                            
                            f'Suppose you are a vision expert. From the satellite image and {number_of_stv_actual} street view images, select the best matching land use type for this region.'
                        ]
                    else:
                        stv_image_random_items = []
                        number_of_stv_actual = 0
                        question_list = [
                            f'Suppose you are a vision expert. You are given a satellite image. Select the most appropriate land use type for this region.',
                            
                            f'Suppose you are a vision expert. You are provided with one satellite image. Identify the land use type of the area.',
                            
                            f'Suppose you are a vision expert. Given the satellite image, determine the most suitable land use type.',
                            
                            f'Suppose you are a vision expert. Look at the satellite image, and classify the region into the correct land use category.',
                            
                            f'Suppose you are a vision expert. From the satellite image, select the best matching land use type for this region.'
                        ]

                    # print(sat_stv_matched['identifier'])
                    if len(list(sat_stv_matched['identifier']))>0:
                        identifier = list(sat_stv_matched['identifier'])[0]
                    else:
                        continue

                    entry = {
                        "id": indicator + '_' + str(cnt),
                        "sat_image_name": image_name_1,
                        "identifier": identifier,
                        "year": year,
                        "images": [image_name_1] + stv_image_random_items,
                        "prompt": f'''{random.choice(question_list)}''' + '\n ' + options + '\n ' + f'''{random.choice(restriction_list)}''',
                        "reference": correct_idx,
                        "landuse":lu_class
                    }
                    data.append(entry)
                    # if cnt == 3:
                    #     break
                    cnt += 1

            with open(output_dir + f"LU_{city_name}_MC_single_year.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)



