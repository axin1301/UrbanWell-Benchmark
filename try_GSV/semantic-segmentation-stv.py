import json
from argparse import ArgumentParser
from mmengine.model import revert_sync_batchnorm
from mmseg.apis import inference_model, init_model
import numpy as np
from tqdm import tqdm
import pandas as pd
import glob
from PIL import Image
from pathlib import Path

def calculate_pixel_percentage(segmentation_map):
    """
    pixel percentage
    """
    total_pixels = segmentation_map.size
    unique, counts = np.unique(segmentation_map, return_counts=True)
    pixel_percentage = {int(label): count / total_pixels for label, count in zip(unique, counts)}
    return pixel_percentage

def main():
    parser = ArgumentParser()
    # parser.add_argument('img', help='Image file')
    # parser.add_argument('--config', default='configs/pspnet/pspnet_r50-d8_4xb2-40k_cityscapes-512x1024.py', help='Config file')
    # parser.add_argument('--checkpoint',  default='pspnet_r50-d8_512x1024_40k_cityscapes_20200605_003338-2966598c.pth',help='Checkpoint file')
    parser.add_argument('--config', default='configs/pspnet/pspnet_r101-d8_4xb4-80k_ade20k-512x512.py', help='Config file')
    parser.add_argument('--checkpoint',  default='pspnet_r101-d8_512x512_80k_ade20k_20200614_031423-b6e782f0.pth',help='Checkpoint file')
    parser.add_argument('--out-file', default='segmentation_results.json', help='Path to output JSON file')
    # parser.add_argument('--device', default='cpu', help='Device used for inference')
    parser.add_argument('--device', default='cuda:0', help='Device used for inference')
    args = parser.parse_args()

    args.img = 'demo/demo.png'

    image_key_list = []

    model = init_model(args.config, args.checkpoint, device=args.device)
    CLASSES = model.dataset_meta['classes']
    print(len(CLASSES))
    if 1:

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

        valid_sat_image_names = list(pd.read_csv('../download_sat/valid_image_lists.csv')['valid_image_name'])
        for city_name in list(city_csv['city_name'].drop_duplicates()):
            cnt= 0
            print(city_name)

            sat_stv_corr_csv_final = pd.DataFrame({})
            args.out_file = f'CitySense_stv-ade20k/{city_name}_stv-ade20k.json'
            data_new = []

            sat0 = pd.read_csv(f"../generate_dataset/inputs/sat_stv_list_dir/{city_name}_sat_stv_list.csv")
            sat1 = pd.read_csv(f"../generate_dataset/inputs/sat_stv_list_dir/{city_name}_sat_stv_list_no_stv.csv")
            sat_stv_corr_csv_full = pd.concat([sat0, sat1], ignore_index=True)
            sat_stv_corr_csv = sat_stv_corr_csv_full[sat_stv_corr_csv_full['sat_image_name'].isin(valid_sat_image_names)].reset_index(drop = True)
            sat_stv_corr_csv_final = pd.concat([sat_stv_corr_csv_final, sat_stv_corr_csv], ignore_index=True)
            sat_stv_corr_csv_final = sat_stv_corr_csv_final.reset_index(drop = True)

            for row_idx in tqdm(range(len(sat_stv_corr_csv_final))):
                if sat_stv_corr_csv_final.loc[row_idx,'stv_image_name'] == 'no_stv_image':
                    continue
                if sat_stv_corr_csv_final.loc[row_idx,'identifier'] == 'none':
                    img_path = f"../try_GSV/downloaded_stv_selected/{sat_stv_corr_csv_final.loc[row_idx,'city_name']}/{sat_stv_corr_csv_final.loc[row_idx,'sat_image_name'].split('.')[0]}/street_view_images/{sat_stv_corr_csv_final.loc[row_idx,'stv_image_name']}"
                else:
                    img_path = f"../try_GSV/downloaded_stv_selected/{sat_stv_corr_csv_final.loc[row_idx,'city_name']}/{sat_stv_corr_csv_final.loc[row_idx,'identifier']}/street_view_images/{sat_stv_corr_csv_final.loc[row_idx,'stv_image_name']}"
                try:
                    item = {}
                    image_path_pathlib = Path(img_path)
                    item['image'] = str(image_path_pathlib.name)
                    # item['image'] = img_path.split('/')[-1] #item['image'].split('/')[-1]
                    args.img = img_path
                    #
                    result = inference_model(model, img_path)
                    segmentation_map = result.pred_sem_seg.data.cpu().numpy().astype(int)

                    unique, counts = np.unique(segmentation_map, return_counts=True)
                    total_pixels = segmentation_map.size

                    #first 20 classes
                    ratios = [
                        (int(label), count / total_pixels)
                        for label, count in zip(unique, counts)
                        if label < len(CLASSES)
                    ]
                    ratios.sort(key=lambda x: x[1], reverse=True)
                    top15 = ratios[:20]

                    pixel_percentage = {
                        CLASSES[label]: round(ratio, 3)
                        for label, ratio in top15
                    }

                    data_new.append({
                        "image": item['image'],
                        "pixel_percentage": pixel_percentage,
                        "image_path": img_path
                    })
                except:
                    continue

            with open(args.out_file, 'w') as f:
                json.dump(data_new, f, indent=4)

if __name__ == '__main__':
    main()