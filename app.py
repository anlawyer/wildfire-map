from bokeh.layouts import column
from bokeh.models import Button
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc

import requests
import json
import math
import xyzservices.providers as xyz
from pyproj import Transformer, transform

from bokeh.models import GeoJSONDataSource, CustomJS, Slider
from bokeh.plotting import figure, show, column

TOOLTIPS = [('County', '@County')]
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

data_url = 'https://incidents.fire.ca.gov/umbraco/api/IncidentApi/GeoJsonList?year='
def fetchData(url):
    geojson_data = requests.get(url).json()
    return geojson_data

data = fetchData(data_url + '2013')
print(data_url + '2013')

def process_json(geojson):
    for i in range(len(geojson['features'])):
        geojson['features'][i]['properties']['Color'] = 'blue'
    
    for i in range(len(geojson['features'])):
        coords = geojson['features'][i]['geometry']['coordinates']
        mercator_coords = transformer.transform(coords[0], coords[1])
        if math.isinf(mercator_coords[0]) or math.isinf(mercator_coords[1]):
            geojson['features'][i]['geometry']['coordinates'] = [0,0]
        else:
            geojson['features'][i]['geometry']['coordinates'] = list(transformer.transform(coords[0], coords[1]))
    return geojson

geo_source = GeoJSONDataSource(geojson=json.dumps(process_json(data)))

p = figure(x_range=(-14500000, -12500000), y_range=(4000000, 5000000),
           x_axis_type="mercator", y_axis_type="mercator", tooltips=TOOLTIPS)

p.add_tile(xyz.OpenStreetMap.Mapnik, retina=True)
p.scatter(x='x', y='y', size=15, color='Color', alpha=0.4, source=geo_source)

date_slider = Slider(value=2013,
                     start=2013,
                     end=2025
                    )

def callback(attr, old, new):
    new_data = fetchData(data_url + str(new))
    geo_source.geojson = json.dumps(process_json(new_data))


date_slider.on_change("value", callback)

layout = column(date_slider, p)

curdoc().add_root(layout)