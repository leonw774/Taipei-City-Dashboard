import io
import json
import sys

import requests

from utils import *

# Init Data DB

data_table_name = 'village_population_density'
try:
    a = sys.argv[1]
except IndexError:
    a = ''

if a != 'skip-init-data':
    # get population_total
    download_url = (
        'https://data.taipei/api/frontstage/tpeod/dataset/resource.download'
        '?rid=a92f4f08-9c3c-4122-98ce-00a3c38ece06'
    )
    response = requests.get(download_url, stream=True)
    response.raw.decode_content = True
    downloaded_file = io.BytesIO(response.content)
    downloaded_file_bytes_lines = downloaded_file.readlines()
    # we only want total population for each vil.
    downloaded_file_bytes_lines = downloaded_file_bytes_lines[4::3]
    # we only want the 3rd and 5th column: village name and total population
    downloaded_file_bytes_lines_splited = [
        line.split(b',', maxsplit=6)
        for line in downloaded_file_bytes_lines
    ]
    village_population = dict([
        (line_splits[3].decode('big5'), int(line_splits[5]))
        for line_splits in downloaded_file_bytes_lines_splited
    ])
    village_population['糖蔀里'] = village_population['糖?里']
    # print(village_population)

    # directly read from front end geojson
    taipei_village_geojson_path = (
        '../Taipei-City-Dashboard-FE/public/mapData/'
        'taipei_village.geojson'
    )
    with open(taipei_village_geojson_path, 'r') as taipei_village_geojson_file:
        taipei_village_geojson = json.load(taipei_village_geojson_file)
    # print(taipei_village_geojson['features'][0])
    village_area = {
        feature['properties']['VNAME']: (
            feature['properties']['AREA'] / 1_000_000 # from m^2 to km^2
        )
        for feature in taipei_village_geojson['features']
    }

    assert '糖蔀里' in village_population
    assert '糖蔀里' in village_area

    # calculate the polulation density
    village_population_density = {
        vname: round(village_population[vname] / village_area[vname], 2)
        for vname in village_area
    }

    csv_buffer = b'village_name,population_density\n'
    csv_buffer += '\n'.join([
        f'{vname},{density}'
        for vname, density in village_population_density.items()
    ]).encode()
    init_data_table_with_csv_buffer(
        csv_buffer=csv_buffer,
        table_name=data_table_name,
        on_conflict_do='update',
        constraint_fields=['village_name']
    )

    taipei_village_pop_density_geojson = taipei_village_geojson
    # write new json data to Front End!
    for feature in taipei_village_pop_density_geojson['features']:
        vname = feature['properties']['VNAME']
        feature['properties'] = {
            'VNAME': vname,
            'POP_DENSITY': village_population_density[vname]
        }
    fe_pop_density_geojson_file_path = (
        '../Taipei-City-Dashboard-FE/public/mapData/'
        'taipei_village_pop_density.geojson'
    )
    with open(fe_pop_density_geojson_file_path, 'w') as fe_geojson_file:
        json.dump(taipei_village_pop_density_geojson, fe_geojson_file)


# Set Manager DB
manager_engine = get_manager_engine()
query_chart = (f"""
    SELECT village_name AS x_axis, population_density AS data
    FROM {data_table_name}
    ORDER BY data DESC
""")
density_fill_color_stops = [
    [0,     '#505050'],
    [25000, '#909010'],
    [75000, '#ffff10'],
]

component_id = 3
component_index = 'village_population_density'
map_config_id = 3
with manager_engine.connect() as conn:
    ComponentManager(
        id=component_id,
        index=component_index,
        name='台北市各里戶籍人口密度',
        query_type='two_d',
        query_chart=query_chart,
        map_config_ids=[map_config_id],
        map_filter=None,
        time_from='static',
        time_to=None,
        source=['臺北市民政局'],
        short_desc='台北市各里戶籍人口密度',
        long_desc='台北市各里戶籍人口密度',
        use_case='可疊加於其他圖層上'
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index=component_index,
        color=[],
        types=['BarChart'],
        unit='每平方公里人口'
    ).insert(conn, on_conflict_do='update')

    MapConfig(
        id=map_config_id,
        index='taipei_village_pop_density',
        title='各里戶籍人口密度',
        type='fill',
        size=None,
        icon=None,
        paint={
            # 'fill-color': '#abcdef',
            'fill-color': {
                'property': 'POP_DENSITY',
                'stops': density_fill_color_stops
            },
            'fill-opacity': 0.3
        },
        property=JsonList(
            {'key': 'VNAME', 'name': '里名'},
            {'key': 'POP_DENSITY', 'name': '戶籍人口密度'}
        )
    ).insert(conn, on_conflict_do='update')

    add_component_into_dashboard(
        conn, component_id, 'hackathon-components'
    )
    conn.commit()
