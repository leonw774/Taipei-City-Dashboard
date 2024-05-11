import geopandas as gpd

import pandas as pd


# 讀取 GeoJSON 文件
gdf = gpd.read_file("breastfeeding_room.geojson")

# 選擇需要的欄位
# 假設這些欄位已經存在於 GeoJSON 的 properties 中
df = gdf[['dist', 'name', 'address', 'services']]

# 將services列表轉換為逗號分隔的字符串
df['services'] = df['services'].apply(lambda x: ', '.join(x))


# 存儲為 CSV
df.to_csv("breastfeeding_room.csv", index=False)
