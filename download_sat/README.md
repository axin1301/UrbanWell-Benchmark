# download_sat

## Google Earth Downloader

This module uses `downloader.exe`, which refers to the Google Earth Images Downloader tool from AllMapSoft:
[https://www.allmapsoft.com/geid/](https://www.allmapsoft.com/geid/)

Install the tool from the website above and make sure `downloader.exe` is available in your runtime environment when running the download script.

## Files

- `download_sat_image_any_year_zoom_16_MoreCity.py`: downloads satellite images for each city and year.
- `filter_sat_images_in_boundary.py`: filters downloaded satellite images to keep those inside the target city boundary.
- `image_intersect_polygon_MoreCity.py`: matches downloaded satellite image footprints with UrbanAtlas land-use-change polygons.
