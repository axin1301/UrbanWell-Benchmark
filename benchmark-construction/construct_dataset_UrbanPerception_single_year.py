import os
import json
import random
import pandas as pd
import numpy as np
import tqdm
from collections import defaultdict

random.seed(42)

# === 加载城市列表（原样） ===
city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
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
BASE_DIR1 = '../placepulse_models/output_stv_selected'
BASE_DIR2 = '../placepulse_models/output_stv_selected_urban_sup'

restriction_list = [
    "Provide a value between -9.9 and 9.9 with exactly one decimal place. Do not include any text or explanation.",
    "Output only a numerical value from -9.9 to 9.9 with one decimal place, nothing else.",
    "Respond strictly with a number between -9.9 and 9.9, rounded to one decimal. No further text.",
    "Give a single numeric value from -9.9 to 9.9 with one decimal place only, without explanation.",
    "Provide just one number in the range -9.9 to 9.9, rounded to one decimal. Do not write any other text."
]

pp2_context = (
    "PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images "
    "to judge perceptions of urban environments. It defines six perceptual dimensions: 'safe', 'lively', "
    "'beautiful', 'wealthy', 'boring', and 'depressing'. Each image receives a perceptual score derived from "
    "these pairwise comparisons, typically normalized. Interpret the indicator as the PlacePulse 2.0 perceptual score."
)

# === 新增：加载 reference CSV ===
sat_reference_csv_path = "generated_QA/all_cities_yearly_sat_scores.csv"   # 你的新csv路径
ref_df = pd.read_csv(sat_reference_csv_path)
# 建立快速查找字典： (city, year, sat_image_name, indicator, num_stv) -> mean_score
ref_dict = {
    (r.city, int(r.year), r.sat_image_name, r.indicator, int(r.num_stv)): float(r.mean_score)
    for r in ref_df.itertuples(index=False)
}

# ---------- 预加载 score_cache ----------
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

# ---------- 主流程 ----------
for city_row in tqdm.tqdm(city_csv.itertuples(index=False), desc="cities"):
    city_name = city_row.city_name
    if city_name not in TARGET_CITIES:
        continue

    sat0_path = f"../final_dataset/sat_stv_list_dir/{city_name}_sat_stv_list.csv"
    sat1_path = f"../final_dataset/sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv"
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

    output_dir = f'generated_QA/{city_name}/'
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

                # === ✅ 改动核心：从 ref_dict 查找 reference_value ===
                # 找出所有该城市、年份、sat图像、指标匹配的记录
                possible_refs = [
                    (k, v)
                    for k, v in ref_dict.items()
                    if k[0] == city_name and int(k[1]) == int(year)
                    and k[2] == sat_image_name and k[3] == ind
                    and int(k[4]) >= 4   # 只要 num_stv >= 4
                ]

                if not possible_refs:
                    continue

                # 随机选一个参考行（或取平均都行）
                ref_key, reference_value = random.choice(possible_refs)

                # 固定取4张街景图
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





##########################################--------------------------------------------------------------------------
# import os
# import json
# import random
# import pandas as pd
# import numpy as np
# import tqdm
# from collections import defaultdict

# random.seed(42)

# city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
# # 添加测试城市 HE LSINKI（和你原来相同）
# city_csv = pd.concat([city_csv, pd.DataFrame([{
#     "city_name":"HELSINKI","city_full_name":"New City Full Name",
#     "province":"New Province","note":"Some note","country_name":"New Country"
# }])], ignore_index=True)

# # 配置
# TARGET_CITIES = list(city_csv['city_name'])
# # ['HELSINKI']          # 只跑哪些城市（调试用）
# INDICATORS = ['safety','lively','wealthy','beautiful','boring','depressing']
# NUM_STV_LIST = [4, 10]
# BASE_DIR1 = '../placepulse_models/output_stv_selected'         # 普通 dir
# BASE_DIR2 = '../placepulse_models/output_stv_selected_urban_sup'  # fallback dir

# restriction_list = [
#     "Provide a value between -9.9 and 9.9 with exactly one decimal place. Do not include any text or explanation.",
#     "Output only a numerical value from -9.9 to 9.9 with one decimal place, nothing else.",
#     "Respond strictly with a number between -9.9 and 9.9, rounded to one decimal. No further text.",
#     "Give a single numeric value from -9.9 to 9.9 with one decimal place only, without explanation.",
#     "Provide just one number in the range -9.9 to 9.9, rounded to one decimal. Do not write any other text."
# ]

# pp2_context = (
#     "PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images "
#     "to judge perceptions of urban environments. It defines six perceptual dimensions: 'safe', 'lively', "
#     "'beautiful', 'wealthy', 'boring', and 'depressing'. Each image receives a perceptual score derived from "
#     "these pairwise comparisons, typically normalized. Interpret the indicator as the PlacePulse 2.0 perceptual score."
# )

# # ---------- 预加载 score_cache（一次性） ----------
# # 结构: score_cache[indicator][key_name] = {basename(img_path): score, ...}
# score_cache = {ind: {} for ind in INDICATORS}

# def preload_score_cache_for_city(city_name):
#     """
#     预加载给定城市、所有 indicator 的 score csv（只读一次）。
#     文件名 pattern: <key>_street_view_images_<indicator>.csv
#     我们把 key 保持为 <key>_street_view_images（正好和你现存 key 一致）
#     并把存储的 img_path 都转换为 os.path.basename 作为字典 key。
#     """
#     for ind in INDICATORS:
#         # 搜两个目录
#         for base_dir in (BASE_DIR1, BASE_DIR2):
#             dir_path = os.path.join(base_dir, city_name)
#             if not os.path.isdir(dir_path):
#                 continue
#             for fname in os.listdir(dir_path):
#                 # 匹配后缀
#                 suffix = f"_street_view_images_{ind}.csv"
#                 if not fname.endswith(suffix):
#                     continue
#                 key_name = fname.replace(suffix, "") + "_street_view_images"  # e.g. "20357-NL002L3_street_view_images"
#                 fullpath = os.path.join(dir_path, fname)
#                 try:
#                     df = pd.read_csv(fullpath, usecols=['img_path', f'{ind}_score'])
#                 except Exception:
#                     continue
#                 # 构造 basename -> score
#                 basename_scores = {os.path.basename(p): float(s) for p, s in zip(df['img_path'], df[f'{ind}_score'])}
#                 score_cache[ind][key_name] = basename_scores

# # ---------- 主流程 ----------
# for city_row in tqdm.tqdm(city_csv.itertuples(index=False), desc="cities"):
#     city_name = city_row.city_name
#     if city_name not in TARGET_CITIES:
#         continue

#     # load sat-stv mapping once
#     sat0_path = f"sat_stv_list_dir/{city_name}_sat_stv_list.csv"
#     sat1_path = f"sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv"
#     if not os.path.exists(sat0_path) and not os.path.exists(sat1_path):
#         print(f"[WARN] no sat-stv list for {city_name}")
#         continue
#     dfs = []
#     if os.path.exists(sat0_path):
#         dfs.append(pd.read_csv(sat0_path))
#     if os.path.exists(sat1_path):
#         dfs.append(pd.read_csv(sat1_path))
#     sat_stv_corr_csv = pd.concat(dfs, ignore_index=True)

#     # 将 sat_stv_corr 按 (year, sat_image_name) 分组，避免重复处理同一 sat-image
#     grouped = sat_stv_corr_csv.groupby(['year', 'sat_image_name']).agg({
#         'identifier': 'first',
#         'stv_image_name': lambda x: list(x)   # list of street view names linked to this sat
#     }).reset_index()

#     # 预加载该城市的 score files
#     preload_score_cache_for_city(city_name)

#     output_dir = f'generated_QA/{city_name}/'
#     os.makedirs(output_dir, exist_ok=True)

#     # 为每个 (indicator, number_of_stv) 建立一个 list 存 entries
#     entries_dict = {(ind, n): [] for ind in INDICATORS for n in NUM_STV_LIST}

#     # 遍历分组后的 sat-image（每个 sat-image 在该年只出现一次）
#     for grp in tqdm.tqdm(grouped.itertuples(index=False), total=len(grouped), desc=f"{city_name} sat_images"):
#         year = grp.year
#         sat_image_name = grp.sat_image_name
#         identifier = grp.identifier
#         stv_full_list = grp.stv_image_name  # full strings as in sat_stv table
#         # 把 basename 列表预做一次
#         stv_basenames = [os.path.basename(x) for x in stv_full_list]
#         sat_image_stem = os.path.splitext(sat_image_name)[0]

#         # 构造 key：与 score_cache 的 key 保持一致（你之前的 score_cache keys 有后缀 _street_view_images）
#         key = (identifier if str(identifier).lower() != 'none' else sat_image_stem) + "_street_view_images"

#         # 对每个 indicator+num_stv 尝试生成 entry
#         for n in NUM_STV_LIST:
#             # 我们在每个 indicator 内部判断是否有足够候选（避免跨 indicator 共享样本导致缺分）
#             for ind in INDICATORS:
#                 # 如果该 indicator 没有为该 key 的分数字典，则跳过
#                 if key not in score_cache[ind]:
#                     continue
#                 scores_dict = score_cache[ind][key]  # basename -> score
#                 # 因为 scores_dict 的 key 已是 basename，所以直接交集
#                 # 找到既属于该 sat 的 stv，又在 scores_dict 中的候选
#                 candidates = [b for b in stv_basenames if b in scores_dict]
#                 if len(candidates) < n:
#                     # 该指标在这个 sat 上没有足够的带分数的 street-view
#                     continue

#                 # 随机选 n 个（可保持 random.seed 全局一致）
#                 sampled = random.sample(candidates, n)
#                 # 计算均值（float），并恢复回原始的 stv full paths 用于 "images" 字段
#                 basename_to_full = {os.path.basename(x): x for x in stv_full_list}
#                 sampled_full_paths = [basename_to_full[b] for b in sampled]
#                 reference_value = round(float(np.mean([scores_dict[b] for b in sampled])), 1)

#                 # 模板（复用你的描述）
#                 templates = [
# f"Suppose you are a vision expert for sensing urban environment from human perspectives. You are given {n + 1} images of a region: the first is a satellite image from year {year}, followed by {n} street views from the same year. Using the observable features in the images together with the additional information provided, analyze the {ind} value using PlacePulse 2.0 dataset as the reference for this area.",
# f"Suppose you are a vision expert for sensing urban environment from human perspectives. Examine {n + 1} images from the same region: 1 satellite image from year {year}, and {n} street views from the same year. Consider both the imagery content and the supplementary details given, provide your assessment of the {ind} value using PlacePulse 2.0 dataset as the reference for this area.",
# f"Suppose you are a vision expert for sensing urban environment from human perspectives. Consider the {n + 1} images provided for the region: the first is a satellite image from year {year}, and the remaining {n} are street views from the same year. Using the observable features in the images together with the additional information provided, estimate the {ind} value for this area using PlacePulse 2.0 dataset as the reference.",
# f"Suppose you are a vision expert for sensing urban environment from human perspectives. You are given {n + 1} images for the same region, including 1 satellite and {n} street views from year {year}. Using the observable features in the images together with the additional information provided, infer the {ind} value for this area using PlacePulse 2.0 dataset as the reference.",
# f"Suppose you are a vision expert for sensing urban environment from human perspectives. Analyze {n + 1} images from the region: first a satellite image from year {year}, then {n} street views from the same year. Using the observable features in the images together with the additional information provided, determine the {ind} value for this area using PlacePulse 2.0 dataset as the reference."
#                 ]

#                 entry = {
#                     "id": f"{ind}_{len(entries_dict[(ind, n)])}",
#                     "sat_image_name": sat_image_name,
#                     "identifier": identifier,
#                     "year": year,
#                     "images": [sat_image_name] + sampled_full_paths,
#                     "prompt": f"{random.choice(templates)}\n{pp2_context}\n{random.choice(restriction_list)}",
#                     "reference": reference_value
#                 }
#                 entries_dict[(ind, n)].append(entry)

#     # 最后把每个 indicator/number 写出文件
#     for (ind, n), entries in entries_dict.items():
#         out_path = os.path.join(output_dir, f"{city_name}_{ind}_single_year_stv_num_{n}.json")
#         with open(out_path, "w", encoding="utf-8") as f:
#             json.dump(entries, f, indent=4, ensure_ascii=False)

#     print(f"[DONE] {city_name} -> wrote JSONs to {output_dir}")

###############################################-------------------------------------------------------------------

# import json
# import pandas as pd
# import random
# import os
# from indicator_col_name_in_prompt import *
# # col_name_dict, indicator_name_dict
# import tqdm
# import numpy as np

# random.seed(42)

# # number_of_stv = 4
# #[2, 4, 8, 12]:
# city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
# new_row = {
#     "city_name": "HELSINKI",
#     "city_full_name": "New City Full Name",
#     "province": "New Province",
#     "note": "Some note",
#     "country_name": "New Country"
# }

# # 转为 DataFrame
# new_row_df = pd.DataFrame([new_row])

# # 拼接到原 DataFrame
# city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

# for i in tqdm.tqdm(range(len(city_csv)-1,len(city_csv))):  # 调试时只跑 1 个城市
#     city_name = city_csv.at[i, 'city_name']
#     city_full_name = city_csv.at[i, 'city_full_name']
#     province = city_csv.at[i, 'province']
#     note = city_csv.at[i, 'note']
#     country_name = city_csv.at[i, 'country_name']
    
#     if city_name in ['PRISTINA','LEFKOSIA','SARAJEVO']:
#         continue
#     if city_name not in ['HELSINKI']:
#         continue

#     sat_stv_corr_csv0 = pd.read_csv(f"sat_stv_list_dir/{city_name}_sat_stv_list.csv") ## 有街景图像的sat-stv
#     sat_stv_corr_csv1 = pd.read_csv(f"sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv") ## 无街景图像的sat
#     sat_stv_corr_csv = pd.concat([sat_stv_corr_csv0, sat_stv_corr_csv1], ignore_index=True)

#     # city_name,identifier,sat_image_name,year,stv_image_name

#     output_dir = f'generated_QA\\{city_name}/'
#     import os
#     os.makedirs(output_dir, exist_ok=True)

#             # 先生成空模板
    
#     for indicator in ['safety', 'lively', 'wealthy', 'beautiful', 'boring', 'depressing']:
#         for number_of_stv in [4,10]:
#             cnt = 0
#             new_data = []
            
#             for year in range(2012,2025):
#                 sat_stv_corr_csv_year = sat_stv_corr_csv[sat_stv_corr_csv['year']==year].reset_index(drop=True)
#                 for i in range(len(sat_stv_corr_csv_year)):
#                     identifier = sat_stv_corr_csv_year.at[i, 'identifier']
#                     sat_image_name =  sat_stv_corr_csv_year.at[i,'sat_image_name']
#                     sat_image_row = sat_image_name.split('_')[1]
#                     sat_image_stem = sat_image_name.split('.')[0]
#                     if identifier == 'none':
#                         stv_score_path = f'../placepulse_models/output_stv_selected_urban_sup/{city_name}/{sat_image_stem}_street_view_images_{indicator}.csv'
#                     else:
#                         stv_score_path = f'../placepulse_models/output_stv_selected/{city_name}/{identifier}_street_view_images_{indicator}.csv'

#                     # print(input_csv_path)
#                     if not os.path.exists(stv_score_path):
#                         continue
#                     df = pd.read_csv(stv_score_path)
#                     # 你要生成多少条记录
#                     merged_df = pd.merge(df, sat_stv_corr_csv_year, 
#                                         left_on='img_path', 
#                                         right_on='stv_image_name', 
#                                         how='inner')

#                     if merged_df.shape[0] >= number_of_stv:
#                         # 随机抽取 sample_size 行
#                         sampled_df = merged_df.sample(n=number_of_stv, random_state=42)
#                     else:
#                         continue

#                     # 限制说明
#                     restriction_list = [
#                         "Provide a value between -9.9 and 9.9 with exactly one decimal place. Do not include any text or explanation.",
#                         "Output only a numerical value from -9.9 to 9.9 with one decimal place, nothing else.",
#                         "Respond strictly with a number between -9.9 and 9.9, rounded to one decimal. No further text.",
#                         "Give a single numeric value from -9.9 to 9.9 with one decimal place only, without explanation.",
#                         "Provide just one number in the range -9.9 to 9.9, rounded to one decimal. Do not write any other text."
#                     ]

#                     number_of_stv_actual = number_of_stv

#                     pp2_context = (
#                         "PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images "
#                         "to judge perceptions of urban environments. It defines six perceptual dimensions: 'safe', 'lively', "
#                         "'beautiful', 'wealthy', 'boring', and 'depressing'. Each image receives a perceptual score derived from "
#                         "these pairwise comparisons, typically normalized to represent how strongly the place is perceived along that dimension. "
#                         f"When referring to the {indicator} value, interpret it strictly in this PlacePulse 2.0 sense—that is, as the perceived degree "
#                         f"of '{indicator}' for the given region—based on visual cues such as greenery, building condition, openness, street activity, "
#                         "lighting, and upkeep."
#                         )
                    
#                     pairwise_question_templates = [
#                         f"Suppose you are a vision expert. You are given {number_of_stv_actual + 1} images of a region: the first is a satellite image from year {year}, followed by {number_of_stv_actual} street views from the same year. Using the observable features in the images together with the additional information provided, analyze the {indicator} value using PlacePulse 2.0 dataset as the reference for this area.",

#                         f"Suppose you are a vision expert. Examine {number_of_stv_actual + 1} images from the same region: 1 satellite image from year {year}, and {number_of_stv_actual} street views from the same year. Consider both the imagery content and the supplementary details given, provide your assessment of the {indicator} value using PlacePulse 2.0 dataset as the reference for this area.",

#                         f"Suppose you are a vision expert. Consider the {number_of_stv_actual + 1} images provided for the region: the first is a satellite image from year {year}, and the remaining {number_of_stv_actual} are street views from the same year. Using the observable features in the images together with the additional information provided, estimate the {indicator} value for this area using PlacePulse 2.0 dataset as the reference.",

#                         f"Suppose you are a vision expert. You are given {number_of_stv_actual + 1} images for the same region, including 1 satellite and {number_of_stv_actual} street views from year {year}. Using the observable features in the images together with the additional information provided, infer the {indicator} value for this area using PlacePulse 2.0 dataset as the reference.",

#                         f"Suppose you are a vision expert. Analyze {number_of_stv_actual + 1} images from the region: first a satellite image from year {year}, then {number_of_stv_actual} street views from the same year. Using the observable features in the images together with the additional information provided, determine the {indicator} value for this area using PlacePulse 2.0 dataset as the reference."
#                     ]

#                     reference_value = np.mean(list(sampled_df[indicator+'_score']))

#                     entry = {
#                         "id": indicator + '_' + str(cnt),
#                         "sat_image_name": sat_image_name,
#                         "identifier": identifier,
#                         "year": year,
#                         "images": [sat_image_name] + list(sampled_df['stv_image_name']),
#                         "prompt": f"{random.choice(pairwise_question_templates)}\n{pp2_context}\n{random.choice(restriction_list)}",
#                         "reference": round(reference_value,1),
#                     }
#                     new_data.append(entry)
#                     # if cnt == 3:
#                     #     break
#                     cnt += 1

#                 # 保存到 JSON 文件
#             with open(output_dir + f"{city_name}_{indicator}_single_year_stv_num_{number_of_stv}.json", "w", encoding="utf-8") as f:
#                 json.dump(new_data, f, indent=4, ensure_ascii=False)

#             # print("✅ JSON 模板已生成，保存在 output.json")