import os
import zipfile

source_dir = "unziped_files_LU_change"  #

# output_root = "unziped_files_LU_2018"  # submission output path
output_root = "unziped_files_LU_2012"  # submission output path


for filename in os.listdir(source_dir):
    if filename.endswith(".zip"):
        
        zip_path = os.path.join(source_dir, filename)
        parts = filename.split("_")
        if len(parts) < 2:
            continue
        folder_name = parts[1]
        
        output_dir = os.path.join(output_root, folder_name)
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        print(f"{filename} saved to {output_dir}")

