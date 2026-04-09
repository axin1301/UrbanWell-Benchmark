# try_GSV

## API Key

Set the Google Street View API key in the environment variable `GOOGLE_KEY_MY` before running the download scripts.

PowerShell example:

```powershell
$env:GOOGLE_KEY_MY = "your_api_key"
```

The submission copy does not store a real API key. The key is read in `configs.py`.

## Python Files

- `configs.py`: reads the Google Street View API key from `GOOGLE_KEY_MY`.
- `generate_stv_points_MoreCity.py`: generates Street View sampling grid points for each satellite-image region.
- `download_GSV_years_MoreCity_pp.py`: searches panoramas, fills missing panorama dates, and downloads Street View images and metadata for the selected years.
- `try_download_GSV_selected_date.py`: test script for searching and downloading a Street View image near a given coordinate for a target year.
- `semantic-segmentation-stv.py`: runs semantic segmentation on Street View images and saves per-image class pixel percentages.
- `classify_indoor_outdoor_image.py`: classifies Street View images as roadside, outdoor-natural, indoor, or uncertain based on the semantic-segmentation results.

## Streetview Library Reference

This module borrows ideas from the `streetview` Python library for Street View panorama search and image download:

- [streetview](https://github.com/robolyst/streetview)
