import json
import shutil
import os
def classify_scene(pixel_percentage):
    # --- Step 1 ---
    outdoor_classes = ['sky','road','tree','building','sidewalk','car',
                       'plant','fence','mountain','grass','bridge','tower']
    indoor_classes = ['wall','floor','ceiling','bed','table','chair',
                      'sofa','curtain','lamp','windowpane','cabinet']

    # --- Step 2 ---
    outdoor_score = sum(pixel_percentage.get(c, 0) for c in outdoor_classes)
    indoor_score = sum(pixel_percentage.get(c, 0) for c in indoor_classes)

    # --- Step 3: ---
    if outdoor_score > 0.25 and outdoor_score > indoor_score * 1.5:
        scene_type = 'outdoor'
    elif indoor_score > 0.25 and indoor_score > outdoor_score * 1.5:
        scene_type = 'indoor'
    else:
        scene_type = 'uncertain'

    # --- Step 4 ---
    if scene_type == 'outdoor':
        roadside_score = (
            pixel_percentage.get('road', 0)
            + pixel_percentage.get('sidewalk', 0)
            + pixel_percentage.get('car', 0)
            + pixel_percentage.get('building', 0) * 0.5
            + pixel_percentage.get('fence', 0) * 0.3
        )

        #
        if pixel_percentage.get('windowpane', 0) > 0.05:
            roadside_score *= 0.5

        if roadside_score > 0.15 and (
            pixel_percentage.get('sky', 0) > 0.05 or
            pixel_percentage.get('building', 0) > 0.05
        ):
            scene_type = 'roadside'
        else:
            scene_type = 'outdoor-natural'

    return scene_type

import pandas as pd

def main():
    #
    # with open('test_output-ade20k.json', 'r', encoding='utf-8') as f:
    city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
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

    valid_stv_list = []
    for city_name in list(city_csv['city_name'].drop_duplicates()):
        cnt= 0
        print(city_name)

        out_file = f'CitySense_stv-ade20k/{city_name}_stv-ade20k.json'

        with open(out_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            pixel_percentage = item["pixel_percentage"]
            scene_type = classify_scene(pixel_percentage)

            if scene_type not in ['roadside','outdoor-natural']:
                continue  # 
            else:
                valid_stv_list.append(item['image'])
            
    pd_dict = pd.DataFrame({'valid_stv_list': valid_stv_list})
    pd_dict.to_csv('outputs/final_dataset/valid_stv_list.csv', index=False)


if __name__ == "__main__":
    main()