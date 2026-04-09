import geopandas as gpd
import pandas as pd
import os

# Example Urban Atlas land-use GPKG path and layer name.
gpkg_path = r"FI001L3_HELSINKI_UA2018_v013/FI001L3_HELSINKI_UA2018_v013/Data/FI001L3_HELSINKI_UA2018_v013.gpkg"
layer_name = "FI001L3_HELSINKI_UA2018"

gdf = gpd.read_file(gpkg_path, layer=layer_name)
unique_classes = sorted(gdf['class_2018'].dropna().unique())

df_classes = pd.DataFrame(unique_classes, columns=['class_2018'])
os.makedirs("outputs/landuse_reference", exist_ok=True)
df_classes.to_csv("outputs/landuse_reference/landuse_class_2018_categories.csv", index=False, encoding="utf-8")

print(f"extract {len(unique_classes)} categories, and saved to outputs/landuse_reference/landuse_class_2018_categories.csv")
