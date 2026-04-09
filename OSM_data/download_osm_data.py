import requests
import pandas as pd
import os

country_csv = pd.read_csv('../UrbanAtlas/European_Countries_VS_Cities.csv')
# country_code,country_name,city_name,city_full_name,province

failed_countries = []
csize = 32* 1024 * 1024  # 4 MB
for i in range(len(country_csv)):
    country_name = country_csv.at[i,'country_name']
    country_code = country_csv.at[i,'country_code'].upper()
    city_full_name = country_csv.at[i,'city_full_name']
    province = country_csv.at[i,'province']
    note = country_csv.at[i,'note']
    
    # for year in [2022]:
    for year in [2014,2015,2016,2017,2019,2020,2021,2024]:
        year_str = str(year - 2000 + 1) + '0101'

        url_list = [
            f"https://download.geofabrik.de/europe/{country_name}/{city_full_name}-{year_str}-free.shp.zip",
            f"https://download.geofabrik.de/europe/{country_name}/{province.lower()}-{year_str}-free.shp.zip",
            f"https://download.geofabrik.de/europe/{country_name}-{year_str}-free.shp.zip",
            f"https://download.geofabrik.de/europe/{country_name}/{note}-{year_str}-free.shp.zip"
        ]
        # https://download.geofabrik.de/europe/netherlands/noord-holland-230101-free.shp.zip
        downloaded = False
        for url in url_list:
            local_filename = f"outputs/osm_raw_data/{os.path.basename(url)}"
            try:
                os.makedirs(os.path.dirname(local_filename), exist_ok=True)
                
                with requests.get(url, stream=True, timeout=30) as r:
                    if r.status_code == 200:
                        if os.path.exists(f"outputs/osm_raw_data/{os.path.basename(url)}"):
                            downloaded = True
                            break
                        with open(local_filename, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=csize):
                                f.write(chunk)
                        print("done ", local_filename)
                        downloaded = True
                        break  #
                    else:
                        print(f"URL {url} {r.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"erro {url} {e}")
        
        if not downloaded:
            failed_countries.append((year, country_name))

print(set(failed_countries))
# https://download.geofabrik.de/europe/greece-220101-free.shp.zip  # 
# https://download.geofabrik.de/europe/germany/berlin-230101-free.shp.zip # 
# https://download.geofabrik.de/europe/netherlands-230101.osm.pbf
# https://download.geofabrik.de/europe/netherlands/noord-holland-230101-free.shp.zip


#  
# https://download.geofabrik.de/europe/united-kingdom/england/greater-london.html#
# https://download.geofabrik.de/europe/bosnia-herzegovina-250101-free.shp.zip
# https://download.geofabrik.de/europe/czech-republic-250101-free.shp.zip
# https://download.geofabrik.de/europe/italy/centro-250101-free.shp.zip
# https://download.geofabrik.de/europe/macedonia-250101-free.shp.zip
# https://download.geofabrik.de/europe/ireland-and-northern-ireland-250101-free.shp.zip
# https://download.geofabrik.de/europe/poland/mazowieckie-250101-free.shp.zip
# https://download.geofabrik.de/europe/united-kingdom/england/greater-london-250101-free.shp.zip

## --------------------------------------------------------------------------------