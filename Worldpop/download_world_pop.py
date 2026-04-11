import os

import requests

# ISO3 country codes to download. Extend this list as needed.
EUROPE_ISO3 = ['IRL', 'ITA', 'DEU']
YEARS = range(2014, 2021)
OUTPUT_DIR = 'outputs/worldpop_rasters'
WORLDPOP_URL_TEMPLATE = 'https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/{country}/{country_lower}_ppp_{year}_UNadj.tif'


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for country in EUROPE_ISO3:
        for year in YEARS:
            country_lower = country.lower()
            url = WORLDPOP_URL_TEMPLATE.format(year=year, country=country, country_lower=country_lower)
            local_filename = os.path.join(OUTPUT_DIR, f'{country_lower}_ppp_{year}_UNadj.tif')
            print(f'requesting {year}/{country}/')

            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(local_filename, 'wb') as file_handle:
                    for chunk in response.iter_content(chunk_size=8192):
                        file_handle.write(chunk)

            print('downloaded:', local_filename)


if __name__ == '__main__':
    main()
