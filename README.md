# Code For UrbanWell

This directory contains the code files prepared for constructing the UrbanWell dataset, grouped by module:

- `UrbanAtlas`:
prepare Urban Atlas based inputs, including satellite-image boundaries, land-use data, land-use change data, and land-use mix.
- `download_sat`:
download satellite imagery and organize the image metadata used by the later modules.
- `Worldpop`:
download WorldPop population raster files and generate population values for each satellite-image region.
- `try_GSV`:
generate Street View sampling points, download Street View images, and prepare Street View metadata.
- `placepulse_models`:
use pretrained models to generate urban perception scores from Street View images.
- `OSM_data`:
download OSM raw data and generate accessibility and economic activity related indicators.
- `extract_EEA`:
download environmental raw data and generate CO2, NDVI, NO2, PM2.5, and quiet-area related indicators.
- `generate_dataset`:
construct the final benchmark datasets for single-year estimation, multi-year forecasting, and multi-year trend analysis.

## Workflow

```mermaid
flowchart TD
    A[UrbanAtlas\nPrepare urban-core bbox, land-use, land-use change, land-use mix] --> B[download_sat\nDownload satellite images and organize image metadata]
    A --> C[Worldpop\nExtract population for each satellite-image region]
    B --> D[try_GSV\nGenerate Street View points and download Street View images]
    B --> E[OSM_data\nGenerate OSM-based indicators]
    B --> F[extract_EEA\nGenerate environmental indicators]
    D --> G[placepulse_models\nGenerate urban perception scores]
    B --> H[generate_dataset\nSingle-year estimation]
    C --> H
    E --> H
    F --> H
    G --> H
    A --> H
    H --> I[generate_dataset\nMulti-year forecasting]
    H --> J[generate_dataset\nMulti-year trend analysis]
```

## Recommended Order

1. Run `UrbanAtlas` to prepare urban boundaries, land-use, land-use change, and land-use mix.
2. Run `download_sat` to download satellite images and organize the image metadata.
3. Run `Worldpop`, `OSM_data`, and `extract_EEA` to generate satellite-region level indicators.
4. Run `try_GSV` to generate Street View points and download Street View images.
5. Run `placepulse_models` to generate urban perception scores from the Street View images.
6. Run `generate_dataset` to build:
   `single-year estimation`, `multi-year forecasting`, and `multi-year trend analysis` benchmarks.

## Notes

1. API keys have been removed from the submission copy.
   Scripts under `try_GSV` read the Google Street View API key from the `GOOGLE_KEY_MY` environment variable.

   Example:

   ```
   GOOGLE_KEY_MY = "your_google_api_key"
   ```

2. This submission folder keeps only the current processing scripts and simplified README files for each module.

3. The code in `generate_dataset` organizes the final tasks into:
   `single-year estimation`, `multi-year forecasting`, and `multi-year trend analysis`.

4. `benchmark_dataset` contains the final benchmark data.