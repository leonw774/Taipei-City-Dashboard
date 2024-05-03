from utils import *
import io

# Init Data DB

pm10_table_name = 'pm10'
fake_data = [
    ('中正', 67), ('大直', 69), ('信義', 66), ('南港', 68),
    ('內湖', 71), ('木柵', 49), ('大安', 76), ('天母', 60),
    ('延平', 78), ('承德', 67), ('中北', 70), ('士林', 59),
    ('大同', 71), ('中山', 58), ('古亭', 64), ('向陽', 75),
    ('松山', 67), ('陽明', 40), ('萬華', 65)
]
buffer_csv = b'x_axis,data\n'
buffer_csv += '\n'.join([
    f'{d[0]},{d[1]}'
    for d in fake_data
]).encode()
buffer_csv = io.BytesIO(buffer_csv)
df = pd.read_csv(buffer_csv)
init_data_table_with_df(
    df=df,
    table_name=pm10_table_name,
    on_conflict_do='update',
    constraint_fields=['x_axis']
)

# Set Manager DB

manager_engine = get_manager_engine()
pm10_query_chart = f'SELECT * FROM {pm10_table_name}'

voronoi_component_id = 160
voronoi_map_config_id = 160
with manager_engine.connect() as conn:
    ComponentManager(
        id=voronoi_component_id,
        index='pm10_voronoi',
        name='pm10_voronoi',
        query_type='two_d',
        query_chart=pm10_query_chart,
        map_config_ids=[voronoi_map_config_id],
        map_filter=None,
        time_from='static',
        time_to=None,
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index='pm10_voronoi',
        color=['#aabbcc'],
        types=['RadarChart'],
        unit=''
    ).insert(conn, on_conflict_do='update')

    # insert map config
    insert_clause(
        conn,
        table_name='component_maps',
        row_dict={
            'id': voronoi_map_config_id,
            'index': 'pm10_measurments',
            'title': 'PM10 Voronoi',
            'type': 'voronoi',
            'size': 'big',
            'source': 'geojson',
            'paint': '{"line-color":"#ffffff"}'
        },
        on_conflict_do='update',
        constraint_fields=['id']
    )

    add_component_into_dashboard(
        conn, voronoi_component_id, 'hackathon-components'
    )
    
    conn.commit()


isoline_component_id = 161
isoline_map_config_id = 161
with manager_engine.connect() as conn:
    ComponentManager(
        id=isoline_component_id,
        index='pm10_isoline',
        name='pm10_isoline',
        query_type='two_d',
        query_chart=pm10_query_chart,
        map_config_ids=[isoline_map_config_id],
        map_filter=None,
        time_from='static',
        time_to=None,
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index='pm10_isoline',
        color=['#aabbcc'],
        types=['RadarChart'],
        unit=''
    ).insert(conn, on_conflict_do='update')

    # insert map config
    insert_clause(
        conn,
        table_name='component_maps',
        row_dict={
            'id': isoline_map_config_id,
            'index': 'pm10_measurments',
            'title': 'PM10 Isoline',
            'type': 'isoline',
            'size': 'big',
            'source': 'geojson',
            'paint': '{"line-color":"#ffffff"}'
        },
        on_conflict_do='update',
        constraint_fields=['id']
    )

    add_component_into_dashboard(
        conn, isoline_component_id, 'hackathon-components'
    )
    
    conn.commit()
