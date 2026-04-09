import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, box
import pyproj
from shapely.ops import transform
import glob
from pathlib import Path

def latlon_to_utm_crs(lat, lon):
    zone = int((lon + 180) / 6) + 1
    south = lat < 0
    epsg_code = 32600 + zone if not south else 32700 + zone
    return pyproj.CRS(f"EPSG:{epsg_code}")

def create_bbox_wgs84(point, extension_m):
    lat, lon = point.y, point.x
    utm_crs = latlon_to_utm_crs(lat, lon)
    wgs84_crs = pyproj.CRS("EPSG:4326")

    project_to_utm = pyproj.Transformer.from_crs(wgs84_crs, utm_crs, always_xy=True).transform
    project_to_wgs84 = pyproj.Transformer.from_crs(utm_crs, wgs84_crs, always_xy=True).transform
    x, y = transform(project_to_utm, point).x, transform(project_to_utm, point).y

    bbox_utm = box(x - extension_m, y - extension_m, x + extension_m, y + extension_m)
    bbox_wgs84 = transform(project_to_wgs84, bbox_utm)
    minx, miny, maxx, maxy = bbox_wgs84.bounds
    return pd.Series({
        "min_lon": minx,
        "min_lat": miny,
        "max_lon": maxx,
        "max_lat": maxy
    })


gpkg_list = glob.glob('unziped_files_LU_change/*/*/Data/*.gpkg')

for gpkg_path in gpkg_list:
    city_name = Path(gpkg_path).parts[1]
    csv_path = 'outputs/urbanchange_centroids_dir/' + f"{city_name}_urban_filtered_centroids_wgs84.csv"
    output_csv_path = 'outputs/urbanchange_centroids_dir/' + f"{city_name}_output_bboxes_with_all_attributes.csv"
    extension_meters = 10

    print(f"A square bbox with side length {2*extension_meters} meters will be generated for each centroid.")

    df = pd.read_csv(csv_path)
    print(f"Successfully read the CSV file with {len(df)} points.")
    print(df.head())

    wgs84 = "EPSG:4326"
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs=wgs84
    )

    bbox_df = gdf.geometry.apply(lambda pt: create_bbox_wgs84(pt, extension_meters))
    final_df = pd.concat([df, bbox_df], axis=1)

    final_df.to_csv(output_csv_path, index=False)
    print(f"Successfully generated bboxes and saved them to '{output_csv_path}'")
    print(final_df.head())

