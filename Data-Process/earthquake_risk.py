from copy import deepcopy
import json
import os
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
    v_start = round(current_process()._identity[0] / 8 * len(village_borders_shapes))
    v_items = list(village_borders_shapes.items())
    v_items = v_items[v_start:] + v_items[:v_start]
    for old_house in tqdm(
            old_house_points,
            ncols=100,
            position=(current_process()._identity[0]),
            leave=False):
        for vname, vborder in list(village_borders_shapes.items()):
            # check contains
            if shapely.contains(vborder, old_house):
                local_vuln_point[vname] += 1
                break
    
    return local_vuln_point

def normalize_dict_value(counter):
    max_val = max(counter.values())
    min_val = min(counter.values())
    return {
        k: round((v - min_val) / (max_val - min_val), 3)
        for k, v in counter.items()
    }

if __name__ == '__main__':
    ### Get village borders

    village_borders_geojson_path = (
        '../Taipei-City-Dashboard-FE/public/mapData/taipei_village.geojson'
    )
    with open(village_borders_geojson_path, 'r') as village_borders_geojson_file:
        village_borders_geojson = json.load(village_borders_geojson_file)

    village_borders_shapes = {
        feature['properties']['VNAME']: shapely.from_geojson(json.dumps(feature))
        for feature in village_borders_geojson['features']
    }
    vnames = list(village_borders_shapes.keys())
    village_base_geojson = village_borders_geojson
    for feature in village_base_geojson['features']:
        feature['properties'] = {
            'VNAME': feature['properties']['VNAME']
        }

    ### Vulnerabiliies

    village_vuln_geojson_filename = 'taipei_village_vulnerability'
    village_vuln_geojson_path = (
        '../Taipei-City-Dashboard-FE/public/mapData/'
        + village_vuln_geojson_filename
        + '.geojson'
    )
    if os.path.exists(village_vuln_geojson_path):
        with open(village_vuln_geojson_path) as f:
            village_vuln_geojson = json.load(f)
            village_vuln_point = {
                feature['properties']['VNAME']: feature['properties']['vulnerability']
                for feature in village_vuln_geojson['features']
            }
    else:
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
        danger_slope_vuln_point = normalize_dict_value(danger_slope_vuln_point)

        ###### Old House

        old_house_geojson_path = (
            'data/building_age.geojson'
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
        old_house_vuln_point = normalize_dict_value(old_house_vuln_point)
    
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
        for vname in vnames:
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
        liquefaction_vuln_point = normalize_dict_value(liquefaction_vuln_point)

        ### Combine into vulnerability

        village_vuln_point = {
            vname: (danger_slope_vuln_point[vname]
                + old_house_vuln_point[vname]
                + liquefaction_vuln_point[vname]
            )
            for vname in vnames
        }
        village_vuln_point = normalize_dict_value(village_vuln_point)
        
        # save to geojson in front end
        village_vuln_geojson = deepcopy(village_base_geojson)
        for feature in village_vuln_geojson['features']:
            vname = feature['properties']['VNAME']
            feature['properties']['vulnerability'] = village_vuln_point[vname]
        with open(village_vuln_geojson_path, 'w') as f:
            json.dump(village_vuln_geojson, f)

    ### Population density

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

    # directly read from front end geojson
    taipei_village_geojson_path = (
        '../Taipei-City-Dashboard-FE/public/mapData/'
        'taipei_village.geojson'
    )
    with open(taipei_village_geojson_path) as taipei_village_geojson_file:
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
    # print(village_pop_density_index)

    ### Risk index

    quake_intensity_weight = [
        ('4級', 0),
        ('5弱', 1/6),
        ('5強', 1/3),
        ('6弱', 1/2),
        ('6強', 2/3),
        ('7級', 5/6),
    ]
    village_risk_indices = {
        intensity: {
            vname: (village_pop_density_index[vname]
                + village_vuln_point[vname]
                + weight
            ) / 3
            for vname in vnames
        }
        for intensity, weight in quake_intensity_weight
    }

    # save to geojson in front end
    village_risk_index_geojson_filename = 'taipei_village_earthquake_risk_index'
    village_risk_index_geojson_path = (
        '../Taipei-City-Dashboard-FE/public/mapData/'
        + village_risk_index_geojson_filename
        + '.geojson'
    )
    village_risk_index_geojson = deepcopy(village_base_geojson)
    for feature in village_risk_index_geojson['features']:
        vname = feature['properties']['VNAME']
        for intensity, _weight in quake_intensity_weight:
            feature['properties'][intensity] = round(
                village_risk_indices[intensity][vname],
                5
            )
    with open(village_risk_index_geojson_path, 'w') as f:
        json.dump(village_risk_index_geojson, f)

    # Init data table

    village_risk_index_table_name = 'village_earthquake_risk_index'
    csv_buffer = 'vname,' + ','.join([
        f'intensity_{intensity}'
        for intensity, _ in quake_intensity_weight
    ]) + '\n'
    for vname in vnames:
        csv_buffer += ','.join([vname] + [
            str(village_risk_indices[intensity][vname])
            for intensity, _ in quake_intensity_weight
        ]) + '\n'
    init_data_table_with_csv_buffer(
        csv_buffer.encode(),
        village_risk_index_table_name,
        on_conflict_do='update',
        constraint_fields=['vname']
    )

    # Set Manager DB
    manager_engine = get_manager_engine()

    vuln_component_id = 77
    vuln_component_index = 'village_vulnerability_index'
    vuln_query_chart = f"""
        SELECT '低' AS name, 'fill' AS type
        UNION ALL
        SELECT '中' AS name, 'fill' AS type
        UNION ALL
        SELECT '高' AS name, 'fill' AS type
    """.strip()
    vuln_fill_color_stops = [
        [0,   '#dddddd'],
        [0.5, '#7777ee'],
        [1,   '#0000ff'],
    ]
    with manager_engine.connect() as conn:
        ComponentManager(
            id=vuln_component_id,
            index=vuln_component_index,
            name='房屋與地質災害潛勢指數',
            query_type='map_legend',
            query_chart=vuln_query_chart,
            map_config_ids=[vuln_component_id],
            time_from='static',
        ).insert(conn, on_conflict_do='update')

        ComponentChartConfig(
            index=vuln_component_index,
            types=['MapLegend'],
            color=[c for _v, c in vuln_fill_color_stops],
            unit='指數'
        ).insert(conn, on_conflict_do='update')

        MapConfig(
            id=vuln_component_id,
            index=village_vuln_geojson_filename,
            title='房屋與地質災害潛勢指數',
            type='fill',
            paint={
                'fill-color': {
                    'property': 'vulnerability',
                    'stops': vuln_fill_color_stops
                },
                'fill-opacity': 0.3
            },
            property=JsonList(
                {'key': 'VNAME', 'name': '里名'},
                {'key': 'vulnerability', 'name': '房屋與地質災害潛勢指數'}
            )
        ).insert(conn, on_conflict_do='update')

        add_component_into_dashboard(
            conn, vuln_component_id, 'hackathon-components'
        )
        conn.commit()

    risk_component_id = 88
    risk_component_index = 'village_earthquake_risk_index'
    risk_query_chart = [
        f"""
        (SELECT '{intensity}' AS x_axis, '{category}' AS y_axis, COUNT(*) AS data
        FROM {village_risk_index_table_name}
        WHERE intensity_{intensity} >= {range_begin} AND intensity_{intensity} < {range_end})
        """.strip()
        for category, range_begin, range_end in [('低(<0.25)', 0, 0.25), ('中(<0.5)', 0.25, 0.5), ('高(>0.5)', 0.5, 1)]
        for intensity, _ in quake_intensity_weight
    ]
    risk_query_chart = '\nUNION ALL\n'.join(risk_query_chart)
    risk_query_chart = f"""
    SELECT * FROM ({risk_query_chart}) AS tmp
    ORDER BY CASE
        WHEN (y_axis = '低') THEN 1
        WHEN (y_axis = '中') THEN 2
        WHEN (y_axis = '高') THEN 3
    END
    """.strip()
    # with get_data_engine().connect() as conn:
    #     print(conn.execute(text(risk_query_chart)).all())
    risk_fill_color_stops = [
        [0,    '#dddddd'],
        [0.25, '#ee7777'],
        [0.5,  '#ff0000'],
    ]
    with manager_engine.connect() as conn:
        ComponentManager(
            id=risk_component_id,
            index=risk_component_index,
            name='地震災害風險評估指數',
            query_type='three_d',
            query_chart=risk_query_chart,
            map_config_ids=[
                risk_component_id + i
                for i in range(len(quake_intensity_weight))
            ],
            map_filter={'mode': 'byLayer'},
            time_from='static',
        ).insert(conn, on_conflict_do='update')

        ComponentChartConfig(
            index=risk_component_index,
            types=['BarPercentChart'],
            color=[c for v, c in risk_fill_color_stops],
            unit='個'
        ).insert(conn, on_conflict_do='update')

        for i, (intensity, _) in enumerate(quake_intensity_weight):
            MapConfig(
                id=risk_component_id+i,
                index=village_risk_index_geojson_filename,
                title=intensity,
                type='fill',
                paint={
                    'fill-color': {
                        'property': intensity,
                        'stops': risk_fill_color_stops
                    },
                    'fill-opacity': 0.3
                },
                property=JsonList(
                    {'key': 'VNAME', 'name': '里名'},
                    {'key': intensity, 'name': '災害風險評估指數'}
                )
            ).insert(conn, on_conflict_do='update')

        add_component_into_dashboard(
            conn, risk_component_id, 'hackathon-components'
        )
        conn.commit()
