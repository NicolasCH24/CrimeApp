# STREAMLIT
import streamlit as st

# MAPA
import folium as fl
from streamlit_folium import st_folium
from folium.elements import MacroElement
from jinja2 import Template

# TIEMPO
from datetime import time

class AddMarkerOnClick(MacroElement):
    """
    Al hacer clic en el mapa, agrega un marcador en la ubicación clicada con un popup que muestra las coordenadas
    y un botón para eliminar el marcador.
    """
    _template = Template(u"""
        {% macro script(this, kwargs) %}
            function onMapClick(e) {
                var lat = e.latlng.lat.toFixed(6);
                var lng = e.latlng.lng.toFixed(6);
                var popupContent = "Latitud: " + lat + "<br>Longitud: " + lng + "<br><button onclick='removeMarker()'>Eliminar Marcador</button>";
                var marker = L.marker([lat, lng]).addTo({{this._parent.get_name()}});
                marker.bindPopup(popupContent);
                marker.on('popupopen', function() {
                    // Asignar la función removeMarker al botón dentro del popup
                    document.querySelector('button').onclick = function() {
                        {{this._parent.get_name()}}.removeLayer(marker);
                    };
                });
            }
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


def container_map(m):
    # SESSIONS STATES
    if "map_clicked" not in st.session_state:
        st.session_state.map_clicked = False
    
    if "latitud" not in st.session_state:
        st.session_state.latitud = []
    
    if "longitud" not in st.session_state:
        st.session_state.longitud = []

    with st.container(border=True):
        if st.session_state.map_clicked == False:
            destino = st.text_input("Ingresá destino aquí o agregar marcador en el mapa.")
            franja_horaria = st.slider( "Seleccioná en qué momento del día vas a concurrir.",
                                        value=(time(11,30)))
            with st.popover("Información"):
                st.write(st.session_state.latitud, st.session_state.longitud)


        elif st.session_state.map_clicked == True:
            franja_horaria = st.slider(
                                        "Seleccioná en qué momento del día vas a concurrir.",
                                        value=(time(11,30))
                                        )
            with st.popover("Información"):
                st.write(st.session_state.latitud, st.session_state.longitud)

    ## SINCRONIZAR MARCADOR CON SALIDA DE POPUP PARA QUE CUANDO SELECCIONE OTRO MARCADOR SE REESTABLEZCA EL POPUP. ASI COMO ELIMINAR MARCADOR CUANDO SELECCIONO OTRO.

        map = st_folium(m, width="%100", height=500)
        if map.get("last_clicked"):
            st.session_state.map_clicked = True
            st.session_state.latitud = map["last_clicked"]["lat"]
            st.session_state.longitud = map["last_clicked"]["lng"]  
        else:
            st.session_state.map_clicked = False
            st.session_state.latitud = []
            st.session_state.longitud = []
