# generate_dataset

This module consumes the processed outputs from the upstream data-preparation modules and constructs the final UrbanWell benchmark datasets.

## Required inputs

Typical upstream inputs include outputs from:
- `download_sat`
- `UrbanAtlas`
- `Worldpop`
- `OSM_data`
- `extract_EEA`
- `try_GSV`
- `placepulse_models`

More concretely, the task-construction scripts read files such as:
- `../inputs/sat_stv_list_dir/<CITY_NAME>_sat_stv_list.csv`
- `../inputs/sat_stv_list_dir/<CITY_NAME>_sat_stv_list_no_stv.csv`
- `../../download_sat/outputs/valid_image_lists/valid_image_lists.csv`
- `../../Worldpop/outputs/output_popu_dir/<CITY_NAME>_ppp_<YEAR>.csv`
- `../../UrbanAtlas/outputs/output_LU_single_year/<CITY_NAME>_LU_<YEAR>.csv`
- `../../UrbanAtlas/outputs/output_LU_mix_dir/<CITY_NAME>_LU_mix_<YEAR>.csv`
- `../../extract_EEA/outputs/generated_CO2/<CITY_NAME>/<CITY_NAME>_CO2_<YEAR>.csv`
- `../../extract_EEA/outputs/generated_NO2/<CITY_NAME>/<CITY_NAME>_NO2_<YEAR>.csv`
- `../../extract_EEA/outputs/generated_PM25/<CITY_NAME>/<CITY_NAME>_PM25_<YEAR>.csv`
- `../../extract_EEA/outputs/generated_QSI/<CITY_NAME>/<CITY_NAME>_QSI_<YEAR>.csv`
- `../../extract_EEA/outputs/generated_NDVI/<CITY_NAME>/<CITY_NAME>_NDVI_<YEAR>.csv`
- `../../OSM_data/outputs/road-output/<CITY_NAME>_<YEAR>.csv`
- `../../OSM_data/outputs/accessability_output_only_POI_update/<CITY_NAME>_<YEAR>.csv`
- `../../OSM_data/outputs/output_economic_dir_update/<CITY_NAME>_economic_urbancore_<YEAR>.csv`
- `../../placepulse_models/outputs/output_stv_selected/`
- `../inputs/generated_QA/all_cities_yearly_sat_scores.csv`

## Main outputs

The scripts in this folder generate benchmark-construction outputs under:
- `outputs/single_year/`
- `outputs/multi_year_type1/`
- `outputs/multi_year_type3/`
- `outputs/final_benchmark/`

The final released benchmark JSON files are then collected into:
- `benchmark_dataset/`

## Suggested order

1. prepare the correspondence files under `inputs/sat_stv_list_dir/`
2. run the single-year scripts under `single_year/`
3. run the forecasting scripts under `multi_year_type1/`
4. run the trend-analysis scripts under `multi_year_type3/`
5. run `extract_final_500_dataset.py` to sample the released benchmark files

## single-year estimation

- `single_year/construct_dataset_any_indicator_single_year.py`: generates single-year dataset samples for general indicators such as CO2, NO2, PM2.5, NDVI, accessibility, road, and economic-diversity metrics.
- `single_year/construct_dataset_LU_single_year.py`: generates single-year dataset samples for land-use classification.
- `single_year/construct_dataset_popu_single_year.py`: generates single-year dataset samples for population estimation.
- `single_year/construct_dataset_UrbanPerception_single_year.py`: generates single-year dataset samples for urban perception estimation using the outputs from `placepulse_models`.
- `single_year/indicator_col_name_in_prompt.py`: maps indicator names to the prompt fields used in the single-year scripts.
- `single_year/similar_map_LU.py`: provides candidate label mapping used by the land-use script.

Output layout:
- `outputs/single_year/<CITY_NAME>/...json`

## multi-year forecasting

- `multi_year_type1/construct_dataset_any_indicator_multi_year_type1.py`: generates multi-year forecasting samples for general indicators.
- `multi_year_type1/construct_dataset_LU_multi_year.py`: generates multi-year forecasting samples for land-use related tasks.
- `multi_year_type1/construct_dataset_popu_multi_year_type1.py`: generates multi-year forecasting samples for population estimation.
- `multi_year_type1/indicator_col_name_in_prompt.py`: maps indicator names to the prompt fields used in the forecasting scripts.
- `multi_year_type1/similar_map_LU.py`: provides candidate label mapping used by the land-use script.

Output layout:
- `outputs/multi_year_type1/<CITY_NAME>/...json`
- helper subsets with names like `*_single_year_selected_type1_*.json`

## multi-year trend analysis

- `multi_year_type3/construct_dataset_any_indicator_multi_year_type3.py`: generates multi-year trend-analysis samples for general indicators.
- `multi_year_type3/construct_dataset_popu_multi_year_type3.py`: generates multi-year trend-analysis samples for population estimation.
- `multi_year_type3/indicator_col_name_in_prompt.py`: maps indicator names to the prompt fields used in the trend-analysis scripts.

Output layout:
- `outputs/multi_year_type3/<CITY_NAME>/...json`
- helper subsets with names like `*_single_year_selected_type3_*.json`

## final benchmark sampling

- `extract_final_500_dataset.py`: scans the generated JSON files, groups them by indicator and task type, performs balanced sampling, and writes the final benchmark release files.

Output layout:
- `outputs/final_benchmark/`
