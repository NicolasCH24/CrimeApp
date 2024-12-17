# STREAMLIT
import streamlit as st

# MAPA
import folium

def folium_map():
    m = folium.Map(location=[-34.6083, -58.3712], zoom_start=12)
    return m