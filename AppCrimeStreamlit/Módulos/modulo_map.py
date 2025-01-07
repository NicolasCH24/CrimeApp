# STREAMLIT
import streamlit as st

# MAPA - GRAFICOS
import folium as fl
from streamlit_folium import st_folium
from folium.elements import MacroElement
from jinja2 import Template
import pydeck as pdk

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
    
    def graph_new_table(self, _lat, _lon):
        df_table, comuna, barrio, hora = self.clase_datos.get_actual_location_table(_lat, _lon)

        tabla = st.dataframe(
            df_table,
            width=1100,
            use_container_width=True,
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
        
        return tabla, comuna, barrio, hora

    def graph_dashboard_elements(self, comuna, barrio, hora, _lat, _lon):
        df_map_box, tupla_mes, tupla_semana, delito_promedio, hechos_delito_promedio = self.clase_datos.get_elements_dashbord(_lat, _lon, comuna, barrio, hora)

        # MAP BOX
        map_box = pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v11',
            initial_view_state=pdk.ViewState(
                latitude=_lat,
                longitude=_lon,
                zoom=13.7,
                pitch=55,
            ),
            layers=[
                pdk.Layer(
                    'HexagonLayer',
                    data=df_map_box,
                    get_position='[LONGITUD, LATITUD]',
                    radius=20,  # Reducir el radio para hexágonos más finos
                    elevation_scale=3,
                    elevation_range=[0, 800],
                    pickable=True,
                    extruded=True,
                ),
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df_map_box,
                    get_position='[LONGITUD, LATITUD]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=20,
                ),
            ],
        )

        return map_box, tupla_mes, tupla_semana, delito_promedio, hechos_delito_promedio
    
    def dashboard(self, _lat, _lon):
        tabla, comuna, barrio, hora = self.graph_new_table(_lat, _lon)
        map_box, tupla_mes , tupla_semana, delito_promedio, hechos_delito_promedio= self.graph_dashboard_elements(comuna, barrio, hora, _lat, _lon)
        st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] {
            font-size: 20px; /* Tamaño uniforme para valores */
            height: 50px; /* Altura fija para todos */
        }
        [data-testid="stMetricDelta"] {
            font-size: 16px; /* Tamaño uniforme para deltas */
            height: 20px; /* Altura fija para deltas */
        }
        </style>
        """,
        unsafe_allow_html=True,
        )
        with st.container(border=True):
            col1, col2 = st.columns([14, 10])  # Ajusta las proporciones de las columnas
            with col1:
                st.markdown("### Indicadores clave (KPIs)")
                kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                with kpi_col1:
                    st.metric(label="Hechos Mes actual - Mes anterior - 5 kilometros", value=tupla_mes[0], delta=tupla_mes[1], border=True)
                with kpi_col2:
                    st.metric(label="Hechos Semana actual - Semana anterior - 5 kilometros", value=tupla_semana[0], delta=tupla_semana[1], border=True)
                with kpi_col3:
                    st.metric(label="Delito promedio", value=delito_promedio, delta = hechos_delito_promedio , border=True)
            with col2:
                st.markdown("#### Mapa del delito")  # Título para el mapa
                st.pydeck_chart(map_box, use_container_width=True)  # Mostrar el mapa directamente

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


### HACER LOS KPI CON PLOTLY