from dataclasses import dataclass, field
from datetime import datetime, UTC
import json
from typing import Any, Dict, List, ClassVar, Union, Literal, Optional

import pandas as pd
from sqlalchemy import (
    create_engine, text,
    URL, CursorResult, Connection
)
from get_env import *

### TYPINGS

DBBasicType = Optional[Union[int, float, str]]
JsonDict = Dict[str, 'JsonDict']
DBValueType = Union[
    DBBasicType, List[DBBasicType], JsonDict
]
Table_Dict = Dict[str, DBValueType]
BASIC_TYPES = (type(None), int, float, str)


### DATABASE CONNECTIONS

MANAGER_URL = URL.create(
    "postgresql+psycopg2",
    host="localhost",
    port=ENVS['DB_MANAGER_PORT'],
    username=ENVS['DB_MANAGER_USER'],
    password=ENVS['DB_MANAGER_PASSWORD'],
    database=ENVS['DB_MANAGER_DBNAME']
)

def get_manager_engine():
    return create_engine(MANAGER_URL)

DASHBORD_URL = URL.create(
    "postgresql+psycopg2",
    host="localhost",
    port=ENVS['DB_DASHBOARD_PORT'],
    username=ENVS['DB_DASHBOARD_USER'],
    password=ENVS['DB_DASHBOARD_PASSWORD'],
    database=ENVS['DB_DASHBOARD_DBNAME']
)

def get_dashboard_engine():
    return create_engine(DASHBORD_URL)


### HELPER FUNCTIONS

def insert_row(
        conn: Connection,
        table_name: str,
        row_dict: Dict[str, DBValueType],
        on_conflict_do: str = Literal['nothing', 'update'],
        constraint_fields: Optional[List[str]] = None) -> CursorResult[Any]:
    fields_str = ','.join((str(n) for n in row_dict.keys()))
    values_str = ','.join((pg_repr(n) for n in row_dict.values()))
    stmt = f'INSERT INTO {table_name} ({fields_str}) VALUES ({values_str})'
    assert on_conflict_do in ('nothing', 'update')
    if on_conflict_do == 'nothing':
        stmt += f' ON CONFLICT DO NOTHING'
    else:
        assert (constraint_fields is not None
            and isinstance(constraint_fields, list)
            and len(constraint_fields) != 0
        )
        constraint_str = ','.join(constraint_fields)
        set_str = ','.join([
            f'{k}=EXCLUDED.{k}'
            for k in row_dict
            if k not in constraint_fields
        ])
        stmt += f' ON CONFLICT ({constraint_str}) DO UPDATE SET {set_str}'
    # print(stmt)
    return conn.execute(text(stmt))

def delete_row(
        conn: Connection,
        table_name: str,
        where_dict: Dict[str, DBValueType]) -> CursorResult[Any]:
    where_str = ','.join(
        (f'{k}={pg_repr(v)}' for k, v in where_dict)
    )
    stmt = f'DELETE FROM {table_name} WHERE {where_str}'
    # print(stmt)
    return conn.execute(text(stmt))

def update_row(
        conn: Connection,
        table_name: str,
        set_dict: Dict[str, Any],
        where_dict: Optional[Dict[str, Any]] = None) -> CursorResult[Any]:
    set_str = ','.join(
        (f'{k}={pg_repr(v)}' for k, v in set_dict.items())
    )
    stmt = f'UPDATE {table_name} SET {set_str}'
    if where_dict is not None:
        stmt += ' WHERE ' + ','.join(
            (f'{k}={pg_repr(v)}' for k, v in where_dict.items())
        )
    # print(stmt)
    return conn.execute(text(stmt))

def pg_repr(obj: DBValueType) -> str:
    assert type(obj) in BASIC_TYPES + (list, dict), \
        type(obj)
    
    if obj is None:
        return 'NULL'

    if isinstance(obj, str):
        return '\'' + obj.replace('\'', '\'\'') + '\'' # escape
    
    if isinstance(obj, list):
        types = set(type(elem) for elem in obj)
        assert (
            len(types) == 0 or len(types) == 1
            and types.pop() in BASIC_TYPES
        )
        return '\'{' + ','.join(map(str, obj)) + '}\''

    if isinstance(obj, dict):
        # key_types = set(type(k) for k in obj)
        # assert (
        #     len(key_types) == 0 or len(key_types) == 1
        #     and key_types.pop() in BASIC_TYPES
        # )
        # assert all(
        #     type(value) in BASIC_TYPES + (list, dict)
        #     for value in obj.values()
        # )
        
        # dont need check, just use json.dump
        return json.dumps(obj)

    # default
    return repr(obj)

def add_component_into_dashboard(
        conn: Connection,
        component_id: int,
        dashboard_index: str) -> None:
    original_components: List[int] = conn.execute(text(
        f'SELECT index, components \
            FROM dashboards \
            WHERE index={pg_repr(dashboard_index)}'
    )).first()[1]
    if component_id in original_components:
        return
    new_components = original_components + [component_id]
    update_row(
        conn,
        table_name='dashboards',
        set_dict={'components': new_components},
        where_dict={'index': dashboard_index}
    )

def get_now_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S+00")


### HELPER CLASSES

@dataclass
class TableBase:
    table_name: ClassVar[str]
    primary_key_field: ClassVar[str]

    def insert(
            self,
            conn: Connection,
            on_conflict_do: Literal['nothing', 'update'] = 'nothing') -> None:
        assert on_conflict_do in ('nothing', 'update')
        insert_row(
            conn=conn,
            table_name=self.table_name,
            row_dict=vars(self),
            on_conflict_do=on_conflict_do,
            constraint_fields=[self.primary_key_field]
        )

    def update(self, conn: Connection) -> None:
        self_dict = vars(self)
        pk_value = self_dict.pop(self.primary_key_field)
        update_row(
            conn=conn,
            table_name=self.table_name,
            set_dict=self_dict,
            where_dict={self.primary_key_field: pk_value},
        )

@dataclass
class ComponentChartConfig(TableBase):
    ### required
    index: str # primary key, func dependent on 'index' in ComponentManager
    color: List[str]
    types: List[Literal[
        'BarChart', 'BarPercentChart', 'ColumnChart', 'DonutChart',
        'GuageChart', 'RadarChart', 'TimelineSeparateChart',
        'TimelineStackedChart', 'TreemapChart', 'DistrictChart',
        'MetroChart', 'HeatmapChart', 'PolarAreaChart', 'ColumnLineChart'
        'BarChartWithGoal', 'IconPercentChart'
    ]]
    unit: str

    ### constants
    table_name: ClassVar[str] = 'public.component_charts'
    primary_key_field: ClassVar[str] = 'index'

@dataclass
class MapConfig:
    pass

@dataclass
class ComponentManager(TableBase):
    ### required
    id: int # primary key, number id of components
    index: str # the name of component used by api
    name: str # the name to appear on website
    query_type: Literal['time', 'map_legend', 'percent', 'two_d', 'three_d']
    query_chart: str # the sql query for the data

    ### optional
    history_config: Optional[JsonDict] = None # visual setting for history
    map_config_ids: List[int] = field(default_factory=list) # maps to filter
    map_filter: Optional[JsonDict] = None # how to filter map
    time_from: Literal[
        'static', 'demo', 'current', 'max',
        'tenyear_ago', 'fiveyear_ago', 'twoyear_ago', 'year_ago',
        'halfyear_ago', 'quarter_ago', 'month_ago', 'week_ago', 'day_ago'
    ] = 'demo'
    time_to: Optional[Literal['now']] = None
    created_at: str = field(default_factory=get_now_timestamp)
    updated_at: str = field(default_factory=get_now_timestamp)
    update_freq: Optional[int] = None
    update_freq_unit: Optional[Literal[
        'minute', 'hour', 'day', 'week', 'month'
    ]] = None
    source: Optional[str] = None # source authority of the data
    short_desc: Optional[str] = None
    long_desc: Optional[str] = None
    use_case: Optional[str] = None
    links: List[str] = field(default_factory=list)
    contributors: List[str] = field(default_factory=list)

    ### constants
    table_name: ClassVar[str] = 'public.components'
    primary_key_field: ClassVar[str] = 'id'

