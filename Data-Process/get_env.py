import os

ENVS = dict()
with open('../docker/.env', 'r') as env_file:
	ENVS = dict(
		line.rstrip().split('=')
		for line in env_file
		if not line.startswith('#') and line.count('=') == 1
	)

GEOJSON_PATH = '../Taipei-City-Dashboard-FE/public/mapData'
