import json

import shapely

from utils import *

### Get village borders

village_borders_geojson_path = (
    '../Taipei-City-Dashboard-FE/public/mapData/taipei_village.geojson'
)
with open(village_borders_geojson_path) as village_borders_geojson_file:
    village_borders_geojson = json.load(village_borders_geojson_file)

village_borders_shapes = {
    feature['properties']['VNAME']: shapely.from_geojson(json.dumps(feature))
    for feature in village_borders_geojson['features']
}
# print(village_borders_shapes)

### Vulnerabiliies

####### Dangerous Slope

dangerous_slopes_geojson_path = 'data/patrol_artificial_slope.geojson'
with open(dangerous_slopes_geojson_path) as dangerous_slopes_geojson_file:
    dangerous_slopes_geojson = json.load(dangerous_slopes_geojson_file)


###### Old House
from shapely.geometry import Point, MultiPolygon

from shapely.geometry import shape

# 定義坐標點
point = Point(121.5055892, 25.1442078)

old_house_geojson_path = (
    '../Data-Process/data/building_age.geojson'
)
with open(old_house_geojson_path) as old_house_geojson_file:
    old_house_geojson = json.load(old_house_geojson_file)

# old_house_points = {
# 	shapely.from_geojson(json.dumps(feature))
#     for feature in old_house_geojson['features']
#     if feature['properties']['age_2021'] < 20
# }

# print(old_house_points)

filtered_features = [
    feature
    for feature in old_house_geojson["features"]
    if feature["properties"]["age_2021"] < 20 and feature["geometry"]is not None
]
# print(old_house_geojson["features"][0])
print(filtered_features)


# village_borders_shapes = {
#     feature['properties']['coordinates']: shapely.from_geojson(json.dumps(feature))
#     for feature in village_borders_geojson['features']
# }

# 過濾age_2021小於20的點位





# 
# for village, shape in village_borders_shapes.items():
#     if point.within(shape):
#         print(f"該點位於 {village}")
#     else:
#         print(f"該點不在 {village}")




###### Liquefaction