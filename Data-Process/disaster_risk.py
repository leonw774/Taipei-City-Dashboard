import json

import tqdm
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
for vname in tqdm(vnames):
    vborder = village_borders_shapes[vname]
    for slope in danger_slopes:
        # check intersect
        if not shapely.intersects(slope, vborder):
            continue
        # split the slope line with the border of village 
        for split_line in shapely.ops.split(slope, vborder).geoms:
            if shapely.contains(vborder, split_line):
                danger_slope_vuln_point[vname] += shapely.length(split_line)
                break
# normalization
max_vuln_pt = max(danger_slope_vuln_point.values())
min_vuln_pt = min(danger_slope_vuln_point.values())
danger_slope_vuln_point = {
    vname: (vuln_point - min_vuln_pt) / (max_vuln_pt - min_vuln_pt)
    for vname, vuln_point in danger_slope_vuln_point.items()
}

###### Old House




###### Liquefaction

liquefaction_geojson_path = 'data/work_soil_liquefaction.geojson'
with open(liquefaction_geojson_path) as liquefaction_geojson_file:
    liquefaction_geojson = json.load(liquefaction_geojson_file)
liquefaction_polygon_class = {
    shapely.from_geojson(json.dumps(feature)): feature['properties']['class']
    for feature in liquefaction_geojson['features']
}

liquefaction_vuln_point = {
    vname: 0
    for vname in vnames
}
for vname in tqdm(vnames):
    vborder = village_borders_shapes[vname]
    vborder_area = shapely.area(vborder)
    for polygon, cls in liquefaction_polygon_class.items():
        if not shapely.intersects(vborder, polygon):
            continue
        intersection_area = shapely.area(
            shapely.intersection(vborder, polygon)
        )
        
        if cls == '高':
            weight = 3
        elif cls == '中':
            weight = 2
        elif cls == '低':
            weight = 1
        else:
            ValueError()
        liquefaction_vuln_point[vname] += (
            weight * intersection_area / vborder_area
        )
max_vuln_pt = max(liquefaction_vuln_point.values())
min_vuln_pt = min(liquefaction_vuln_point.values())
liquefaction_vuln_point = {
    vname: (vuln_point - min_vuln_pt) / (max_vuln_pt - min_vuln_pt)
    for vname, vuln_point in liquefaction_vuln_point.items()
}

### Weighted sum

for vname in vnames:
    village_vuln_point[vname] = (
        danger_slope_vuln_point[vname]
        # + old_house_vuln_point[vname]
        + liquefaction_vuln_point[vname]
    )