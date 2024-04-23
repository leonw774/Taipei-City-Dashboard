import io
from datetime import datetime
import pytz
from time import sleep
import random

from sqlalchemy import create_engine, inspect, text, URL
import pandas as pd

from get_env import ENVS
from utils import *

clock_table_name = 'the_clock'

dashbaord_url = URL.create(
    "postgresql+psycopg2",
    host="localhost",
    port=ENVS['DB_DASHBOARD_PORT'],
    username=ENVS['DB_DASHBOARD_USER'],
    password=ENVS['DB_DASHBOARD_PASSWORD'],
    database=ENVS['DB_DASHBOARD_DBNAME']
)
data_engine = create_engine(dashbaord_url)

if not inspect(data_engine).has_table(clock_table_name, scheme='public'):
    # Load CSV into a pandas DataFrame
    buffer_csv = b'tick,hour_hand,minute_hand\n'
    for tick in range(60):
        # rand = random.randint(1, 10)
        # buffer_csv += f'{tick},{rand}\n'.encode()
        buffer_csv += f'{tick},0,0\n'.encode()
    buffer_csv = io.BytesIO(buffer_csv)
    df = pd.read_csv(buffer_csv)

    with data_engine.connect() as conn:
        df.to_sql(clock_table_name, conn, index=False, schema='public')
        the_clock_table_all = conn.execute(text(
            f'SELECT * FROM {clock_table_name}'
        )).fetchall()
        conn.commit()
else:
    with data_engine.connect() as conn:
        conn.execute(make_update_clause(
            clock_table_name,
            {'hour_hand': 0, 'minute_hand': 0},
            'true'
        ))
        the_clock_table_all = conn.execute(text(
            f'SELECT * FROM {clock_table_name}'
        )).fetchall()
        conn.commit()
print('initialized the clock')

manager_url = URL.create(
    "postgresql+psycopg2",
    host="localhost",
    port=ENVS['DB_MANAGER_PORT'],
    username=ENVS['DB_MANAGER_USER'],
    password=ENVS['DB_MANAGER_PASSWORD'],
    database=ENVS['DB_MANAGER_DBNAME']
)
manager_engine = create_engine(manager_url)

with manager_engine.connect() as conn:
    chart_query = (
        """(SELECT tick AS x_axis, 'hour' AS y_axis, hour_hand AS data FROM the_clock)
        UNION
        (SELECT tick AS x_axis, 'minute' AS y_axis, minute_hand AS data FROM the_clock)
        ORDER BY x_axis ASC
        """
    )
    clock_component_manager = {
        'id': 87,
        'index': 'the_clock',
        'name': '時鐘',
        'map_config_ids': [],
        'time_from': 'current',
        'update_freq': 1,
        'update_freq_unit': 'minute',
        'source': '本地時間',
        'short_desc': '時間',
        'long_desc': '現在時間，精準到分鐘',
        'use_case': '看時間',
        'links': [],
        'contributors': [],
        'created_at': '2024-04-21 22:00:00+00',
        'updated_at': '2024-04-21 22:00:00+00',
        'query_type': 'three_d',
        'query_chart': chart_query
    }
    conn.execute(make_insert_clause(
        'public.components',
        clock_component_manager,
        on_conflict_action='NOTHING'
    ))

    clock_component_chart_configs = {
        'index': 'the_clock',
        'color': ['#5fa0fa', '#e56056'],
        'types': ['RadarChart'],
        'unit': '單位'
    }
    conn.execute(make_insert_clause(
        'public.component_charts',
        clock_component_chart_configs,
        on_conflict_action='NOTHING'
    ))

    demo_dashboard_components = conn.execute(
        text('SELECT index, components FROM dashboards WHERE index=\'demo-components\'')
    ).first()
    demo_dashboard_components = demo_dashboard_components[1]
    if 87 not in demo_dashboard_components:
        conn.execute(make_update_clause(
            'dashboards',
            {'components': demo_dashboard_components + [87]},
            'index=\'demo-components\''
        ))
    
    conn.commit()

minute_hand_length = 5
hour_hand_length = 3
prev_hour_tick, prev_min_tick = 0, 0
prev_min = 0
while True:
    cur_time = datetime.now(tz=pytz.timezone('Asia/Taipei'))
    cur_hour = cur_time.hour
    cur_min = cur_time.minute
    if cur_min == prev_min:
        continue
    with data_engine.connect() as conn:
        cur_min_tick = cur_min
        cur_hour_tick = (cur_hour % 12) * 5 + cur_min // 12
        if cur_min_tick != prev_min_tick:
            conn.execute(make_update_clause(
                clock_table_name,
                {'minute_hand': 0},
                f'tick={prev_min_tick}'
            ))
            conn.execute(make_update_clause(
                clock_table_name,
                {'minute_hand': minute_hand_length},
                f'tick={cur_min_tick}'
            ))
        if cur_hour_tick != prev_hour_tick:
            conn.execute(make_update_clause(
                clock_table_name,
                {'hour_hand': 0},
                f'tick={prev_hour_tick}'
            ))
            conn.execute(make_update_clause(
                clock_table_name,
                {'hour_hand': hour_hand_length},
                f'tick={cur_hour_tick}'
            ))
        if cur_min_tick != prev_min_tick or cur_hour_tick != prev_hour_tick:
            print(f'update clock: {cur_hour:02d}:{cur_min:02d}')
            conn.commit()
    prev_hour_tick, prev_min_tick = cur_hour_tick, cur_min_tick

    sleep(10)
