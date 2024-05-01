import io
from datetime import datetime
import pytz
from time import sleep

import pandas as pd

from utils import *

# Init Data DB

clock_table_name = 'the_clock'
# Make CSV buffer and load into pandas DataFrame
buffer_csv = b'tick,hour_hand,minute_hand\n'
for tick in range(60):
    # rand = random.randint(1, 10)
    # buffer_csv += f'{tick},{rand}\n'.encode()
    buffer_csv += f'{tick},0,0\n'.encode()
buffer_csv = io.BytesIO(buffer_csv)
df = pd.read_csv(buffer_csv)
init_data_table_with_df(
    df=df,
    table_name=clock_table_name,
    on_conflict_do='update',
    constraint_fields=['tick']
)

# Set Manager DB

manager_engine = get_manager_engine()
clock_component_id = 87
clock_index = 'the_clock'
chart_query = (
    f"""(SELECT tick AS x_axis, 'hour' AS y_axis, hour_hand AS data
    FROM {clock_table_name})
    UNION
    (SELECT tick AS x_axis, 'minute' AS y_axis, minute_hand AS data
    FROM {clock_table_name})
    ORDER BY x_axis ASC
    """
)
with manager_engine.connect() as conn:
    ComponentManager(
        id=clock_component_id,
        index=clock_index,
        name='時鐘',
        query_type='three_d',
        query_chart=chart_query,
        map_config_ids=[],
        map_filter=None,
        time_from='current',
        time_to=None,
        update_freq=1,
        update_freq_unit='minute',
        source='本地時間',
        short_desc='時鐘',
        long_desc='顯示現在時間，精準到分鐘',
        use_case='看現在時間',
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index=clock_index,
        color=['#5fa0fa', '#e56056'],
        types=['RadarChart'],
        unit='單位'
    ).insert(conn, on_conflict_do='update')

    add_component_into_dashboard(
        conn, clock_component_id, 'demo-components'
    )
    conn.commit()

# Update Data DB

data_engine = get_data_engine()
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
            update_clause(
                conn=conn,
                table_name=clock_table_name,
                set_dict={'minute_hand': 0},
                where_dict={'tick': prev_min_tick}
            )
            update_clause(
                conn=conn,
                table_name=clock_table_name,
                set_dict={'minute_hand': minute_hand_length},
                where_dict={'tick': cur_min_tick}
            )
        if cur_hour_tick != prev_hour_tick:
            update_clause(
                conn=conn,
                table_name=clock_table_name,
                set_dict={'hour_hand': 0},
                where_dict={'tick': prev_hour_tick}
            )
            update_clause(
                conn=conn,
                table_name=clock_table_name,
                set_dict={'hour_hand': hour_hand_length},
                where_dict={'tick': cur_hour_tick}
            )
        if (cur_min_tick != prev_min_tick
            or cur_hour_tick != prev_hour_tick):
            print(f'update clock: {cur_hour:02d}:{cur_min:02d}')
            conn.commit()
    prev_hour_tick, prev_min_tick = cur_hour_tick, cur_min_tick

    sleep(10)
