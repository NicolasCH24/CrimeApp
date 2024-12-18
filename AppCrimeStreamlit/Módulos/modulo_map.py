# STREAMLIT
import streamlit as st

# MAPA
import folium as fl
from streamlit_folium import st_folium

def folium_map():
    m = fl.Map(location=[-34.6083, -58.3712], zoom_start=12)
    m.add_child(fl.LatLngPopup())
    map = st_folium(m, height=700, width='100%')
    return map

def get_location(lat, lon):
    return lat, lon

def get_lat_lon(map):
    data = get_location(map['last_clicked']['lat'], map['last_clicked']['lng'])
    return data

