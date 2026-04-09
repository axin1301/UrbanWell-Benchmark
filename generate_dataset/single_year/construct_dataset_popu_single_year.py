import json
import pandas as pd
import random
import os

random.seed(42)

# number_of_stv = 4
for number_of_stv in [4]:#[10]:#[2, 4, 8, 12]:
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

        sat_stv_corr_csv0 = pd.read_csv(f"../inputs/sat_stv_list_dir/{city_name}_sat_stv_list.csv") ## 
        # sat_stv_corr_csv1 = pd.read_csv(f"../inputs/sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv") ##
        sat_stv_corr_csv = sat_stv_corr_csv0 #pd.concat([sat_stv_corr_csv0, sat_stv_corr_csv1], ignore_index=True)

        # city_name,identifier,sat_image_name,year,stv_image_name

        output_dir = f'../outputs/single_year/{city_name}/'
        import os
        os.makedirs(output_dir, exist_ok=True)

        cnt = 0
        data = []
        
        for year in range(2012,2021):
            if year == 2013:
                continue
            input_csv_path = f'../../Worldpop/outputs/output_popu_dir/{city_name}_ppp_{year}.csv'
            df = pd.read_csv(input_csv_path)
            num_records = len(df)

            restriction_list = [
                "Answer only with the numeric value. Do not explain or write anything else.",
                "Provide strictly the number representing the indicator. No extra text or explanation.",
                "Reply only with the numeric value. Nothing else should be included.",
                "Your answer must be exactly the numeric value of the indicator, without any words or explanation.",
                "Output only the numeric value. Do not include any other text."
            ]

            for idx, row in df.iterrows():
                if 'image_name' in df.columns:
                    image_name_1 = row['image_name']
                else:
                    image_name_1 = row["best_image_name"]
                
                value1_ = row[indicator]

                sat_stv_matched = sat_stv_corr_csv[(sat_stv_corr_csv['sat_image_name']==image_name_1) & (sat_stv_corr_csv['year']==year)]
                # city_name,identifier,sat_image_name,year,stv_image_name

                stv_image_list = list(sat_stv_matched['stv_image_name'])
                if len(stv_image_list)>=number_of_stv:
                    number_of_stv_actual = number_of_stv
                    stv_image_random_items = random.sample(stv_image_list, number_of_stv)
                elif len(stv_image_list) < number_of_stv and len(stv_image_list) > 1:
                    stv_image_random_items = stv_image_list
                    number_of_stv_actual = len(stv_image_list)
                else:
                    stv_image_random_items = []
                    number_of_stv_actual = 0

                # print(sat_stv_matched['identifier'])
                if len(list(sat_stv_matched['identifier']))>0:
                    identifier = list(sat_stv_matched['identifier'])[0]
                else:
                    continue

                prompt_indicator = indicator + ' number'
                if len(stv_image_list) <= 3:
                        continue
                        # pairwise_question_templates = [
                        #     f"Suppose you are a vision expert. You are given a satellite image of a region from year {year}. Based on the image, please analyze the {prompt_indicator}.",

                        #     f"Suppose you are a vision expert. Examine the satellite image from year {year}. Provide your assessment of the {prompt_indicator}.",

                        #     f"Suppose you are a vision expert. Consider the satellite image provided for the region. Estimate the {prompt_indicator}.",

                        #     f"Suppose you are a vision expert. You are given a satellite image for the region. Based on that, infer the {prompt_indicator}.",

                        #     f"Suppose you are a vision expert. Analyze the satellite image from year {year}, and determine the {prompt_indicator}."
                        # ]

                else:
                    pairwise_question_templates = [
                        f"Suppose you are a vision expert specializing in socioeconomic estimation. You are given {number_of_stv_actual + 1} images of a region: the first is a satellite image from year {year}, followed by {number_of_stv_actual} street views from the same year. Using the observable features in the images, analyze the {prompt_indicator} for this area.",

                        f"Suppose you are a vision expert specializing in socioeconomic estimation. Examine {number_of_stv_actual + 1} images from the same region: 1 satellite image from year {year}, and {number_of_stv_actual} street views from the same year. Consider the imagery content, provide your assessment of the {prompt_indicator} for this area.",

                        f"Suppose you are a vision expert specializing in socioeconomic estimation. Consider the {number_of_stv_actual + 1} images provided for the region: the first is a satellite image from year {year}, and the remaining {number_of_stv_actual} are street views from the same year. Using the observable features in the images together, estimate the {prompt_indicator} for this area.",

                        f"Suppose you are a vision expert specializing in socioeconomic estimation. You are given {number_of_stv_actual + 1} images for the same region, including 1 satellite and {number_of_stv_actual} street views from year {year}. Using the observable features in the images together, infer the {prompt_indicator} for this area.",

                        f"Suppose you are a vision expert specializing in socioeconomic estimation. Analyze {number_of_stv_actual + 1} images from the region: first a satellite image from year {year}, then {number_of_stv_actual} street views from the same year. Using the observable features in the images together, determine the {prompt_indicator} for this area."
                    ]

                entry = {
                    "id": indicator + '_' + str(cnt),
                    "sat_image_name": image_name_1,
                    "identifier": identifier,
                    "year": year,
                    "images": [image_name_1] + stv_image_random_items,
                    "prompt": f"{random.choice(pairwise_question_templates)}\n{random.choice(restriction_list)}",
                    "reference": round(value1_,0),
                }
                data.append(entry)
                # if cnt == 3:
                #     break
                cnt += 1

        with open(output_dir + f"{city_name}_{indicator}_single_year_stv_{number_of_stv}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)



        




