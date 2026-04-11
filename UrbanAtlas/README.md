# UrbanAtlas

This module prepares the urban-core boundary, land-use, and land-use-change inputs used by the later stages of the UrbanWell pipeline.

## Raw inputs

Place the raw Urban Atlas files under this directory before running the scripts.

Typical inputs include:
- Urban Atlas archives for 2012 and 2018
- Urban Atlas change products
- city-level or FUA-level source files downloaded from Copernicus

The workflow expects the extracted files to be organized into directories such as:
- `unziped_files_LU_2012/`
- `unziped_files_LU_2018/`
- `unziped_files_LU_change/`

## Configuration notes

The submission scripts in this folder now keep their main input and output directories as constants near the top of each file.
Before running them, first check paths such as:
- `INPUT_GPKG_GLOB`
- `CENTROID_DIR`
- `OUTPUT_DIR`
- `BBOX_EXTENSION_METERS`

In practice, the most important requirement is to preserve the expected unzip structure under `unziped_files_LU_change/` and to write outputs under `outputs/`.

## Main outputs

The scripts in this folder generate intermediate files under directories such as:
- `outputs/urbancore_bbox_dir/`
- `outputs/urbanchange_centroids_dir/`
- `outputs/output_LU_single_year/`
- `outputs/output_LU_mix_dir/`
- `outputs/landuse_reference/`

These outputs are later consumed by:
- `download_sat`
- `generate_dataset`

## Suggested order

1. `unzip_all_files.py`
2. `generate_bbox_lonlat_urbancore_MoreCity.py`
3. `calculate_change_centroids_MoreCity.py`
4. `read_centroids_and_generate_bbox_for_sat_MoreCity.py`
5. `landuse_categories_extraction.py`
6. `landuse_MoreCity.py`
7. `landuse_mix_MoreCity.py`
8. `calculate_urban_bbox_area.py`

## Python Files

- `calculate_change_centroids_MoreCity.py`: extracts land-use-change centroids within the UrbanCore boundary.
- `calculate_urban_bbox_area.py`: calculates area statistics for UrbanCore bounding boxes.
- `generate_bbox_lonlat_urbancore_MoreCity.py`: generates UrbanCore bounding boxes in longitude/latitude.
- `landuse_categories_extraction.py`: exports the Urban Atlas land-use category reference table.
- `landuse_mix_MoreCity.py`: calculates land-use-mix values for satellite image regions.
- `landuse_MoreCity.py`: assigns land-use classes to satellite image regions.
- `read_centroids_and_generate_bbox_for_sat_MoreCity.py`: converts change centroids into bounding boxes for satellite image download.
- `unzip_all_files.py`: unzips Urban Atlas source files for later processing.
- `City_list.csv`: city list used by some batch scripts.

