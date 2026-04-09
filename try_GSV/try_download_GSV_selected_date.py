import datetime

import streetview

from configs import *


Maps_API_KEY = GOOGLE_KEY_MY


def find_and_download_image_by_year(lat, lon, target_year):
    """Search for a Street View panorama near a coordinate and download one from the target year."""
    print(f"Searching for a Street View image near {lat}, {lon} for year {target_year}...")

    try:
        panos = streetview.search_panoramas(lat=lat, lon=lon)
    except Exception as e:
        print(f"Error while searching panoramas: {e}")
        return 0

    found_pano = None
    for pano in panos:
        print(pano)
        if pano.date and pano.date.startswith(str(target_year)):
            found_pano = pano
            break

    if not found_pano:
        print(f"No Street View image was found for year {target_year} near the target location.")
        return 0

    print(
        f"Found a Street View image from {target_year}. "
        f"Capture date: {found_pano.date}, pano ID: {found_pano.pano_id}"
    )

    formatted_lat = f"{lat:.6f}"
    formatted_lon = f"{lon:.6f}"
    file_name = (
        f"street_view_{formatted_lat}_{formatted_lon}_{found_pano.lat}_{found_pano.lon}_"
        f"{target_year}_{found_pano.date}_{found_pano.pano_id}_180.jpg"
    )

    response = streetview.get_streetview(
        pano_id=found_pano.pano_id,
        heading=0,
        fov=180,
        pitch=0,
        api_key=Maps_API_KEY,
    )
    response.save(file_name, "jpeg")
    print(f"Saved image to {file_name}")
    return 1


if __name__ == "__main__":
    year = 2022
    target_date_str = f"{year}-07-31"

    try:
        target_year = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").year
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        raise SystemExit(1)

    latitude = 60.272495
    longitude = 24.961462
    find_and_download_image_by_year(latitude, longitude, target_year)
