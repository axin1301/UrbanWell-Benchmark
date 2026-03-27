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

for i in range(len(city_csv)):  # 调试时只跑 1 个城市
    city_name = city_csv.at[i, 'city_name']
    city_full_name = city_csv.at[i, 'city_full_name']
    province = city_csv.at[i, 'province']
    note = city_csv.at[i, 'note']
    country_name = city_csv.at[i, 'country_name']
    
    if city_name in ['PRISTINA','LEFKOSIA','SARAJEVO']:
        continue

    sat_stv_corr_csv = pd.read_csv(f"../final_dataset/sat_stv_list_dir/{city_name}_sat_stv_list.csv")
    # city_name,identifier,sat_image_name,year,stv_image_name

    output_dir = f'generated_QA\\{city_name}/'
    import os
    os.makedirs(output_dir, exist_ok=True)

    single_year_data_path = output_dir + f"{city_name}_{indicator}_single_year_stv_{max_stv_images}.json"

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
    reconstructed_data = []
    remained_items = []
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

            # # 1. 找到符合“图像数量大于1”的最近一个年份
            # #    首先筛选出所有图像数量大于1的数据
            # multi_image_items = [item for item in items if len(item['images']) > 1]
            # #    然后按年份降序排序，以找到最晚的那个
            # if len(multi_image_items)<2:
            #     continue
        
            # multi_image_items.sort(key=lambda x: x['year'], reverse=True)

            # #    获取最后一个（即最晚的）年份，并从列表中移除
            # last_year_item = multi_image_items[0]

            # # 2. 找到符合“图像数量等于1”的其他年份
            # #    从原始数据中排除已选择的最后一个年份，并筛选出图像数量等于1的数据
            # single_image_items = [
            #     item for item in items 
            #     if len(item['images']) == 1 and item != last_year_item
            # ]
            # #    按年份升序排序，然后选择前 used_year_num - 1 个
            # single_image_items.sort(key=lambda x: x['year'])
            # preceding_items = single_image_items[:used_year_num - 1]

            # # 3. 合并两部分数据并按年份排序
            # selected_items = preceding_items + [last_year_item]
            # selected_items.sort(key=lambda x: x['year'])

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

            # question_template = f'''
            # Suppose you are a vision expert. You are given a series of images for a region.
            # There are a total of {used_year_num} years of data, from {all_years[0]} to {all_years[-1]}.

            # **Here are the images and data for each year:**
            # '''

            header_templates = [
f"""Suppose you are a vision expert specializing in socioeconomic estimation. You are given a series of images for a region. There are a total of {used_year_num} years of data, from {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below. **Here are the images and data for each year:**""",

f"""You are an analyst specializing in socioeconomic estimation and tasked with examining satellite and street-view images of a region over time. The dataset spans {used_year_num} years, ranging from {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below. The following lists the imagery and {indicator} values for each year:""",

f"""As a remote-sensing specialist specializing in socioeconomic estimation, you are provided with {used_year_num} years of imagery of a region, covering the period {all_years[0]} to {all_years[-1]}. The images are provided to you as per the instructions below.Below you will find the available images and historical {indicator} numbers by year:""",

f"""Imagine you are studying urban change using geospatial data for a region. The dataset includes {used_year_num} yearly snapshots, from {all_years[0]} through {all_years[-1]}. The images are provided to you as per the instructions below. Each year’s imagery and the corresponding {indicator} number are given below:""",

f"""You are provided with temporal visual data of a region, covering {used_year_num} years ({all_years[0]} → {all_years[-1]}). The images are provided to you as per the instructions below. For each year, the following imagery and the reported {indicator} values are listed:"""
            ]

            # 随机选择一个模板
            question_template = random.choice(header_templates)

            # 循环构建每个年份的图像和数据描述
            for item in selected_items[:-1]:
                # remained_items.append(item)
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
    - Corresponding {indicator} number: {int(item['reference'])}
                '''
                sat_image_row = sat_image.split('_')[1]
                sat_image_stem = sat_image.split('.')[0]
                tmp_identifier = item['identifier']

                # sat_image_path = '../download_sat/' + f'downloaded_sat_{year}_zoom_{16}\\{city_name}\\{year}-07-31\\{city_name}\\{16}\\{sat_image_row}\\{sat_image}'
                # if city_name == 'HELSINKI':
                #     sat_image_path = '../download_sat/' + f'downloaded_sat_{year}_zoom_{16}\\urbancore\\{year}-07-31\\urbancore\\{16}\\{sat_image_row}\\{sat_image}'
                # merged_images.append(sat_image_path)

                # if item['identifier'] == 'none':
                #     stv_root_path = f'D:\\CitySense原始数据\\try_GSV_urban_sup\\downloaded_stv_selected\\{city_name}\\{sat_image_stem}/street_view_images/'
                # else:
                #     stv_root_path = f'D:\\CitySense原始数据\\try_GSV\\downloaded_stv_selected\\{city_name}\\{tmp_identifier}/street_view_images/'

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

            item = selected_items[-1]
            remained_items.append(item)
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

            sat_image_row = sat_image.split('_')[1]
            sat_image_stem = sat_image.split('.')[0]
            tmp_identifier = item['identifier']
            question_template += f'''
Year {year}:
    - Images provided: {image_description}
                '''

            # sat_image_path = '../download_sat/' + f'downloaded_sat_{year}_zoom_{16}\\{city_name}\\{year}-07-31\\{city_name}\\{16}\\{sat_image_row}\\{sat_image}'
            # if city_name == 'HELSINKI':
            #     sat_image_path = '../download_sat/' + f'downloaded_sat_{year}_zoom_{16}\\urbancore\\{year}-07-31\\urbancore\\{16}\\{sat_image_row}\\{sat_image}'
            # merged_images.append(sat_image_path)

            # if item['identifier'] == 'none':
            #     stv_root_path = f'D:\\CitySense原始数据\\try_GSV_urban_sup\\downloaded_stv_selected\\{city_name}\\{sat_image_stem}/street_view_images/'
            # else:
            #     stv_root_path = f'D:\\CitySense原始数据\\try_GSV\\downloaded_stv_selected\\{city_name}\\{tmp_identifier}/street_view_images/'

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

            # # 添加最后一个年份的待分析部分
            # question_template += f'''
            # Now, analyze the images for year {all_years[-1]}. These images include {image_description}.
            # The reference {indicator} numbers for the previous years are provided to give you a historical context.
            # Based on the images, estimate the {indicator} number for year {all_years[-1]}.
            # Output only the numeric value. Do not include any other text or explanation.
            # '''

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
Look at the images corresponding to year {all_years[-1]}. You may use the prior years’ {indicator} values for context. Estimate the {indicator} for {all_years[-1]} for this area and give only the numeric answer.''',

f'''
Evaluate the imagery for year {all_years[-1]}. The earlier years’ {indicator} values serve as historical background. Based on this, estimate the {indicator} value for this area for {all_years[-1]}.
Do not add any explanation—output the number only.''']

            question_part_final = random.choice(question_part_final_list)
            question_template += question_part_final

            new_element = {
                'sat_image_name': sat_image,
                'years': all_years,
                'city':city_name,
                'ids': f"{indicator}_{count}",
                'images': merged_images, # 合并所有图片的列表
                'prompt': question_template, # 假设prompt是相同的
                'references': int(all_references[-1]) # 合并所有reference
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
    with open(output_dir + f"{city_name}_{indicator}_multi_year_type1_stv_num_{max_stv_images}_year_num_{used_year_num}.json", "w", encoding="utf-8") as f:
        json.dump(reconstructed_data, f, indent=4, ensure_ascii=False)

    with open(output_dir + f"{city_name}_{indicator}_single_year_selected_type1_stv_num_{max_stv_images}_year_num_{used_year_num}.json", "w", encoding="utf-8") as f:
        json.dump(remained_items, f, indent=4, ensure_ascii=False)

    print("✅ JSON 模板已生成，保存在 output.json")


