import json

import shapely
import shapely.ops

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
vnames = village_borders_shapes.keys()

### Vulnerabiliies

village_vuln_point = {
    vname: 0
    for vname in vnames
}

####### Dangerous Slope

danger_slopes_geojson_path = 'data/patrol_artificial_slope.geojson'
with open(danger_slopes_geojson_path) as danger_slopes_geojson_file:
    danger_slopes_geojson = json.load(danger_slopes_geojson_file)
# fix coordinate
for feature in danger_slopes_geojson['features']:
    feature['geometry']['coordinates'] = [
        [x, y]
        for x, y, z in feature['geometry']['coordinates']
    ]

# 第五類: 無異常徵兆
# 第四類: 有輕微徵兆
# 第三類: 有明顯徵兆
# 第二類: 有潛在危險
# 第一類: 有立即危險之虞
danger_slopes = [
    shapely.from_geojson(json.dumps(feature))
    for feature in danger_slopes_geojson['features']
    if feature['properties']['level'] != '第五類'
]
# print(danger_slopes)

danger_slope_vuln_point = {
    vname: 0
    for vname in vnames
}
for slope in danger_slopes:
    for vname in vnames:
        vborder = village_borders_shapes[vname]
        # check intersect
        if not shapely.intersects(slope, vborder):
            continue
        # split the slope line with the border of village 
        for split_line in shapely.ops.split(slope, vborder).geoms:
            if shapely.contains(vborder, split_line):
                danger_slope_vuln_point[vname] += shapely.length(split_line)
# normalization
max_vuln_pt = max(danger_slope_vuln_point.values())
min_vuln_pt = min(danger_slope_vuln_point.values())
danger_slope_vuln_point = {
    vname: (vuln_point - min_vuln_pt) / (max_vuln_pt - min_vuln_pt)
    for vname, vuln_point in danger_slope_vuln_point.items()
}

for vname in vnames:
    village_vuln_point[vname] += danger_slope_vuln_point[vname]
print(village_vuln_point)

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