from osgeo import gdal
import pandas as pd
import numpy as np
import os
from shapely.geometry import box
from shapely.ops import transform
import pyproj
import tqdm

#
# def mean_qsi_from_bbox(ds, min_lon, min_lat, max_lon, max_lat):
#     bbox_wgs84 = box(min_lon, min_lat, max_lon, max_lat)

#     project = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
#     bbox_3857 = transform(project, bbox_wgs84)
#     xmin, ymin, xmax, ymax = bbox_3857.bounds

#     gt = ds.GetGeoTransform()
#     inv_gt = gdal.InvGeoTransform(gt)

#     if isinstance(inv_gt, tuple) and len(inv_gt) == 2:
#         ok, inv_gt = inv_gt
#         if not ok:
#             raise RuntimeError("æ— æ³•åç®— GeoTransform")

#     px1, py1 = gdal.ApplyGeoTransform(inv_gt, xmin, ymax)
#     px2, py2 = gdal.ApplyGeoTransform(inv_gt, xmax, ymin)

#     xoff, yoff = int(min(px1, px2)), int(min(py1, py2))
#     xsize, ysize = int(abs(px2 - px1)), int(abs(py2 - py1))

#     band = ds.GetRasterBand(1)
#     arr = band.ReadAsArray(xoff, yoff, xsize, ysize)

#     if arr is None or arr.size == 0:
#         return -100
#     return float(np.nanmean(arr))

from rasterio.warp import transform_bounds
from osgeo import gdal
import numpy as np

def mean_qsi_from_bbox(ds, min_lon, min_lat, max_lon, max_lat):

    #
    src_wkt = ds.GetProjection()
    src_srs = gdal.osr.SpatialReference(wkt=src_wkt)
    src_epsg = src_srs.GetAttrValue("AUTHORITY", 1)
    src_crs = f"EPSG:{src_epsg}" if src_epsg else src_srs.ExportToWkt()

    #
    xmin, ymin, xmax, ymax = transform_bounds(
        "EPSG:4326", src_crs, min_lon, min_lat, max_lon, max_lat, densify_pts=21
    )
    #
    gt = ds.GetGeoTransform()
    inv_gt = gdal.InvGeoTransform(gt)
    if isinstance(inv_gt, tuple) and len(inv_gt) == 2:
        ok, inv_gt = inv_gt
        if not ok:
            raise RuntimeError("æ— æ³•åç®— GeoTransform")

    px1, py1 = gdal.ApplyGeoTransform(inv_gt, xmin, ymax)  #
    px2, py2 = gdal.ApplyGeoTransform(inv_gt, xmax, ymin)  #

    # 3.
    xoff = int(np.floor(min(px1, px2)))
    yoff = int(np.floor(min(py1, py2)))
    xend = int(np.ceil(max(px1, px2)))
    yend = int(np.ceil(max(py1, py2)))

    xsize = xend - xoff
    ysize = yend - yoff

    # 4. clamp
    xoff = max(0, xoff)
    yoff = max(0, yoff)
    xsize = min(ds.RasterXSize - xoff, xsize)
    ysize = min(ds.RasterYSize - yoff, ysize)

    # 5.
    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    arr = band.ReadAsArray(xoff, yoff, xsize, ysize)

    if arr is None or arr.size == 0:
        return np.nan

    # 6.
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)

    return float(np.nanmean(arr)) if arr.size > 0 else np.nan

def get_country_layers(layers, country_iso3):

    country_iso2_map = {
    'NLD': 'NL',
    'GRC': 'GR',
    'SRB': 'RS',
    'DEU': 'DE',
    'SVK': 'SK',
    'BEL': 'BE',
    'ROU': 'RO',
    'HUN': 'HU',
    'IRL': 'IE',
    'HRV': 'HR',
    'AUT': 'AT',
    'DNK': 'DK',
    'CYP': 'CY',
    'PRT': 'PT',
    'SVN': 'SI',
    'GBR': 'UK',   #
    'ESP': 'ES',
    'NOR': 'NO',
    'FRA': 'FR',
    'CZE': 'CZ',
    'XKX': 'XKX',  #
    'LVA': 'LV',
    'ITA': 'IT',
    'BIH': 'BA',
    'MKD': 'MK',
    'BGR': 'BG',
    'SWE': 'SE',
    'EST': 'EE',
    'ALB': 'AL',
    'LTU': 'LT',
    'POL': 'PL',
    'CHE': 'CH',
    'FIN': 'FI'
}
    print(country_iso3)
    iso2 = country_iso2_map.get(country_iso3.upper())
    if not iso2:
        raise ValueError(f"invalid data: {country_iso3}")
    
    # ç­›é€‰ layer
    selected = [ly for ly in layers if ly.startswith(iso2) and 'n2k' not in ly]
    return selected

# df_img: ImageFileName, Left_Edge_Longitude, Right_Edge_Longitude, Top_Edge_Latitude, Bottom_Edge_Latitude

gpkg_path = f"outputs/eea_raw_data/EEA/QA_results_europe.gpkg"

subdatasets = gdal.Open(gpkg_path).GetSubDatasets()
layers = [sd[0].split(":")[-1] for sd in subdatasets]

# layer_name = "SIqsiebk"  # 
# gdf = gpd.read_file(gpkg_path, layer=layer_name)
# print(gdf.head())

city_csv = (pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv'))
new_row = {
    "city_name": "HELSINKI",
    "city_full_name": "New City Full Name",
    "province": "New Province",
    "note": "Some note",
    "country_name": "New Country",
    "country_code": "fin"
}

new_row_df = pd.DataFrame([new_row])

city_csv = pd.concat([city_csv, new_row_df], ignore_index=True)

for i in range(len(city_csv)): # tqdm.tqdm(range(len(city_csv))):
    city_name = city_csv.at[i,'city_name']
    country_code = city_csv.at[i,'country_code']
    output_dir = "outputs/generated_QSI/"+city_name
    os.makedirs(output_dir, exist_ok=True)
    # year = 2018
    for year in [2022]:
        year_str = str(year)
        date = f"{year_str}-07-31"
        zoom_level = 16
        identifier = city_name
        
        destination_directory = (
            f"../download_sat/outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{identifier}\\{date}"
            + "/" + identifier + "/img_info/"
        )
        new_file_name = identifier + "_list1.txt"

        destination_file = os.path.join(destination_directory, new_file_name)

        df_img = pd.read_csv(destination_file, delim_whitespace=True)
        df_img["ImageFileName"] = df_img["ImageFileName"].str.replace(":", "", regex=False)

        results = []

        layer = get_country_layers(layers, country_code)
        if not layer:
            continue

        layer_name = layer[0]
        ds = gdal.Open(f"GPKG:{gpkg_path}:{layer_name}")
        if ds is None:
            raise RuntimeError(f"error‚ {layer_name}")

        # --- bbox ---
        for _, img_row in df_img.iterrows():
            image_name = img_row["ImageFileName"]

            min_lon = min(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            max_lon = max(img_row['Left_Edge_Longitude'], img_row['Right_Edge_Longitude'])
            min_lat = min(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])
            max_lat = max(img_row['Bottom_Edge_Latitude'], img_row['Top_Edge_Latitude'])

            mean_qsi = mean_qsi_from_bbox(ds, min_lon, min_lat, max_lon, max_lat)

            results.append({
                "ImageFileName": image_name,
                "layer": layer_name,
                "mean_QSI": mean_qsi
            })

        df_out = pd.DataFrame(results)
        df_out.to_csv(output_dir + f"/{city_name}_QSI_{2016}.csv", index=False)

