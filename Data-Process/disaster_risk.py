import json

import shapely

from utils import *

### Get village borders

village_borders_geojson_path = (
    '../Taipei-City-Dashboard-FE/public/mapData/taipei_village.geojson'
)
with open(village_borders_geojson_path) as village_borders_geojson_file:
    village_borders_geojson = json.load(village_borders_geojson_file)

village_borders_shapes = {
    feature['properties']['VNAME']: shapely.from_geojson(json.dumps(feature))
    for feature in village_borders_geojson['features']
}
print(village_borders_shapes)

### Vulnerabiliies

####### Dangerous Slope

dangerous_slopes_geojson_path = 'data/patrol_artificial_slope.geojson'
with open(dangerous_slopes_geojson_path) as dangerous_slopes_geojson_file:
    dangerous_slopes_geojson = json.load(dangerous_slopes_geojson_file)


###### Old House




###### Liquefaction


