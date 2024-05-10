import io

import sqlalchemy
import pandas as pd
import requests

from utils import *

### rent subsidy (租金補貼)

# Init Data DB

data_table_name = 'yearly_rent_subsidy'
api_url = (
    'https://data.taipei/api/frontstage/tpeod/dataset/resource.download'
    '?rid=e54950a4-86b4-407b-bccf-180f17e1b310'
)
respond = requests.get(api_url)
downloaded_file = io.BytesIO(respond.content)
df = pd.read_csv(downloaded_file)
kept_col_names = [
    col_name for col_name in df.columns
    if any(substr in col_name for substr in ('申請', '核定')) and '租金' in col_name
]
df = df[['項目'] + kept_col_names]
# turn "XX年度" into just "XX"
df['項目'] = list(map(
    lambda s: f'{int(s[:-2][:3]) + 1911}-01-01T00:00:00',
    df['項目']
))
# print(df)
init_data_table_with_df(
    df=df,
    table_name=data_table_name,
    on_conflict_do='update',
    constraint_fields=['項目'],
    dtype={'項目': sqlalchemy.DateTime}
)

# Set Manager DB

component_id = 5
component_index = 'yearly_rent_subsidy'
columns_queries = [
    f"""(SELECT 項目 AS x_axis, '{col_name}' AS y_axis, {col_name} AS data
    FROM {data_table_name}
    GROUP BY x_axis)
    """
    for col_name in kept_col_names
]
chart_query = ' UNION ALL '.join(columns_queries)
chart_query = f'SELECT * FROM ({chart_query}) AS tmp ORDER BY x_axis, y_axis ASC'

manager_engine = get_manager_engine()
with manager_engine.connect() as conn:
    ComponentManager(
        id=component_id,
        index=component_index,
        name='歷年住宅租金補貼受理情形',
        query_type='time',
        query_chart=chart_query,
        time_from='static',
        source='都發局',
        short_desc='臺北市歷年住宅租金補貼受理申請戶數及核定戶數情形',
        long_desc='臺北市歷年住宅租金補貼受理申請戶數及核定戶數情形',
        use_case='',
        links=['https://data.taipei/dataset/detail?id=6297943a-1e71-480d-967c-635855df66fe'],
        contributors=['王彥翔'],
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index=component_index,
        color=['#FFDB5C', '#FFAF61'],
        types=['TimelineSeparateChart'],
        unit='戶'
    ).insert(conn, on_conflict_do='update')

    add_component_into_dashboard(conn, component_id, 'hackathon-components')
    conn.commit()

### rental housing subleasing (包租代管)

# Init Data DB

data_table_name = 'yearly_rental_housing_subleasing'
csv_str = """年度,媒合戶數
106,17
107,687
108,462
109,229
110,744
111,546
112,499
"""
init_data_table_with_csv_buffer(
    csv_str.encode(),
    table_name=data_table_name,
    on_conflict_do='nothing',
    constraint_fields=['年度']
)

# Set Manager DB

component_id = 6
component_index = 'yearly_rental_housing_subleasing'
chart_query = f"""
    SELECT 年度 AS x_axis, 媒合戶數 AS data
    FROM {data_table_name}
    ORDER BY x_axis ASC
"""
with manager_engine.connect() as conn:
    ComponentManager(
        id=component_id,
        index=component_index,
        name='社會住宅包租代管媒合情形',
        query_type='two_d',
        query_chart=chart_query,
        time_from='static',
        source='都發局',
        short_desc='臺北市政府社會住宅包租代管媒合統計資料',
        long_desc='臺北市政府社會住宅包租代管媒合統計資料',
        use_case='',
        links=['https://data.taipei/dataset/detail?id=1a6432e4-4377-4033-ab00-96228c3d8b40'],
        contributors=['王彥翔'],
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index=component_index,
        color=['#C3FF93'],
        types=['ColumnChart'],
        unit='戶'
    ).insert(conn, on_conflict_do='update')

    add_component_into_dashboard(conn, component_id, 'hackathon-components')
    conn.commit()