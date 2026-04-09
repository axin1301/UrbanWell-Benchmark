import os
import pandas as pd
import torch
import torch.nn as nn
import tqdm
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import torchvision.transforms as T
from PIL import Image

perception = ['safety', 'lively', 'wealthy',
              'beautiful', 'boring', 'depressing']

model_dict = {
    'safety': 'safety.pth',
    'lively': 'lively.pth',
    'wealthy': 'wealthy.pth',
    'beautiful': 'beautiful.pth',
    'boring': 'boring.pth',
    'depressing': 'depressing.pth',
}

train_transform = T.Compose([
    T.Resize((384, 384)),
    T.ToTensor(),
    T.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225])
])

BATCH_SIZE = 16  # GPU 

# ------------------
def predict_batch(model, img_paths, device, transform):
    imgs = []
    valid_paths = []
    for img_path in img_paths:
        if os.path.getsize(img_path) < 20000:
            continue
        try:
            img = Image.open(img_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img = transform(img)
            imgs.append(img)
            valid_paths.append(img_path)
        except:
            continue

    if not imgs:
        return []

    batch_tensor = torch.stack(imgs).to(device)
    model.eval()
    with torch.no_grad():
        preds = model(batch_tensor)
        softmax = nn.Softmax(dim=1)
        preds = softmax(preds)[:, 1]  #
        preds = (preds * 10).round(decimals=2).cpu().numpy().tolist()

    return list(zip([os.path.basename(p) for p in valid_paths], preds))


# ------------------------------
def process_city_model(city_name, p, model_load_path, model_dict, device):
    model_path = os.path.join(model_load_path, model_dict[p])
    model = torch.load(model_path, map_location=device, weights_only=False)
    if torch.cuda.device_count() > 1:
        model = nn.DataParallel(model)
    model = model.to(device)
    model.eval()

    print(f"######### {p} - {city_name} #########")

    input_csv = f"../download_sat/Landuse_Change_2012_2018_urbancore/{city_name}_sat_image_landuse_change_2012_2018_urbancore.csv"
    df_input = pd.read_csv(input_csv)

    out_Path = "./outputs/output_stv_selected/" + city_name
    os.makedirs(out_Path, exist_ok=True)

    for idx, row in tqdm.tqdm(df_input.iterrows(), total=len(df_input)):
        identifier = str(row['fua_code'])
        images_path = f"../try_GSV/outputs/downloaded_stv_selected/{city_name}/{identifier}/street_view_images/"
        out_csvPath = os.path.join(out_Path, f"{identifier}_street_view_images_{p}.csv")
        df_columns = ['img_path', f"{p}_score"]

        if os.path.exists(out_csvPath) and os.path.getsize(out_csvPath) > 20:
            df_existing = pd.read_csv(out_csvPath)
            processed_imgs = set(df_existing['img_path'].tolist())
        else:
            df_existing = pd.DataFrame(columns=df_columns)
            processed_imgs = set()
        
        # df_existing = pd.DataFrame(columns=df_columns)
        # processed_imgs = set()

        if not os.path.exists(images_path):
            continue

        all_imgs = [os.path.join(images_path, img) for img in os.listdir(images_path) if img not in processed_imgs]

        data_arr = []
        for i in range(0, len(all_imgs), BATCH_SIZE):
            batch_imgs = all_imgs[i:i + BATCH_SIZE]
            data_arr.extend(predict_batch(model, batch_imgs, device, train_transform))

        if data_arr:
            df_new = pd.DataFrame(data_arr, columns=df_columns)
            combined_df = pd.concat([df_existing, df_new], ignore_index=True)
            combined_df.to_csv(out_csvPath, index=False)


# ----------------
if __name__ == "__main__":
    model_load_path = "pretrained_weights"
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print("using device:{} ".format(device))

    city_list = list(pd.read_csv('../UrbanAtlas/City_list.csv')['city_name'])

    with ProcessPoolExecutor(max_workers=2) as executor:  # CPU 
        for p in perception:
            func = partial(process_city_model,
                           p=p,
                           model_load_path=model_load_path,
                           model_dict=model_dict,
                           device=device)
            executor.map(func, city_list)

