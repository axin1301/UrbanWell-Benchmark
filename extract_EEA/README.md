# extract_EEA

Download the raw environmental datasets into `outputs/eea_raw_data/` before running the scripts in this folder.

## Python Files

- `extract_CO2_1km.py`: extracts CO2 values for each satellite-image region.
- `extract_NDVI.py`: extracts NDVI values for each satellite-image region.
- `extract_NO2.py`: extracts NO2 values for each satellite-image region.
- `extract_PM25.py`: extracts PM2.5 values for each satellite-image region.
- `extract_quite_area.py`: extracts quiet-area / QSI values for each satellite-image region.
- `generate_NDVI_Copernicus.py`: generates the bbox / boundary file used for NDVI extraction.
