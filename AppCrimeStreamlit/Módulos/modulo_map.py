# STREAMLIT
import streamlit as st

# DATOS
import pandas as pd

# MAPA - GRAFICOS
import folium as fl
from streamlit_folium import st_folium
from folium.elements import MacroElement
from jinja2 import Template
import plotly.graph_objects as go

# TIEMPO
from datetime import time

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

class ModuloMap:
    def __init__(self):
        self.clase_datos = Datos()

    # FUNCIONALIDADES

    def folium_map(self):
        m = fl.Map(location=[-34.6083, -58.3712], zoom_start=12)
        m.add_child(AddMarkerOnClick())
        return m

    @staticmethod
    @st.cache_resource
    def graph_table(_lat, _lon):
        clase_datos = Datos()
        df_table = clase_datos.get_actual_location_table(_lat, _lon)
        barrio = df_table["Barrio"].values[0]
        barrio = barrio.upper()
        tabla = st.dataframe(
                df_table,
                width=1000,
                column_config={
                    barrio: st.column_config.LineChartColumn(
                        "Contactos por mes",
                        help="Historial de contactos mensuales",
                        y_min=0,
                    ),
                    "Franja horaria": st.column_config.LineChartColumn(
                        "Contactos por franja horaria",
                        help="Historial de contactos por franja horaria",
                        y_min=0,
                    ),
                },
                hide_index=True,
            )
        
        return tabla
    
    @staticmethod
    @st.cache_resource
    def graph_mapa(_lat, _lon):
        fig_map = go.Figure(go.Scattermapbox(
        lat=[_lat],
        lon=[_lon],
        mode='markers',
        ))

        # Configurar el layout del mapa
        fig_map.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            mapbox_style="open-street-map",  # Estilo del mapa
            mapbox_zoom=14,  # Nivel de zoom
            mapbox_center={"lat": _lat, "lon": _lon},  # Centro del mapa
        )
        return fig_map
    
    def graph_new_table(self, _lat, _lon):
        clase_datos = Datos()
        df_table = clase_datos.get_actual_location_table(_lat, _lon)
        barrio = df_table["Barrio"].values[0]
        barrio = barrio.upper()
        tabla = st.dataframe(
                df_table,
                width=1000,
                column_config={
                    barrio: st.column_config.LineChartColumn(
                        "Contactos por mes",
                        help="Historial de contactos mensuales",
                        y_min=0,
                    ),
                    "Franja horaria": st.column_config.LineChartColumn(
                        "Contactos por franja horaria",
                        help="Historial de contactos por franja horaria",
                        y_min=0,
                    ),
                },
                hide_index=True,
            )
        
        return tabla
    
    def graph_new_mapa(self, _lat, _lon):
        fig_map = go.Figure(go.Scattermapbox(
        lat=[_lat],
        lon=[_lon],
        mode='markers',
        ))

        # Configurar el layout del mapa
        fig_map.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            mapbox_style="open-street-map",  # Estilo del mapa
            mapbox_zoom=14,  # Nivel de zoom
            mapbox_center={"lat": _lat, "lon": _lon},  # Centro del mapa
        )
        return fig_map
 
    # DASHBOARD
    def dashboard(self, tabla, fig_map):
        col1 = st.columns([1])
        with col1[0]:
            st.markdown("Mapa del delito")
        
        with st.container(border=True):
            tabla
        col1, col2 = st.columns([4, 10])
        with col2:
            with st.container(border=True):
                st.plotly_chart(fig_map, use_container_width=True)

    # CONTAINER DE SELECCION DE UBICACION & CONTAINER DE DASHBORD INFORMATIVO
    def container_dashboard(self, _lat, _lon):
        tabla = self.graph_new_table(_lat, _lon)
        fig_map = self.graph_new_mapa(_lat, _lon)
        with st.container(border=True):
            dashboard = self.dashboard(tabla, fig_map)

    def container_map(self, m):
        # DATOS GLOBALES
        _df = self.clase_datos.get_df_by_query(query="""
                                            SELECT
                                            FECHA,
                                            FRANJA_HORARIA,
                                            CONTACTO_ID
                                            FROM
                                            FCT_HECHOS
                                            WHERE YEAR(FECHA) = (SELECT MAX(YEAR(FECHA)) FROM FCT_HECHOS)
                                            GROUP BY
                                            FECHA, FRANJA_HORARIA, CONTACTO_ID
                                            ORDER BY
                                            FECHA;
                                            """)
        df_table = self.clase_datos.get_data_table(_df)

        # MODULO MAP
        # SESSION STATES
        if "selected_location" not in st.session_state:
            st.session_state.selected_location = None

        col1, col2 = st.columns([10, 5.5])
        with col1:
            with st.container(border=True):
                destino = st.text_input("Ingresá destino aquí o agregar marcador en el mapa.")
                franja_horaria = st.slider("Seleccioná en qué momento del día vas a concurrir.",
                                        value=(time(11, 30)))
                styled_df = df_table.style.background_gradient(cmap="YlOrBr", axis=None)
                st.markdown("Grilla horaria - Último año")
                tabla_grilla = st.dataframe(styled_df, use_container_width=True, hide_index=False)

        with col2:
            with st.container(border=True, height=663):
                st.write("Selecciona un punto en el mapa.")
                map = st_folium(m, width="%100", height=590, use_container_width=False)
                if map.get("last_clicked"):
                    _lat = map["last_clicked"]["lat"]
                    _lon = map["last_clicked"]["lng"]
                    st.session_state.selected_location = [_lat, _lon]
                    st.rerun()


        
