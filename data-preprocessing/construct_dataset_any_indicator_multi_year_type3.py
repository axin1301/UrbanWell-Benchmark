import json
import pandas as pd
import random
import os
from indicator_col_name_in_prompt import *
# col_name_dict, indicator_name_dict
import tqdm
from collections import defaultdict

random.seed(42)

max_stv_images = 4
change_threshold = 2

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

for i in tqdm.tqdm(range(len(city_csv))):  # 调试时只跑 1 个城市
    city_name = city_csv.at[i, 'city_name']
    city_full_name = city_csv.at[i, 'city_full_name']
    province = city_csv.at[i, 'province']
    note = city_csv.at[i, 'note']
    country_name = city_csv.at[i, 'country_name']
    
    if city_name in ['PRISTINA','LEFKOSIA','SARAJEVO']:
        continue

    indicators_all = ['network_density_km_per_km2', 'road_length', 'avg_dist_to_restaurant','avg_dist_to_hotel', 'avg_dist_to_supermarket','avg_dist_to_convenience', 'economic']
    #['safety', 'lively', 'wealthy', 'beautiful', 'boring', 'depressing']#['CO2','NO2', 'PM25', 'QSI', 'NDVI', 'network_density_km_per_km2', 'intersection_density_per_km2', 'avg_dist_to_restaurant','avg_dist_to_hotel', 'avg_dist_to_supermarket','avg_dist_to_hospital', 'economic', 'landuse_mix','safety', 'lively', 'wealthy', 'beautiful', 'boring', 'depressing'] # ['PM25']
    # 
    for indicator in indicators_all:
    # for indicator in ['landuse_mix','NDVI']:

        if indicator == 'QSI':
            continue

        if indicator in ['landuse_mix','NDVI']:
            used_year_num = 2
            num_with_multiple_images_t = 1
        else:
            used_year_num = 4
            num_with_multiple_images_t = 2

        if indicator in indicator_name_dict:
            prompt_indicator = indicator_name_dict[indicator]
        else:
            prompt_indicator = indicator.replace('_',' ')

        if indicator in add_info_indicator:
            need_add_info = add_info_indicator[indicator]
        else:
            need_add_info = ''

        cnt = 0
        data = []
        # output_dir = f'generated_QA\\{city_name}/'
        output_dir = f'generated_QA_update\\{city_name}/'
        import os
        os.makedirs(output_dir, exist_ok=True)

        if indicator in ['safety', 'lively', 'wealthy', 'beautiful', 'boring', 'depressing']:
            single_year_data_path = output_dir + f"{city_name}_{indicator}_single_year_stv_num_4.json"
        else:
            single_year_data_path = output_dir + f"{city_name}_{indicator}_single_year_stv.json"

        with open(single_year_data_path, 'r', encoding='utf-8') as file:
            single_year_data = json.load(file)

        # print(single_year_data[1])

        # 1. 按 'sat_image_name' 分组
        grouped_data = defaultdict(list)
        for item in single_year_data :
            grouped_data[item['sat_image_name']].append(item)

        count = 0
        limit = 2
        # 2. 根据条件重构数据
        remained_items = []
        reconstructed_data = []
        for sat_image_name, items in grouped_data.items():
            # 检查是否满足“有四个年份”的条件
            top_n_items = []
            if len(items) >= used_year_num:
                years = sorted([item['year'] for item in items])
                # 假设所有其他字段都可以从第一个元素获取或合并
                # first_item = items[0]
                
                # for item in items:
                #     print(item)

                sorted_items = sorted(items, key=lambda x: len(x['images']), reverse=True)
                # 3. 选择前 x 个元素
                top_n_items.extend(sorted_items[:used_year_num])

                # 2. 对这4个年份的数据按年份升序重新排序
                # 这将确保最终结果是按时间顺序排列的
                selected_items = sorted(top_n_items, key=lambda x: x['year'])

                # 创建一个布尔值列表，然后求和
                num_with_multiple_images = sum(len(item['images']) > 1 for item in selected_items)

                if num_with_multiple_images < num_with_multiple_images_t:
                    # print("条件满足：至少有两个元素的images长度大于1。")
                    continue

                # for item in selected_items:
                #     print(item)
                # print('-----------------------------------------------')

                # 提取所有 'reference' 值
                all_references = [item['reference'] for item in selected_items]
                all_years = [item['year'] for item in selected_items]
                # 提取所有 'images' 列表
                # all_images = [item['images'] for item in selected_items]
                # all_images_input = [item['images'] for item in selected_items[:-1]]
                all_images_output = [item['images'] for item in selected_items[-1:]]

                # 如果您想将所有图片路径合并到一个列表中，可以这样做：
                merged_images = [] #[img for item in selected_items for img in item['images']]

                header_templates = [
                    f"""Suppose you are a vision expert. You are given a series of images for a region. There are a total of {used_year_num} years of data, from {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below. **Here are the images for each year:**""",

                    f"""You are an analyst tasked with examining satellite and street-view images over time for a region. The dataset spans {used_year_num} years, ranging from {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below. The following lists the available imagery for each year: """,

                    f"""As a remote-sensing specialist, you are provided with {used_year_num} years of imagery, covering the period {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below. Below you will find the available images for each year:""",

                    f"""Imagine you are studying urban change using geospatial data. The dataset includes {used_year_num} yearly snapshots, from {all_years[0]} through {all_years[-1]}. The images are provided to you as per the instructions below. Each year’s available imagery is described below:""",

                    f"""You are provided with temporal visual data of a region, covering {used_year_num} years ({all_years[0]} → {all_years[-1]}). The images are provided to you as per the instructions below. For each year, the available images are listed:"""
                ]

                # 随机选择一个模板
                question_template = random.choice(header_templates)
                if indicator != 'NDVI':
                    if need_add_info == '':
                        question_template = question_template + '\n'
                    else:
                        question_template = need_add_info + '\n' + question_template + '\n'

                # 循环构建每个年份的图像和数据描述
                for item in selected_items[:-1]:
                    # 根据年份提取对应的数据
                    year = item['year']
                    lst = item['images']
                    not_valid_target = "no_stv_image"
                    lst = [name for name in lst if not_valid_target not in name]
                    item['images'] = lst
                    # 提取卫星图像和街景图像
                    sat_image = item['images'][0] # 假设你已经提取了卫星图像
                    if len(item['images']) > 1:
                        street_view_images = item['images'][1:max_stv_images+1] # 假设你已经提取了街景图像
                        # 拼接描述
                        image_description = f"1 satellite image and {min(max_stv_images, len(item['images'])-1)} street view image(s)"
                    else:
                        street_view_images = []
                        image_description = "1 satellite image"
        
                    # 拼接描述
                    question_template += f'''
Year {year}:
- Images provided: {image_description}
                    '''
                    sat_image_row = sat_image.split('_')[1]
                    sat_image_stem = sat_image.split('.')[0]
                    tmp_identifier = item['identifier']

                    sat_image_path = '/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/download_sat/' + f'downloaded_sat_{year}_zoom_{16}/{city_name}/{year}-07-31/{city_name}/{16}/{sat_image_row}/{sat_image}'
                    if city_name == 'HELSINKI':
                        sat_image_path = '/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/download_sat/' + f'downloaded_sat_{year}_zoom_{16}/urbancore/{year}-07-31/urbancore/{16}/{sat_image_row}/{sat_image}'
                    merged_images.append(sat_image_path)

                    if item['identifier'] == 'none':
                        stv_root_path = f'/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/try_GSV_urban_sup/downloaded_stv_selected/{city_name}/{sat_image_stem}/street_view_images/'
                    else:
                        stv_root_path = f'/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/try_GSV/downloaded_stv_selected/{city_name}/{tmp_identifier}/street_view_images/'

                    street_view_images_paths = [stv_root_path + x for x in street_view_images]
                    merged_images = merged_images + street_view_images_paths
                    # remained_items.append(item)

                item = selected_items[-1]
                # 根据年份提取对应的数据
                year = item['year']
                lst = item['images']
                not_valid_target = "no_stv_image"
                lst = [name for name in lst if not_valid_target not in name]
                item['images'] = lst
                # 提取卫星图像和街景图像
                sat_image = item['images'][0] # 假设你已经提取了卫星图像
                if len(item['images']) > 1:
                    street_view_images = item['images'][1:max_stv_images+1] # 假设你已经提取了街景图像
                    # 拼接描述
                    image_description = f"1 satellite image and {min(max_stv_images, len(item['images'])-1)} street view image(s)"
                else:
                    street_view_images = []
                    image_description = "1 satellite image"
                remained_items.append(item)
                # 拼接描述
                question_template += f'''
Year {year}:
- Images provided: {image_description}
                '''

                sat_image_row = sat_image.split('_')[1]
                sat_image_stem = sat_image.split('.')[0]
                tmp_identifier = item['identifier']

                sat_image_path = '/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/download_sat/' + f'downloaded_sat_{year}_zoom_{16}/{city_name}/{year}-07-31/{city_name}/{16}/{sat_image_row}/{sat_image}'
                if city_name == 'HELSINKI':
                    sat_image_path = '/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/download_sat/' + f'downloaded_sat_{year}_zoom_{16}/urbancore/{year}-07-31/urbancore/{16}/{sat_image_row}/{sat_image}'
                merged_images.append(sat_image_path)

                if item['identifier'] == 'none':
                    stv_root_path = f'/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/try_GSV_urban_sup/downloaded_stv_selected/{city_name}/{sat_image_stem}/street_view_images/'
                else:
                    stv_root_path = f'/wrk-vakka/users/xiyanxin/vllm-dir/project_visual/try_GSV/downloaded_stv_selected/{city_name}/{tmp_identifier}/street_view_images/'

                street_view_images_paths = [stv_root_path + x for x in street_view_images]
                merged_images = merged_images + street_view_images_paths

                if used_year_num == 2:
                    question_part_final_list = [
f'''
Please analyze the imagery sequence. For each consecutive pair of years, classify the {prompt_indicator} change for the area using this rule:
- "positive" if the change exceeds +{change_threshold}%
- "negative" if the change is less than -{change_threshold}%
- "no change" if the change is between -{change_threshold}% and +{change_threshold}%

Output exactly {used_year_num-1} word ("positive", "negative", or "no change") for the interval.''',

f'''
Your task is to study the temporal imagery for the area. For every interval between consecutive years, decide whether the {prompt_indicator} shows growth, decline, or stability for the area. Use the following thresholds:
- positive: > +{change_threshold}%
- negative: < -{change_threshold}%
- no change: between -{change_threshold}% and +{change_threshold}%

Return only {used_year_num-1} label (labels include "positive", "negative", and "no change").''',

f'''
Look at the series of yearly images. Compare the {prompt_indicator} across each consecutive pair of years for the area. 
Assign one of three labels:
- "positive" if the relative change is greater than +{change_threshold}%
- "negative" if the relative change is less than -{change_threshold}%
- "no change" otherwise

Provide exactly {used_year_num-1} label (labels include "positive", "negative", and "no change").''',

f'''
Focus on the temporal evolution of the region. For each two-year step, classify the {prompt_indicator} trend for the area based on relative change:
- positive (> +{change_threshold}%)
- negative (< -{change_threshold}%)
- no change (between -{change_threshold}% and +{change_threshold}%)

Return only {used_year_num-1} word. (Words include "positive", "negative", and "no change")''',

f'''
Based on the imagery, analyze how the {prompt_indicator} evolves over time. For each consecutive year interval, output one label using this rule:
- "positive" if the change > +{change_threshold}%
- "negative" if the change < -{change_threshold}%
- "no change" if the change is within ±{change_threshold}%

Provide {used_year_num-1} label (labels include "positive", "negative", and "no change"), nothing else.'''
                    ]

                else:
                    question_part_final_list = [
f'''
Please analyze the imagery sequence. For each consecutive pair of years, classify the {prompt_indicator} change for the area using this rule:
- "positive" if the change exceeds +{change_threshold}%
- "negative" if the change is less than -{change_threshold}%
- "no change" if the change is between -{change_threshold}% and +{change_threshold}%

Output exactly {used_year_num-1} labels (labels include "positive", "negative", and "no change"), one for each interval, separated by commas.''',

f'''
Your task is to study the temporal imagery. For every interval between consecutive years, decide whether the {prompt_indicator} shows growth, decline, or stability for the area. Use the following thresholds:
- positive: > +{change_threshold}%
- negative: < -{change_threshold}%
- no change: between -{change_threshold}% and +{change_threshold}%

Return {used_year_num-1} labels (labels include "positive", "negative", and "no change") in order, separated by commas.''',

f'''
Look at the series of yearly images. Compare the {prompt_indicator} across each consecutive pair of years for the area. 
Assign one of three labels:
- "positive" if the relative change is greater than +{change_threshold}%
- "negative" if the relative change is less than -{change_threshold}%
- "no change" otherwise

Provide exactly {used_year_num-1} comma-separated labels (labels include "positive", "negative", and "no change") in this order.''',

f'''
Focus on the temporal evolution of the region. For each two-year step, classify the {prompt_indicator} trend for the area based on relative change:
- positive (> +{change_threshold}%)
- negative (< -{change_threshold}%)
- no change (between -{change_threshold}% and +{change_threshold}%)

Return only {used_year_num-1} words (words include "positive", "negative", and "no change") separated by commas.''', 

f'''
Based on the imagery, analyze how the {prompt_indicator} evolves over time. 
For each consecutive year interval, output one label using this rule:
- "positive" if the change > +{change_threshold}%
- "negative" if the change < -{change_threshold}%
- "no change" if the change is within ±{change_threshold}%

Provide {used_year_num-1} comma-separated labels (labels include "positive", "negative", and "no change"), nothing else.'''
                ]

                question_part_final = random.choice(question_part_final_list)
                question_template += question_part_final
                if indicator == 'NDVI':
                    question_template += ' '
                    question_template += need_add_info

                true_labels = []
                references = [item['reference'] for item in selected_items]

                if used_year_num == 2 and references[0] == 0:
                    continue

                if used_year_num == 4:
                    if references[0] == 0 or references[1] == 0 or references[2] == 0:
                        continue

                # print(references)

                for i in range(len(references)-1):
                    prev_val = references[i]
                    next_val = references[i+1]

                    delta = (next_val - prev_val) / prev_val  # 相对变化率

                    if delta > 0.02: ####dui
                        true_labels.append("positive")
                    elif delta < -0.02:
                        true_labels.append("negative")
                    else:
                        true_labels.append("no change")

                if len(true_labels)>1 and len(set(true_labels))==1:
                    continue

                new_element = {
                    'sat_image_name': sat_image,
                    'years': all_years,
                    'ids': f"{indicator}_{count}",
                    'images': merged_images, # 合并所有图片的列表
                    'prompt': question_template, # 假设prompt是相同的
                    'references': true_labels # 合并所有reference
                }
                reconstructed_data.append(new_element)
                count+=1
                # if count >= limit:
                #     break  # 达到限制，立即停止循环
            else:
                # 如果不满足条件，则将原始元素添加到新列表中
                # reconstructed_data.extend(items)
                continue

        # 打印最终重构的列表
        # print(reconstructed_data)
        with open(output_dir + f"{city_name}_{indicator}_multi_year_type3_stv_num_{max_stv_images}_year_num_{used_year_num}.json", "w", encoding="utf-8") as f:
            json.dump(reconstructed_data, f, indent=4, ensure_ascii=False)

        with open(output_dir + f"{city_name}_{indicator}_single_year_selected_type3_stv_num_{max_stv_images}_year_num_{used_year_num}.json", "w", encoding="utf-8") as f:
            json.dump(remained_items, f, indent=4, ensure_ascii=False)
        print("✅ JSON 模板已生成，保存在 output.json")


