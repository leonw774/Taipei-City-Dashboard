import requests
import json

import psycopg2
from sqlalchemy import create_engine, URL
import pandas as pd

from get_env import ENVS

url = URL.create(
    "postgresql+psycopg2",
    host="localhost",
    port=ENVS['DB_DASHBOARD_PORT'],
    username=ENVS['DB_DASHBOARD_USER'],
    password=ENVS['DB_DASHBOARD_PASSWORD'],
    database=ENVS['DB_DASHBOARD_DBNAME']
)
engine = create_engine(url)

# Load CSV into a pandas DataFrame
test_csv = 'test_house_age.csv'
df = pd.read_csv(test_csv)

with engine.connect() as conn:
    df.to_sql('test_house_age', conn, index=False, schema='public')
