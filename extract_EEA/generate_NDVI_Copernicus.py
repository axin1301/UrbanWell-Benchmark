import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import networkx as nx
import osmnx as ox
import numpy as np
from shapely.geometry import Point, Polygon
from collections import Counter
from joblib import Parallel, delayed
import os
import pandas as pd
from shapely.geometry import box
from shapely.geometry import Point, LineString, MultiLineString
import json


year = 2022
year_str = str(year - 2000 + 1) + "0101"
zoom_level = 16
date = f"{year}-07-31"

city_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')

all_records = []
bboxes = []
for i in range(len(city_csv)):  #
    city_name = city_csv.at[i, 'city_name']
    city_full_name = city_csv.at[i, 'city_full_name']
    province = city_csv.at[i, 'province']
    note = city_csv.at[i, 'note']
    country_name = city_csv.at[i, 'country_name']

    city_bound = pd.read_csv(f"../UrbanAtlas/outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")

    minx, miny, maxx, maxy = city_bound.at[0,'min_lon'],city_bound.at[0,'min_lat'],city_bound.at[0,'max_lon'],city_bound.at[0,'max_lat']  # ç¤ºä¾‹ EPSG:3857 
    # helsinki_bbox = box(minx, miny, maxx, maxy)
    # bboxes.append((minx, miny, maxx, maxy))
    data = [
        {"EPSG": 4326, "lat": maxy, "lon": minx},  #
        {"EPSG": 4326, "lat": miny, "lon": maxx}   #
    ]

    out_csv = f"outputs/NDVI_bbox_csv/{city_name}_bbox_points.csv"
    df = pd.DataFrame(data)
    df.to_csv(out_csv, index=False)