# generate_dataset

## single-year estimation

- `single_year/construct_dataset_any_indicator_single_year.py`: generates single-year dataset samples for general indicators.
- `single_year/construct_dataset_LU_single_year.py`: generates single-year dataset samples for land-use classification.
- `single_year/construct_dataset_popu_single_year.py`: generates single-year dataset samples for population estimation.
- `single_year/construct_dataset_UrbanPerception_single_year.py`: generates single-year dataset samples for urban perception estimation.
- `single_year/indicator_col_name_in_prompt.py`: maps indicator names to the prompt fields used in the single-year scripts.
- `single_year/similar_map_LU.py`: provides candidate label mapping used by the land-use script.

## multi-year forecasting

- `multi_year_type1/construct_dataset_any_indicator_multi_year_type1.py`: generates multi-year forecasting samples for general indicators.
- `multi_year_type1/construct_dataset_LU_multi_year.py`: generates multi-year forecasting samples for land-use related tasks.
- `multi_year_type1/construct_dataset_popu_multi_year_type1.py`: generates multi-year forecasting samples for population estimation.
- `multi_year_type1/indicator_col_name_in_prompt.py`: maps indicator names to the prompt fields used in the forecasting scripts.
- `multi_year_type1/similar_map_LU.py`: provides candidate label mapping used by the land-use script.

## multi-year trend analysis

- `multi_year_type3/construct_dataset_any_indicator_multi_year_type3.py`: generates multi-year trend-analysis samples for general indicators.
- `multi_year_type3/construct_dataset_popu_multi_year_type3.py`: generates multi-year trend-analysis samples for population estimation.
- `multi_year_type3/indicator_col_name_in_prompt.py`: maps indicator names to the prompt fields used in the trend-analysis scripts.

## final benchmark sampling

- `extract_final_500_dataset.py`: reads the generated dataset files, performs city-balanced sampling, and writes the final benchmark files with up to 500 samples per indicator.
