import io

import sqlalchemy
import pandas as pd
import requests

from utils import *

# Init Data DB

table_name = 'monthly_pedestrian_accidents'
months_limit = 12
# call api to get data
api_base = (
    'https://roadsafety.tw/api/DashboardAjax/GetDashboardStaticDataChartMonth'
    + '?sCity=臺北市&TypeDeathHurt=2&ItemType='
)
all_accidents_url = api_base + '行人'
elder_accidents_url = api_base + '高齡者行人(含代步)'
cross_accidents_url = api_base + '行人路口事故'

respond_json = requests.request('GET', all_accidents_url).json()
monthly_all_accidents = {
    entry['col'][0]: int(entry['value'])
    for entry in respond_json
}

respond_json = requests.request('GET', elder_accidents_url).json()
monthly_elder_accidents = {
    entry['col'][0]: int(entry['value'])
    for entry in respond_json
}

respond_json = requests.request('GET', cross_accidents_url).json()
monthly_cross_accidents = {
    entry['col'][0]: int(entry['value'])
    for entry in respond_json
}

minguo_yms: List[str] = sorted(
    monthly_all_accidents.keys(),
    key=lambda s: int(s[:3])*13+int(s[4:])
)
minguo_ym_timestamp = {
    minguo_ym: (
        f'{int(minguo_ym[:3]) + 1911}-{int(minguo_ym[4:]):02d}-01T00:00:00'
    )
    for minguo_ym in minguo_yms
}

buffer_csv = b'ym,all_number,elder_number,cross_number\n'
for minguo_ym in minguo_yms:
    row = ','.join([
        minguo_ym_timestamp[minguo_ym],
        str(monthly_all_accidents[minguo_ym]),
        str(monthly_elder_accidents[minguo_ym]),
        str(monthly_cross_accidents[minguo_ym]),
    ]) + '\n'
    buffer_csv += row.encode()
# print(buffer_csv.decode())

buffer_csv = io.BytesIO(buffer_csv)
df = pd.read_csv(buffer_csv)
init_data_table_with_df(
    df=df,
    table_name=table_name,
    on_conflict_do='nothing',
    constraint_fields=['ym'],
    dtype={'ym': sqlalchemy.DateTime}
)

# Set Manager DB
manager_engine = get_manager_engine()
component_id = 1
component_index = table_name
line_colors = ['#c74729', '#db822e', '#a8994d']
chart_query = (
    f"""SELECT * FROM (
        (SELECT ym AS x_axis, '行人事故總件數' AS y_axis, all_number AS data
        FROM {table_name}
        GROUP BY x_axis)
        UNION ALL
        (SELECT ym AS x_axis, '高齡行人事故件數' AS y_axis, elder_number AS data
        FROM {table_name}
        GROUP BY x_axis)
        UNION ALL
        (SELECT ym AS x_axis, '路口行人事故件數' AS y_axis, cross_number AS data
        FROM {table_name}
        GROUP BY x_axis)
        ORDER BY x_axis DESC LIMIT {months_limit * 3}
    ) AS tmp
    ORDER BY x_axis, y_axis ASC
    """
)
history_query = (
    f"""SELECT * FROM (
        (SELECT ym AS x_axis, '行人事故總件數' AS y_axis, all_number AS data
        FROM {table_name}
        GROUP BY x_axis)
        UNION ALL
        (SELECT ym AS x_axis, '高齡行人事故件數' AS y_axis, elder_number AS data
        FROM {table_name}
        GROUP BY x_axis)
        UNION ALL
        (SELECT ym AS x_axis, '路口行人事故件數' AS y_axis, cross_number AS data
        FROM {table_name}
        GROUP BY x_axis)
    ) AS tmp
    WHERE DATE_TRUNC('%s', x_axis) BETWEEN '%s' AND '%s'
    ORDER BY x_axis, y_axis ASC;
    """
)
with manager_engine.connect() as conn:
    ComponentManager(
        id=component_id,
        index=component_index,
        name='近一年歷月行人事故件數',
        query_type='time',
        query_chart=chart_query,
        history_config={
            'color': line_colors,
            'range': ['fiveyear_ago']
        },
        map_config_ids=[],
        map_filter=None,
        time_from='current',
        time_to=None,
        update_freq=1,
        update_freq_unit='month',
        source='道安資訊查詢網',
        short_desc='台北市近一年來歷月的行人交通事故件數',
        long_desc='台北市近一年來歷月的行人交通事故總件數，與特殊子類別的件數',
        use_case='通過查看行人交通事故的不同類別的佔比，了解台北當下的行人安全狀況的一個側面',
        links=['https://roadsafety.tw/Dashboard/Custom'],
        contributors=['王彥翔'],
        query_history=history_query
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index=component_index,
        color=line_colors,
        types=['TimelineSeparateChart'],
        unit='件'
    ).insert(conn, on_conflict_do='update')

    add_component_into_dashboard(
        conn, component_id, 'hackathon-components'
    )
    conn.commit()
