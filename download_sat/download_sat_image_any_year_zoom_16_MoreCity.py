import pandas as pd
import os
import subprocess
from func_timeout import func_set_timeout
import concurrent.futures
import requests
import time
import threading
import shutil

semaphore = threading.Semaphore(10)

# @func_set_timeout(60)
def task(city_name, ll, rl, tl, bl, date):
    with semaphore:
        python_exe_path = "downloader.exe"
        py_file_path = f"{city_name} {zoom_level} {zoom_level} {ll} {rl} {tl} {bl} outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date} {date}"
        cmd_command = f"{python_exe_path} {py_file_path}"

        print(f"Running command: {cmd_command}")
        run_cmd_process = subprocess.Popen(cmd_command, shell=True)#, env=env)
        run_cmd_process.wait()

def run_tasks_for_city(year,row_num,city_name):
    try:
        # city_bound_one = city_bound[city_bound['city_name'] == one_city]
        city_bound_one = city_bound.iloc[row_num]

        left_longitude = city_bound_one['min_lon']
        right_longitude = city_bound_one['max_lon']
        top_latitude = city_bound_one['max_lat']
        bottom_latitude = city_bound_one['min_lat']
        area_identifier = city_bound_one['identifier']

        # for year in range(2016, 2017):
        year_str = str(year)
        date = f"{year_str}-07-31"

        if not os.path.exists(f'outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}'):
            os.makedirs(f'outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}')
        print(f"Running task for {city_name} on {date}")

        print(f"Parameters: {city_name}, {str(left_longitude)}, {str(right_longitude)}, {str(top_latitude)}, {str(bottom_latitude)}, {date}")
        task(city_name, str(left_longitude), str(right_longitude), str(top_latitude), str(bottom_latitude), date)
        
        #########################list_file
        source_file = f'outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}'+ '/'+city_name+'_list1.txt'
        destination_directory = f'outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}'+'/'+ city_name + '/img_info/'
        new_file_name = area_identifier+ "_list1.txt"
        destination_file = os.path.join(destination_directory, new_file_name)
        os.makedirs(destination_directory, exist_ok=True)
        shutil.copy(source_file, destination_file)

    #########################log file
        source_file = f'outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}'+ '/'+city_name+'_log.txt'
        destination_directory = f'outputs/downloaded_sat_{year}_zoom_{zoom_level}\\{city_name}\\{date}'+'/'+ city_name + '/img_info/' 
        new_file_name = area_identifier+ "_log.txt"
        destination_file = os.path.join(destination_directory, new_file_name)
        os.makedirs(destination_directory, exist_ok=True)   
        shutil.copy(source_file, destination_file)
        print(f"{destination_file} saved ")

    except Exception as e:
        print(f"Exception occurred while processing {city_name}: {e}")

if __name__ == "__main__":
    start_time = time.time()

    global zoom_level

    zoom_level = 16
    
    city_list = list(pd.read_csv('../UrbanAtlas/City_list.csv')['city_name'])

    for city_name in city_list:
        global city_bound
        city_bound = pd.read_csv(f"../UrbanAtlas/outputs/urbancore_bbox_dir/{city_name}_urbancore_bbox.csv")
        city_bound.at[0,'identifier'] = city_name
        print(city_bound)

        for year in range(2012,2025):#[2016]: #[2024]: #[2015, 2020]:#[2019]:#[2012,2019,2022,2014,2017,2021,2023]:#[2018]:
        # year = 2012
        # row_num = 15
            for row_num in [0]: #range(21,25):
                city_name = city_bound.at[row_num,'identifier']
                run_tasks_for_city(year,row_num,city_name)
                time.sleep(10)

    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_time_hours = elapsed_time / 3600
    print('elapsed_time_hours: ',elapsed_time_hours)



