# OSM_data

This module downloads OSM raw data and generates road-network, accessibility, and economic-activity indicators for each satellite-image region.

## Required inputs

Typical upstream inputs include:
- satellite-image regions from `download_sat`
- country or city selections used for downloading Geofabrik extracts
- boundary or bbox files used for clipping road and POI layers

## Configuration notes

The lighter submission scripts in this folder now keep their main path settings near the top of each file.
Before running them, first check values such as:
- `CITY_TABLE_PATH`
- `URBANCORE_BBOX_DIR`
- `DOWNLOAD_SAT_OUTPUT_ROOT`
- `OSM_RAW_DIR`
- `PROCESSED_OSM_DIR`
- `OUTPUT_DIR`
- `YEARS`

Most scripts in this module still reflect research-workspace assumptions, but `diversity_of_economic_activity_any_year_MoreCity.py` and `generate_road_access_update_mp_update.py` now expose their main path settings near the top of the file. The remaining OSM scripts are still best treated as documented reference pipelines rather than polished command-line packages.

## Main outputs

The scripts in this folder generate files under directories such as:
- `outputs/osm_raw_data/`
- `outputs/unzipped_osm_files/`
- `outputs/processed_osm_data/`
- `outputs/output_economic_dir_update/`
- `outputs/accessability_output_only_POI_update/`
- `outputs/road-output/`

These outputs are later consumed by:
- `generate_dataset`

## Suggested order

1. `download_osm_data.py`
2. `exclude_non_commercial_pois.py`
3. `diversity_of_economic_activity_any_year_MoreCity.py`
4. `generate_road_access_only_dist_poi.py`
5. `generate_road_access_update_mp_update.py`

## Python Files

- `download_osm_data.py`: downloads raw OSM shapefile packages for the selected countries, cities, and years.
- `exclude_non_commercial_pois.py`: unzips OSM shapefiles and keeps only commercial / economic POIs.
- `diversity_of_economic_activity_any_year_MoreCity.py`: calculates economic activity diversity for each satellite-image region.
- `generate_road_access_only_dist_poi.py`: calculates POI-distance based accessibility features for each region.
- `generate_road_access_update_mp_update.py`: reads OSM road and POI layers together with satellite-image bbox lists, optionally filters to a research image subset, and exports road length, road density, POI counts, and nearest-POI accessibility features for each region.


