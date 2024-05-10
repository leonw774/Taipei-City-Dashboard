import requests
import sqlalchemy

from utils import *

# Init Data DB

table_name = 'volcano_microseism'
date_limit = 10
api_url = 'https://tvo.ncree.narl.org.tw/sys/api/MonitoringInformation/Load'
api_url += '?MonitoringType=%E5%BE%AE%E9%9C%87%E7%9B%A3%E6%B8%AC'
api_url += f'&Page=1&Limit={date_limit}'
response_json = requests.get(api_url).json()
assert response_json['code'] == 200
csv_buffer = b'date,value\n'
csv_buffer += '\n'.join([
    entry['monitoringDate'] + ',' + str(entry['monitoringValue']) + '\n'
    for entry in response_json['data']
]).encode()
init_data_table_with_csv_buffer(
    csv_buffer,
    table_name,
    on_conflict_do='update',
    constraint_fields=['date'],
    dtype={'date': sqlalchemy.DateTime}
)

# Set Manager DB

manager_engine = get_manager_engine()
component_id = 2
component_index = table_name
chart_query = (f"""
    SELECT * FROM (
        SELECT TO_CHAR(date, 'YYYY/MM/DD') AS x_axis, value AS data
        FROM {table_name}
        ORDER BY x_axis DESC LIMIT {date_limit}
    ) AS tmp
    ORDER BY x_axis ASC
""").strip()
with manager_engine.connect() as conn:
    ComponentManager(
        id=component_id,
        index=component_index,
        name='大屯火山近十天微震發生次數',
        query_type='two_d',
        query_chart=chart_query,
        history_config=None,
        map_config_ids=[],
        map_filter=None,
        time_from='current',
        time_to=None,
        update_freq=1,
        update_freq_unit='day',
        source='大屯火山觀測站-菁山監測站',
        short_desc='大屯火山近十天微震發生次數',
        long_desc='大屯火山近十天微震發生次數',
        use_case=(
            '地震觀測是研究火山活動常見且非常有效的一種方法。目前在大屯火山群地區利用高密度的地震觀測網，長期監測地震活動，'
            '了解火山地震在時間與空間的分布狀況，並由記錄的地震波形，辨識地震震源的種類，有助討論大屯火山群地震的成因與火山活動的可能性。'
            '(引用來源: https://tvo.ncree.narl.org.tw/decrypt/watch/earthquake)'
        ),
        links=['https://tvo.ncree.narl.org.tw/decrypt/live'],
        contributors=['王彥翔'],
        query_history=None
    ).insert(conn, on_conflict_do='update')

    ComponentChartConfig(
        index=component_index,
        color=['#ff9966'],
        types=['ColumnChart'],
        unit='次'
    ).insert(conn, on_conflict_do='update')

    add_component_into_dashboard(
        conn, component_id, 'hackathon-components'
    )
    conn.commit()
