# Worldpop

This module downloads WorldPop population rasters, prepares city-selection references, and extracts population values for each satellite-image region.

## Required inputs

Typical upstream inputs include:
- city population reference tables
- selected satellite-image regions from `download_sat`

## Configuration notes

The main submission scripts in this folder now keep their important path settings near the top of each file.
Before running them, first check values such as:
- `EUROPE_ISO3`
- `YEARS`
- `OUTPUT_DIR`
- `CITY_TABLE_PATH`
- `DOWNLOAD_SAT_OUTPUT_ROOT`
- `WORLDPOP_RASTER_DIR`

The extraction script expects the satellite-image metadata lists from `download_sat/outputs/downloaded_sat_<YEAR>_zoom_16/.../img_info/`.

## Main outputs

The scripts in this folder generate files under directories such as:
- `outputs/city_selection/`
- `outputs/worldpop_rasters/`
- `outputs/output_popu_dir/`

These outputs are later consumed by:
- `generate_dataset`

## Suggested order

1. `select_most_populated_cities_EU.py`
2. `download_world_pop.py`
3. `extract_world_pop_MoreCity.py`

## Python Files

- `download_world_pop.py`: downloads WorldPop population raster files.
- `extract_world_pop_MoreCity.py`: extracts population values for each satellite-image region in the multi-city workflow.
- `select_most_populated_cities_EU.py`: selects the most populated city for each country from the city population table.

## Other Files

- `europe-cities-by-population-2025.csv`: reference city population table used for city selection.

