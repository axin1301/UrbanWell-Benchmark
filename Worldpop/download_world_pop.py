import requests
import os
#https://data.worldpop.org/GIS/Population/Global_2000_2020/2012/SVN/svn_ppp_2012_UNadj.tif
#https://data.worldpop.org/GIS/Population/Global_2000_2020/2012/DEU/deu_ppp_2012_UNadj.tif
# url = "https://data.worldpop.org/GIS/Population/Global_2000_2020/2012/ALB/alb_ppp_2012_UNadj.tif"
# local_filename = "alb_ppp_2012_UNadj.tif"

europe_iso3 = [
    'IRL', 'ITA','DEU'
]

# 'ALB' 'AND', 'AUT', 'BEL', 'BIH', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK',
    # 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'HUN', 'ISL', 'IRL', 'ITA', 'LVA',
    # 'LIE', 'LTU', 'LUX', 'MLT', 'MDA', 'MCO', 'NLD', 'MKD', 'NOR', 'POL',
    # 'PRT', 'ROU', 'SMR', 'SRB', 'SVK', 'SVN', 'ESP', 'SWE', 'CHE', 'GBR'

for country in europe_iso3:
    for year in range(2014,2021):#[2020]: #[2012,2018]:
        # if year == 2012 or year == 2018:
        #     continue
        country_lower = country.lower()
        url = f"https://data.worldpop.org/GIS/Population/Global_2000_2020/{year}/{country}/{country_lower}_ppp_{year}_UNadj.tif"
        local_filename = f"outputs/worldpop_rasters/{country_lower}_ppp_{year}_UNadj.tif"
        # if os.path.exists(local_filename):
        #     continue
        print(f"requesting {year}/{country}/")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()  #
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        print("ä¸‹è½½å®Œæˆ:", local_filename)
