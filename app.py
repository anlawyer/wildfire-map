import requests
import json
import math
import xyzservices.providers as xyz
from pyproj import Transformer, transform

from bokeh.models import GeoJSONDataSource, CustomJS, Slider, Title
from bokeh.plotting import figure, show, column, curdoc

TOOLTIPS = [('County', '@County')]
# Needed to transform lat/long values to mercator coordinates
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
# External API from Cal Fire https://www.fire.ca.gov/incidents 
data_url = 'https://incidents.fire.ca.gov/umbraco/api/IncidentApi/GeoJsonList?year='

# Handle API call
def fetchData(url):
    geojson_data = requests.get(url).json()
    return geojson_data

# Initial data fetch with 2013 as the start date
data = fetchData(data_url + '2013')

# Handle json manipulation
def process_json(geojson):
    for i in range(len(geojson['features'])):
        geojson['features'][i]['properties']['Color'] = 'red'
    
    for i in range(len(geojson['features'])):
        coords = geojson['features'][i]['geometry']['coordinates']
        mercator_coords = transformer.transform(coords[0], coords[1])
        if math.isinf(mercator_coords[0]) or math.isinf(mercator_coords[1]):
            geojson['features'][i]['geometry']['coordinates'] = [0,0]
        else:
            geojson['features'][i]['geometry']['coordinates'] = list(transformer.transform(coords[0], coords[1]))
    return geojson

# Initial source data for inital map load
geo_source = GeoJSONDataSource(geojson=json.dumps(process_json(data)))
    
# Map base
p = figure(x_range=(-14500000, -12500000), y_range=(4000000, 5000000),
           x_axis_type="mercator", y_axis_type="mercator", tooltips=TOOLTIPS)
p.add_tile(xyz.OpenStreetMap.Mapnik, retina=True)

# Add data points to map using source data
p.scatter(x='x', y='y', size=15, color='Color', alpha=0.4, source=geo_source)

# Text and titles
p.add_layout(Title(text="This map shows the wildfires that occurred in California during the year selected below", 
                   align="center", text_font_size = '10pt'), "above")
p.add_layout(Title(text="Wildfires in California", 
                   align="center", text_font_size = '20pt'), "above")
p.add_layout(Title(text="Source: CAL FIRE: fire.ca.gov/incidents", align="center", text_alpha = 0.5), "below")
p.add_layout(Title(text="Made by Alison Lawyer", align="center", text_alpha = 0.5), "below")

# Date slider
date_slider = Slider(value=2013, start=2013, end=2025, title='Year', align='center')

# Make new API call when user changes slider
def callback(attr, old, new):
    new_data = fetchData(data_url + str(new))
    geo_source.geojson = json.dumps(process_json(new_data))

# Handle date slider changes
date_slider.on_change("value", callback)

# Combine slider and map, render layout
layout = column(p, date_slider)
curdoc().add_root(layout)
curdoc().title = "California Wildfires"