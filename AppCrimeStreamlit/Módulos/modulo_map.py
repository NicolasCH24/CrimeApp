# STREAMLIT
import streamlit as st

# MAPA - GRAFICOS
import folium as fl
from streamlit_folium import st_folium
from folium.elements import MacroElement
from jinja2 import Template
import plotly.graph_objects as go

# TIEMPO
from datetime import time

# DATOS
import pandas as pd

# LOCALIZACION
from Módulos.clase_datos import Datos

class AddMarkerOnClick(MacroElement):
    """
    Al hacer clic en el mapa, agrega un marcador en la ubicación clicada con un popup que muestra las coordenadas
    y un botón para eliminar el marcador.
    """
    _template = Template(u"""
        {% macro script(this, kwargs) %}
            var lastMarker = null;  // Variable para almacenar el último marcador creado

            function onMapClick(e) {
                var lat = e.latlng.lat.toFixed(6);
                var lng = e.latlng.lng.toFixed(6);
                var popupContent = "Latitud: " + lat + "<br>Longitud: " + lng;

                // Si existe un marcador previo, eliminarlo
                if (lastMarker !== null) {
                    {{this._parent.get_name()}}.removeLayer(lastMarker);
                }

                // Crear el nuevo marcador
                lastMarker = L.marker([lat, lng]).addTo({{this._parent.get_name()}});
                lastMarker.bindPopup(popupContent);

                // Configurar el evento para eliminar el marcador al cerrar el popup
                lastMarker.on('popupclose', function() {
                    if (lastMarker !== null) {
                        {{this._parent.get_name()}}.removeLayer(lastMarker);
                        lastMarker = null;  // Reiniciar la variable
                    }
                });
            }

            // Agregar el evento de clic al mapa
            {{this._parent.get_name()}}.on('click', onMapClick);
        {% endmacro %}
    """)


    def __init__(self):
        super().__init__()
        self._name = 'AddMarkerOnClick'


def folium_map():
    m = fl.Map(location=[-34.6083, -58.3712], zoom_start=12)
    m.add_child(AddMarkerOnClick())
    return m

def graph_table(lat, lon):
    clase_datos = Datos()
    df_data = clase_datos.get_current_location(lat, lon)
    # TABLA
    values = [['Fecha',
            'Comuna',
            'Barrio',
            'Franja horaria',
            'Zona',
            'Índice de peligro - Zona']
            , [df_data['Fecha'].values, df_data['Comuna'].values, df_data["Barrio"].values, df_data['Franja Horaria'].values, df_data['Zona'].values, df_data['ZonaPeligroIndice'].values]]

    fig_table = go.Figure(data=[go.Table(
    columnorder = [1,2],
    columnwidth = [60,80],
    header = dict(
        values = [['<b>TABLA DELICTIVA</b><br>para el dia de hoy'],
                    ['<b>DESCRIPCIÓN</b>']],
        line_color='#929795',
        fill_color='black',
        align=['left','center'],
        font=dict(color='white', size=12),
        height=40
    ),
    cells=dict(
        values=values,
        line_color='#929795',
        fill=dict(color=['gray', 'white']),
        align=['left', 'center'],
        font=dict(color="black"),
        font_size=12,
        height=30)
        )
    ])
    fig_table.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    return fig_table

def graph_mapa(lat, lon):
    fig_map = go.Figure(go.Scattermapbox(
    lat=[lat],
    lon=[lon],
    mode='markers',
    ))

    # Configurar el layout del mapa
    fig_map.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        mapbox_style="open-street-map",  # Estilo del mapa
        mapbox_zoom=14,  # Nivel de zoom
        mapbox_center={"lat": lat, "lon": lon},  # Centro del mapa
    )
    return fig_map

def dashboard(fig_table, fig_map):
    col1 = st.columns([1])
    with col1[0]:
        st.markdown("Mapa del delito")
    
    col2_1, col2_2 = st.columns([3, 10])
    with col2_1:
        with st.container(border=True):
            st.plotly_chart(fig_table, use_container_width=True)
    with col2_2:
        with st.container(border=True):
            st.plotly_chart(fig_map, use_container_width=True)

def container_map(m):
    # DATOS GLOBALES
## OBTENER TABLA DE DATOS Y GRAFICARLA CON FORMATO CONDICIONAL DEBAJO DEL MAPA
    ## SI NO CABE, PROBAR CON "MADRUGADA, MAÑANA, TARDE Y NOCHE"
    # SESSIONS STATES
    if "location" not in st.session_state:
        st.session_state.location = None

    col1, col2 = st.columns([5, 10])
    with col1:
        with st.container(border=True):
            destino = st.text_input("Ingresá destino aquí o agregar marcador en el mapa.")
            franja_horaria = st.slider( "Seleccioná en qué momento del día vas a concurrir.",
                                            value=(time(11,30)))

    with col2:
        with st.container(border=True):
            map = st_folium(m, width="%100", height=500)
            if map.get("last_clicked"):
                st.session_state.location = [map["last_clicked"]["lat"], map["last_clicked"]["lng"]]
                with st.expander("Información"):
                    if st.session_state["location"] == [map["last_clicked"]["lat"], map["last_clicked"]["lng"]]:
                        fig_table = graph_table(lat=map["last_clicked"]["lat"], lon=map["last_clicked"]["lng"])
                        fig_map = graph_mapa(lat=map["last_clicked"]["lat"], lon=map["last_clicked"]["lng"])
                        dashboard(fig_table, fig_map)
                        st.session_state.location = None

## MEJORAR EL POPUP, U OBTENER OTRA FORMA DE GENERAR EL INFORME DETALLADO ACTUAL.
        
