# OSM_data

## Python Files

- `download_osm_data.py`: downloads raw OSM shapefile packages for the selected countries, cities, and years.
- `exclude_non_commercial_pois.py`: unzips OSM shapefiles and keeps only commercial / economic POIs.
- `diversity_of_economic_activity_any_year_MoreCity.py`: calculates economic activity diversity for each satellite-image region.
- `generate_road_access_only_dist_poi.py`: calculates POI-distance based accessibility features for each region.
- `generate_road_access_update_mp_update.py`: calculates road length, road density, POI counts, and related accessibility features for each region.
