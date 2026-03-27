import os
import json
import random
import pandas as pd
import tqdm
from indicator_col_name_in_prompt import *  # col_name_dict, indicator_name_dict, add_info_indicator

random.seed(42)

# 生成数据文件路径的函数
def get_path(city_name, indicator, year):
    if indicator == 'CO2':
        if year < 2014:
            return None
        return f"../extract_EEA/generated_CO2/{city_name}/{city_name}_CO2_{year}.csv"

    elif indicator == 'NO2':
        if year < 2014:
            return None
        return f"../extract_EEA/generated_NO2/{city_name}/{city_name}_NO2_{year}.csv"

    elif indicator == 'QSI':
        if year != 2016:
            return None
        return f"../extract_EEA/generated_QSI/{city_name}/{city_name}_QSI_{year}.csv"

    elif indicator == 'PM25':
        if year < 2014:
            return None
        return f"../extract_EEA/generated_PM25/{city_name}/{city_name}_PM25_{year}.csv"

    elif indicator in ['network_density_km_per_km2', 'road_length', 'avg_dist_to_restaurant','avg_dist_to_hotel', 'avg_dist_to_supermarket','avg_dist_to_convenience']:
        if year < 2014 or year > 2024:
            return None
        year_str = str(year - 2000 + 1) + "0101"
        # return f"../OSM_data/accessability_output/{city_name}_accessibility_metrics_{year_str}.csv"
        return f"../OSM_data/accessability_output_only_POI_update_parallel_test/{city_name}_{year_str}.csv"


    elif indicator == 'landuse_mix':
        if year not in [2012, 2018]:
            return None
        return f'../UrbanAtlas/output_LU_mix_dir/{city_name}_LU_mix_{year}.csv'

    elif indicator == 'economic':
        if year < 2014:
            return None
        # return f'../OSM_data/output_economic_dir/{city_name}_economic_urbancore_{year}.csv'
        return f'../OSM_data/output_economic_dir_update/{city_name}_economic_urbancore_{year}.csv'


    elif indicator == 'NDVI':
        if year not in [2018, 2020, 2022, 2024]:
            return None
        return f"../extract_EEA/generated_NDVI/{city_name}/{city_name}_NDVI_{year}.csv"

    return None


# 模板函数
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


# 限制说明（一次定义，循环内重复用）
restriction_list = [
    "Answer only with the numeric value. Do not explain or write anything else.",
    "Provide strictly the number representing the indicator. No extra text or explanation.",
    "Reply only with the numeric value. Nothing else should be included.",
    "Your answer must be exactly the numeric value of the indicator, without any words or explanation.",
    "Output only the numeric value. Do not include any other text."
]

# 主循环
for number_of_stv in [4]:# [10]:
    city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
    new_row = {
        "city_name": "HELSINKI",
        "city_full_name": "New City Full Name",
        "province": "New Province",
        "note": "Some note",
        "country_name": "New Country"
    }

    # 转为 DataFrame
    new_row_df = pd.DataFrame([new_row])

    # 拼接到原 DataFrame
    city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

    # 添加测试城市
    # city_csv.loc[len(city_csv)] = ["HELSINKI", "New City Full Name", "New Province", "Some note", "New Country"]

    for city in tqdm.tqdm(city_csv.itertuples(index=False)):
        if city.city_name in ['PRISTINA', 'LEFKOSIA', 'SARAJEVO']:
            continue

        # 加载 sat-stv 对照表
        try:
            sat0 = pd.read_csv(f"../final_dataset/sat_stv_list_dir/{city.city_name}_sat_stv_list.csv")
            sat1 = pd.read_csv(f"../final_dataset/sat_stv_list_dir/{city.city_name}_sat_stv_list_no_stv.csv")
            # sat_stv_corr_csv0 = pd.read_csv(f"../final_dataset/sat_stv_list_dir/{city.city_name}_sat_stv_list.csv")
            sat_stv_corr_csv_full = pd.concat([sat0, sat1], ignore_index=True)
            valid_sat_image_names = list(pd.read_csv('../download_sat/valid_image_lists.csv')['valid_image_name'])
            sat_stv_corr_csv = sat_stv_corr_csv_full[sat_stv_corr_csv_full['sat_image_name'].isin(valid_sat_image_names)].reset_index(drop = True)

        except FileNotFoundError:
            continue

        # output_dir = f'generated_QA/{city.city_name}/'
        output_dir = f'generated_QA_update/{city.city_name}/'
        os.makedirs(output_dir, exist_ok=True)

        # for indicator in [
        #     'CO2', 'NO2', 'PM25', 'QSI', 'NDVI',
        #     'network_density_km_per_km2', 'intersection_density_per_km2',
        #     'avg_dist_to_restaurant', 'avg_dist_to_hotel',
        #     'avg_dist_to_supermarket', 'avg_dist_to_hospital',
        #     'economic', 'landuse_mix'
        # ]:
        indicator_list = ['network_density_km_per_km2', 'road_length', 'avg_dist_to_restaurant','avg_dist_to_hotel', 'avg_dist_to_supermarket','avg_dist_to_convenience', 'economic']
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
                    # 获取 image_name
                    image_name_1 = getattr(row, 'image_name', None) or getattr(row, 'ImageFileName', None) or row.best_image_name
                    value1_ = round(getattr(row, col_indicator), 3)
                    if indicator == 'NDVI':
                        if value1_ < -1 or value1_ > 1:
                            continue

                    if indicator == 'QSI' and pd.isna(value1_):
                        continue

                    # 匹配 sat-stv
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

                    # 选模板
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

            # 写文件
            with open(os.path.join(output_dir, f"{city.city_name}_{indicator}_single_year_stv.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

print("✅ 全部完成！")


# import json
# import pandas as pd
# import random
# import os
# from indicator_col_name_in_prompt import *
# # col_name_dict, indicator_name_dict
# import tqdm

# random.seed(42)

# # number_of_stv = 4
# for number_of_stv in [10]:#[2, 4, 8, 12]:
#     indicator = 'population'

#     city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
#     new_row = {
#         "city_name": "HELSINKI",
#         "city_full_name": "New City Full Name",
#         "province": "New Province",
#         "note": "Some note",
#         "country_name": "New Country"
#     }

#     # 转为 DataFrame
#     new_row_df = pd.DataFrame([new_row])

#     # 拼接到原 DataFrame
#     city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

#     for i in tqdm.tqdm(range(len(city_csv))):  # 调试时只跑 1 个城市
#         city_name = city_csv.at[i, 'city_name']
#         city_full_name = city_csv.at[i, 'city_full_name']
#         province = city_csv.at[i, 'province']
#         note = city_csv.at[i, 'note']
#         country_name = city_csv.at[i, 'country_name']
        
#         if city_name in ['PRISTINA','LEFKOSIA','SARAJEVO']:
#             continue

#         sat_stv_corr_csv0 = pd.read_csv(f"sat_stv_list_dir/{city_name}_sat_stv_list.csv") ## 有街景图像的sat-stv
#         sat_stv_corr_csv1 = pd.read_csv(f"sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv") ## 无街景图像的sat
#         sat_stv_corr_csv = pd.concat([sat_stv_corr_csv0, sat_stv_corr_csv1], ignore_index=True)

#         # city_name,identifier,sat_image_name,year,stv_image_name

#         output_dir = f'generated_QA\\{city_name}/'
#         import os
#         os.makedirs(output_dir, exist_ok=True)

#                 # 先生成空模板
        
#         for indicator in ['CO2','NO2', 'PM25', 'QSI', 'NDVI', 'network_density_km_per_km2', 'intersection_density_per_km2', 'avg_dist_to_restaurant','avg_dist_to_hotel', 'avg_dist_to_supermarket','avg_dist_to_hospital', 'economic', 'landuse_mix']:
#             cnt = 0
#             data = []
            
#             for year in range(2012,2025):
#                 if indicator == 'CO2':
#                     if year <2014:
#                         continue
#                     input_csv_path = f"../extract_EEA/generated_CO2/{city_name}/{city_name}_CO2_{year}.csv"
                
#                 elif indicator == 'NO2':
#                     if year <2014:
#                         continue
#                     input_csv_path = f"../extract_EEA/generated_NO2/{city_name}/{city_name}_NO2_{year}.csv"
#                 elif indicator == 'QSI':
#                     if year != 2016:
#                         continue
#                     input_csv_path = f"../extract_EEA/generated_QSI/{city_name}/{city_name}_QSI_{year}.csv"
#                 elif indicator == 'PM25':
#                     if year <2014:
#                         continue
#                     input_csv_path = f"../extract_EEA/generated_PM25/{city_name}/{city_name}_PM25_{year}.csv"
                
#                 elif indicator in ['network_density_km_per_km2', 'intersection_density_per_km2', 'avg_dist_to_restaurant','avg_dist_to_hotel', 'avg_dist_to_supermarket','avg_dist_to_hospital']:
#                     if year <2014 or year > 2024:
#                         continue
#                     year_str = str(year - 2000 + 1) + "0101"
#                     input_csv_path = f"../OSM_data/accessability_output/{city_name}_accessibility_metrics_{year_str}.csv"
                
#                 elif indicator == 'landuse_mix':
#                     if year not in [2012,2018]:
#                         continue
#                     input_csv_path = f'../UrbanAtlas/output_LU_mix_dir/{city_name}_LU_mix_{year}.csv'
                
#                 elif indicator == 'economic':
#                     if year < 2014:
#                         continue
#                     input_csv_path = f'../OSM_data/output_economic_dir/{city_name}_economic_urbancore_{year}.csv'
                
#                 elif indicator == 'NDVI':
#                     if year not in [2018,2020,2022,2024]:
#                         continue
#                     input_csv_path = f"../extract_EEA/generated_NDVI/{city_name}/{city_name}_NDVI_{year}.csv"
#                 # elif indicator == '':
#                     # input_csv_path = f'../WorldPop/output_popu_dir/{city_name}_ppp_{year}.csv'

#                 # print(input_csv_path)
#                 if not os.path.exists(input_csv_path):
#                     continue
#                 df = pd.read_csv(input_csv_path)
#                 # 你要生成多少条记录
#                 num_records = len(df)
                
#                 if indicator in col_name_dict:
#                     col_indicator = col_name_dict[indicator]
#                 else:
#                     col_indicator = indicator

#                 if indicator in indicator_name_dict:
#                     prompt_indicator = indicator_name_dict[indicator]
#                 else:
#                     prompt_indicator = indicator.replace('_',' ')

#                 if indicator in add_info_indicator:
#                     need_add_info = add_info_indicator[indicator]
#                 else:
#                     need_add_info = ''

#                 # 限制说明
#                 restriction_list = [
#                     "Answer only with the numeric value. Do not explain or write anything else.",
#                     "Provide strictly the number representing the indicator. No extra text or explanation.",
#                     "Reply only with the numeric value. Nothing else should be included.",
#                     "Your answer must be exactly the numeric value of the indicator, without any words or explanation.",
#                     "Output only the numeric value. Do not include any other text."
#                 ]

#                 for idx, row in df.iterrows():
#                     # 当前行
#                     if 'image_name' in df.columns:
#                         image_name_1 = row['image_name']
#                     elif 'ImageFileName' in df.columns:
#                         image_name_1 = row['ImageFileName']
#                     else:
#                         image_name_1 = row["best_image_name"]
                    
#                     #
#                     if indicator in ['CO2','NO2', 'PM25', 'QSI', 'NDVI', 'network_density_km_per_km2', 'intersection_density_per_km2', 'avg_dist_to_restaurant','avg_dist_to_hotel', 'avg_dist_to_supermarket','avg_dist_to_hospital', 'economic', 'landuse_mix']:
#                         value1_ = round(row[col_indicator],3)

#                     sat_stv_matched = sat_stv_corr_csv[(sat_stv_corr_csv['sat_image_name']==image_name_1) & (sat_stv_corr_csv['year']==year)]
#                     # city_name,identifier,sat_image_name,year,stv_image_name

#                     stv_image_list = list(sat_stv_matched['stv_image_name'])
#                     if len(stv_image_list)>=number_of_stv:
#                         number_of_stv_actual = number_of_stv
#                         stv_image_random_items = random.sample(stv_image_list, number_of_stv)
#                     elif len(stv_image_list) < number_of_stv and len(stv_image_list) > 1:
#                         stv_image_random_items = stv_image_list
#                         number_of_stv_actual = len(stv_image_list)
#                     else:
#                         stv_image_random_items = []
#                         number_of_stv_actual = 0

#                     # print(sat_stv_matched['identifier'])
#                     if len(list(sat_stv_matched['identifier']))>0:
#                         identifier = list(sat_stv_matched['identifier'])[0]
#                     else:
#                         continue

#                     if len(stv_image_list) <= 1:
#                         pairwise_question_templates = [
#                             f"Suppose you are a vision expert. You are given a satellite image of a region from year {year}. Using the observable features in the image together with the additional information provided,, please analyze the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. Examine the satellite image content from year {year}. Provide your assessment of the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. Consider the satellite image provided for the region. Estimate the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. You are given a satellite image for the region. Based on that, infer the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. Analyze the satellite image content from year {year}, and determine the {prompt_indicator} for this area."
#                         ]

#                     else:
#                         pairwise_question_templates = [
#                             f"Suppose you are a vision expert. You are given {number_of_stv_actual + 1} images of a region: the first is a satellite image from year {year}, followed by {number_of_stv_actual} street views from the same year. Using the observable features in the images together with the additional information provided, analyze the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. Examine {number_of_stv_actual + 1} images from the same region: 1 satellite image from year {year}, and {number_of_stv_actual} street views from the same year. Consider both the imagery content and the supplementary details given, provide your assessment of the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. Consider the {number_of_stv_actual + 1} images provided for the region: the first is a satellite image from year {year}, and the remaining {number_of_stv_actual} are street views from the same year. Using the observable features in the images together with the additional information provided, estimate the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. You are given {number_of_stv_actual + 1} images for the same region, including 1 satellite and {number_of_stv_actual} street views from year {year}. Using the observable features in the images together with the additional information provided, infer the {prompt_indicator} for this area.",

#                             f"Suppose you are a vision expert. Analyze {number_of_stv_actual + 1} images from the region: first a satellite image from year {year}, then {number_of_stv_actual} street views from the same year. Using the observable features in the images together with the additional information provided, determine the {prompt_indicator} for this area."
#                         ]


#                     entry = {
#                         "id": indicator + '_' + str(cnt),
#                         "sat_image_name": image_name_1,
#                         "identifier": identifier,
#                         "year": year,
#                         "images": [image_name_1] + stv_image_random_items,
#                         "prompt": f"{random.choice(pairwise_question_templates)}\n{need_add_info}\n{random.choice(restriction_list)}",
#                         "reference": value1_,
#                     }
#                     data.append(entry)
#                     # if cnt == 3:
#                     #     break
#                     cnt += 1

#                 # 保存到 JSON 文件
#             with open(output_dir + f"{city_name}_{indicator}_single_year_stv.json", "w", encoding="utf-8") as f:
#                 json.dump(data, f, indent=4, ensure_ascii=False)

#             # print("✅ JSON 模板已生成，保存在 output.json")