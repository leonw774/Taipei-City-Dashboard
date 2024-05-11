import json
from multiprocessing import Pool, current_process

from tqdm import tqdm
import shapely
import shapely.ops

from utils import *

def get_vuln_points(arg_dict):
    village_borders_shapes = arg_dict['village_borders_shapes']
    old_house_points = arg_dict['old_house_points']
    local_vuln_point = {
        vname: 0
        for vname in village_borders_shapes
    }
    for old_house in tqdm(
            old_house_points,
            ncols=100,
            position=(current_process()._identity[0]),
            leave=False):
        for vname, vborder in village_borders_shapes.items():
            # check contains
            if shapely.contains(vborder, old_house):
                local_vuln_point[vname] += 1
                break
    
    return local_vuln_point

if __name__ == '__main__':
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

    for feature in village_borders_geojson['features']:
        feature['properties'] = {
            'VNAME': feature['properties']['VNAME']
        }

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

    danger_slope_vuln_point = {
        vname: 0
        for vname in vnames
    }
    for vname in tqdm(vnames, ncols=100):
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

    old_house_geojson_path = (
        '../Data-Process/data/building_age.geojson'
    )
    with open(old_house_geojson_path) as old_house_geojson_file:
        old_house_geojson = json.load(old_house_geojson_file)

    old_house_points = [
        shapely.from_geojson(json.dumps(feature))
        for feature in old_house_geojson["features"]
        if feature["properties"]["age_2021"] > 20 and feature["geometry"] is not None
    ]

    # for test
    # old_house_points = old_house_points[:10000]

    old_house_vuln_point = {
        vname: 0
        for vname in vnames
    }
    with Pool(8) as p:
        chunk_length = len(old_house_points) // 8
        old_house_points_chunks = [
            old_house_points[i:i+chunk_length]
            for i in range(0, len(old_house_points), chunk_length)
        ]
        args_dict_list = [
            {
                'village_borders_shapes': village_borders_shapes,
                'old_house_points': chunk
            }
            for chunk in old_house_points_chunks
        ]
        chunks_vuln_points = list(
            p.imap_unordered(get_vuln_points, args_dict_list)
        )
        # print(chunks_vuln_points)
    for chunk_vuln_point in chunks_vuln_points:
        for vname in vnames:
            old_house_vuln_point[vname] += chunk_vuln_point[vname]
    # normalization
    max_vuln_pt = max(old_house_vuln_point.values())
    min_vuln_pt = min(old_house_vuln_point.values())
    old_house_vuln_point = {
        vname: (vuln_point - min_vuln_pt) / (max_vuln_pt - min_vuln_pt)
        for vname, vuln_point in old_house_vuln_point.items()
    }
  
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
    for vname in tqdm(vnames, ncols=100):
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
            + old_house_vuln_point[vname]
            + liquefaction_vuln_point[vname]
        ) / 3

    print('Vulnerability')
    print(village_vuln_point)

    # Population density

    village_pop_csv_path = 'data/111_villages_populations.csv'
    with open(village_pop_csv_path) as village_pop_csv_file:
        # we only want total population for each vil.
        village_pop_lines = village_pop_csv_file.readlines()[4::3]
        # we only want the 3rd and 5th column: name and total population
        village_pop_lines_splited = [
            line.split(',', maxsplit=6)
            for line in village_pop_lines
        ]
    village_pop = dict([
        (line_splits[3], int(line_splits[5]))
        for line_splits in village_pop_lines_splited
    ])
    village_pop['糖蔀里'] = village_pop['糖?里']
    # print(village_pop)

    # directly read from front end geojson
    taipei_village_geojson_path = (
        '../Taipei-City-Dashboard-FE/public/mapData/'
        'taipei_village.geojson'
    )
    with open(taipei_village_geojson_path, 'r') as taipei_village_geojson_file:
        taipei_village_geojson = json.load(taipei_village_geojson_file)
    village_area = {
        feature['properties']['VNAME']: (
            feature['properties']['AREA'] / 1_000_000 # from m^2 to km^2
        )
        for feature in taipei_village_geojson['features']
    }
    # calculate the polulation density
    village_pop_density = {
        vname: round(village_pop[vname] / village_area[vname], 2)
        for vname in vnames
    }
    # normalization
    village_pop_density_index = {
        vname: village_pop_density[vname] / max(village_pop_density.values())
        for vname in vnames
    }
    print(village_pop_density_index) 

    # Calculate risk index



    # Set Manager DB

    manager_engine = get_manager_engine()
