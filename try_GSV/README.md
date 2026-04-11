# try_GSV

This module generates Street View sampling points, queries panoramas, downloads Street View images, and prepares Street View metadata.

## API Key

Set the Google Street View API key in the environment variable `GOOGLE_KEY_MY` before running the download scripts.

PowerShell example:

```powershell
$env:GOOGLE_KEY_MY = "your_api_key"
```

The submission copy does not store a real API key. The key is read in `configs.py`.

## Required inputs

This module expects the satellite-image stage to have already produced the selected satellite-image regions.

Typical upstream inputs include:
- `../download_sat/outputs/Landuse_Change_2012_2018_urbancore/`
- satellite-image identifiers and image names produced by `download_sat`

## Configuration notes

The clearer submission scripts in this folder keep their main path settings near the top of each file.
Before running them, first check values such as:
- `CITY_LIST_PATH`
- `LANDUSE_CHANGE_DIR`
- `OUTPUT_ROOT`
- `NUM_ROWS` and `NUM_COLS`

For the heavier Street View download scripts, also verify:
- `GOOGLE_KEY_MY`
- `../download_sat/outputs/Landuse_Change_2012_2018_urbancore/`
- `outputs/generated_grid_points/`
- `outputs/PANO_ID_PKL/`
- `outputs/downloaded_stv_selected/`

## Main outputs

The scripts in this folder generate files under directories such as:
- `outputs/generated_grid_points/`
- `outputs/PANO_ID_PKL/`
- `outputs/downloaded_stv_selected/`
- `outputs/final_dataset/`

These outputs are later consumed by:
- `placepulse_models`
- `generate_dataset`

## Suggested order

1. `generate_stv_points_MoreCity.py`
2. `download_GSV_years_MoreCity_pp.py`
3. `semantic-segmentation-stv.py`
4. `classify_indoor_outdoor_image.py`

## Python Files

- `configs.py`: reads the Google Street View API key from `GOOGLE_KEY_MY`.
- `generate_stv_points_MoreCity.py`: generates Street View sampling grid points for each satellite-image region.
- `download_GSV_years_MoreCity_pp.py`: reads grid-point CSVs from `outputs/generated_grid_points/`, caches pano search results under `outputs/PANO_ID_PKL/`, selects usable panoramas by year, and downloads 4 headings per selected pano into `outputs/downloaded_stv_selected/`.
- `try_download_GSV_selected_date.py`: test script for searching and downloading a Street View image near a given coordinate for a target year.
- `semantic-segmentation-stv.py`: runs semantic segmentation on Street View images and saves per-image class pixel percentages.
- `classify_indoor_outdoor_image.py`: classifies Street View images as roadside, outdoor-natural, indoor, or uncertain based on the semantic-segmentation results.

## Streetview Library Reference

This module borrows ideas from the `streetview` Python library for Street View panorama search and image download:

- [streetview](https://github.com/robolyst/streetview)


