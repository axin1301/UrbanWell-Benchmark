# placepulse_models

This module runs pretrained urban-perception models on the selected Street View images and exports region-level perception scores used by the final benchmark.

## Required inputs

Typical upstream inputs include:
- selected Street View images under `../try_GSV/outputs/downloaded_stv_selected/`
- satellite-region identifiers from `../download_sat/outputs/Landuse_Change_2012_2018_urbancore/`
- city list file `../UrbanAtlas/City_list.csv`
- pretrained model files placed under `pretrained_weights/`

## Main outputs

The scoring script generates one CSV file per region and perception attribute under:
- `outputs/output_stv_selected/`

These outputs are later consumed by:
- `generate_dataset`

## Suggested order

1. download or prepare the Street View images in `../try_GSV/outputs/downloaded_stv_selected/`
2. place the pretrained model files in `pretrained_weights/`
3. run `eval_two_years_MoreCity_pp.py`

## Python Files

- `eval_two_years_MoreCity_pp.py`: loads the pretrained model, reads the selected Street View image folders, and writes per-attribute urban-perception scores.

## Other Files

- `requirements.txt`: Python dependencies for running the perception scoring script.
- `pretrained_weights/README.md`: placeholder directory for pretrained model checkpoints.
