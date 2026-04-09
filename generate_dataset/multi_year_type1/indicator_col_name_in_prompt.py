import os

indicator_name_dict = {
    'network_density_km_per_km2':'driving road length density in the region in the unit of kilometer per square kilometer',
    'intersection_density_per_km2':'road endpoint density per square kilometer',
    'road_length':'driving road length in kilometer',
    'avg_dist_to_restaurant':'minumum distance (kilometer) from the center of region to the nearest restaurant in urban area',
    'avg_dist_to_hotel':'minimum distance (kilometer) from the center of region to the nearest hotel in urban area',
    'avg_dist_to_convenience':'minimum distance (kilometer) from the center of region to the nearest convenience store in urban area',
    'avg_dist_to_supermarket':'minimum distance (kilometer) from the center of region to the nearest supermarket in urban area',
    'avg_dist_to_hospital':'minimum distance (kilometer) from the center of region to the nearest hospital in urban area',
    'CO2':'fossil fuel carbon dioxide emission in the unit of **tonne carbon (monthly total)** in July',
    'NO2':'annual mean nitrogen dioxide concentration (in micrograms per cubic meter) based on the based on the European Environment Agency (EEA) air quality dataset',
    'NDVI':'Normalised Difference Vegetation Index (NDVI) in July',
    'PM25':'annual average concentration of fine particulate matter (PM2.5) in micrograms per cubic meter based on the European Environment Agency (EEA) air quality dataset',
    'QSI':'Quietness Suitability Index (QSI) value (in the range of 0 - 1000 that indicates how suitable an area is to be considered quiet, with higher values meaning quieter areas) according to the potential quiet areas in EU',
    'landuse_mix':'diversity index of land use mix',
    'economic': 'diversity index of economic activity',
    'safety': 'safety value',
    'lively' : 'livelyness value',
    'wealthy': 'wealth value',
    'beautiful': 'beauty value',
    'boring': 'boredom value',
    'depressing': 'depression value'
}

col_name_dict = {
    'CO2':'CO2_mean',
    'NO2':'NO2_value',
    'NDVI':'NDVI_mean',
    'PM25':'PM25_value',
    'QSI':'mean_QSI',
}

add_info_indicator = {
    'landuse_mix':'The diversity of land use mix is calculated as the normalized Shannon index (from 0 to 1) based merely on the distribution of the following land use categories: (1) residential; (2) commercial/industrial/institutional/governmental; and (3) recreational/parks/water.',

    'economic':'The diversity of economic activity is calculated as the Shannon entropy of commercial POI numbers (including restaurant, fast_food, cafe, bar, pub, supermarket, convenience, mall, clothes, shoes, electronics, jeweller, bakery, butcher, florist, bookshop, hairdresser, beauty_shop, laundry, repair, photo, travel_agent, car_rental, car_wash, hotel, motel, guesthouse, hostel, camp_site, cinema, theatre, museum, gallery, nightclub, casino, sports_centre, fitness_centre.)',

    'NDVI':'NDVI is from -1 to 1, with higher value indicationg higher vegetation.',

    'safety':"PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images to judge perceptions of urban environments. It defines six perceptual dimensions: safe, lively, beautiful, wealthy, boring, and depressing. Each image receives a perceptual score derived from these pairwise comparisons, typically normalized to represent how strongly the place is perceived along that dimension. When referring to the safety value, interpret it strictly in this PlacePulse 2.0 sense - that is, as the perceived degree of safety for the given region - based on visual cues such as greenery, building condition, openness, street activity, lighting, and upkeep.",
    
    'lively':"PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images to judge perceptions of urban environments. It defines six perceptual dimensions: safe, lively, beautiful, wealthy, boring, and depressing. Each image receives a perceptual score derived from these pairwise comparisons, typically normalized to represent how strongly the place is perceived along that dimension. When referring to the lively value, interpret it strictly in this PlacePulse 2.0 sense - that is, as the perceived degree of lively for the given region - based on visual cues such as greenery, building condition, openness, street activity, lighting, and upkeep.",
    
    'wealthy':"PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images to judge perceptions of urban environments. It defines six perceptual dimensions: safe, lively, beautiful, wealthy, boring, and depressing. Each image receives a perceptual score derived from these pairwise comparisons, typically normalized to represent how strongly the place is perceived along that dimension. When referring to the wealthy value, interpret it strictly in this PlacePulse 2.0 sense - that is, as the perceived degree of wealthy for the given region - based on visual cues such as greenery, building condition, openness, street activity, lighting, and upkeep.",
    
    'beautiful':"PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images to judge perceptions of urban environments. It defines six perceptual dimensions: safe, lively, beautiful, wealthy, boring, and depressing. Each image receives a perceptual score derived from these pairwise comparisons, typically normalized to represent how strongly the place is perceived along that dimension. When referring to the beautiful value, interpret it strictly in this PlacePulse 2.0 sense - that is, as the perceived degree of beautiful for the given region - based on visual cues such as greenery, building condition, openness, street activity, lighting, and upkeep.",
    
    'boring':"PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images to judge perceptions of urban environments. It defines six perceptual dimensions: safe, lively, beautiful, wealthy, boring, and depressing. Each image receives a perceptual score derived from these pairwise comparisons, typically normalized to represent how strongly the place is perceived along that dimension. When referring to the boring value, interpret it strictly in this PlacePulse 2.0 sense - that is, as the perceived degree of boring for the given region - based on visual cues such as greenery, building condition, openness, street activity, lighting, and upkeep.",
    
    'depressing':"PlacePulse 2.0 is a large-scale crowdsourced dataset where people compared pairs of street view images to judge perceptions of urban environments. It defines six perceptual dimensions: safe, lively, beautiful, wealthy, boring, and depressing. Each image receives a perceptual score derived from these pairwise comparisons, typically normalized to represent how strongly the place is perceived along that dimension. When referring to the depressing value, interpret it strictly in this PlacePulse 2.0 sense - that is, as the perceived degree of depressing for the given region - based on visual cues such as greenery, building condition, openness, street activity, lighting, and upkeep."                        
}


