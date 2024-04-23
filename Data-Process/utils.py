from typing import Any, Dict, List, Tuple, Union
from sqlalchemy import text, TextClause

AcceptableBasicType = Union[int, float, str]
AcceptableValueType = Union[AcceptableBasicType, List[AcceptableBasicType]]

def pg_repr(obj: AcceptableValueType) -> str:
    assert type(obj).__name__ in ('int', 'float', 'list', 'str'), \
        type(obj).__name__
    if isinstance(obj, str):
        return '\'' + obj.replace('\'', '\'\'') + '\'' # escape
    if isinstance(obj, list):
        types = set(type(elem) for elem in obj)
        assert len(types) == 0 or len(types) == 1 and types.pop() != 'list'
        return '\'{' + ','.join(map(str, obj)) + '}\''
    # default
    return repr(obj)

def make_insert_clause(
        table_name: str,
        row: Dict[str, AcceptableValueType],
        on_conflict_action: str = ''
    ) -> TextClause:
    fields_str = ','.join((str(n) for n in row.keys()))
    values_str = ','.join((pg_repr(n) for n in row.values()))
    stmt = f'INSERT INTO {table_name} ({fields_str}) VALUES ({values_str})'
    if on_conflict_action != '':
        stmt += f' ON CONFLICT DO {on_conflict_action}'
    return text(stmt)

def make_update_clause(table_name: str, set_values: Dict[str, Any], where_text: str = ''):
    set_str = ','.join((k + f'={pg_repr(v)}' for k, v in set_values.items()))
    stmt = f'UPDATE {table_name} SET {set_str}'
    if where_text != '':
        stmt += f' WHERE {where_text}'
    return text(stmt)
