# STREAMLIT
import streamlit as st

# MAPA - GRAFICOS
import folium as fl
from streamlit_folium import st_folium
import plotly.graph_objects as go
from folium.elements import MacroElement
from jinja2 import Template
import pydeck as pdk

# TIEMPO
from datetime import time, datetime

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

    def graph_dashboard_elements(self, peligrosidad, comuna, barrio, _lat, _lon):
        df_map_box, tupla_mes, tupla_semana, delito_promedio, hechos_delito_promedio, df_locations = self.clase_datos.get_dashboard_data(_lat, _lon, comuna, barrio)
        df_bar = df_map_box
        df_map_box = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['FRANJA_HORARIA'] == datetime.now().hour]
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
        # KPI MES
        kpi_mes = go.Figure()
        kpi_mes.add_trace(go.Indicator(
            mode = "number+delta",
            value = tupla_mes[0],
            title = {"text": "Mes actual - Mes anterior",
                     "font": {"size": 14, "color": "white"}},
            delta = {'reference': tupla_mes[1]}))
        
        kpi_mes.update_layout(
            #grid={'rows': 0, 'columns': 0, 'pattern': "independent"},
            autosize=False,
            width=950,
            height=120,
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=30,
                pad=4
            ),
        )
        
        # KPI SEMANA
        kpi_semana = go.Figure()
        kpi_semana.add_trace(go.Indicator(
            mode = "number+delta",
            value= tupla_semana[0],
            title= {'text':"Semana actual - Semana anterior",
                    "font": {"size": 14, "color": "white"}},
            delta = {'reference':tupla_mes[1]}
        ))

        kpi_semana.update_layout(
            #grid={'rows': 0, 'columns': 1, 'pattern': "independent"},
            autosize=False,
            width=950,
            height=120,
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=30,
                pad=4
            ),
        )

        # KPI DELITO PROMEDIO
        kpi_delito = go.Figure()
        kpi_delito.add_trace(go.Indicator(
            mode="number",
            value = hechos_delito_promedio,
            title = {'text':f"Delito promedio - {delito_promedio}",
                     "font": {"size": 14, "color": "white"}},
        ))

        kpi_delito.update_layout(
            #grid={'rows': 0, 'columns': 0, 'pattern': "independent"},
            autosize=False,
            width=950,
            height=120,
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=30,
                pad=4
            ),
        )

        # KPI PELIGROSIDAD
        if peligrosidad <= 25:
            color_barra = "rgba(255, 255, 153, 1)"  
        elif peligrosidad <= 50:
            color_barra = "rgba(255, 204, 102, 1)"  
        elif peligrosidad <= 75:
            color_barra = "rgba(255, 140, 0, 1)"
        else:
            color_barra = "rgba(255, 0, 0, 1)"

        # Crear la figura
        kpi_peligrosidad = go.Figure()

        kpi_peligrosidad.add_trace(go.Indicator(
            mode="number+gauge",
            value=peligrosidad,
            title = {'text':"% Peligrosidad",
                     "font": {"size": 14, "color": "white"}},
            number={'suffix': " %",
                    'font':{'size':20, 'color':'white'}}, 
            gauge={
                'shape': "bullet",
                'axis': {'range': [0, 100], 'visible': False}, 
                'bar': {'color': color_barra},  
                'steps': [  
                    {'range': [0, 25], 'color': "rgba(255, 255, 153, 1)"},  
                    {'range': [25, 50], 'color': "rgba(255, 204, 102, 1)"}, 
                    {'range': [50, 75], 'color': "rgba(255, 140, 0, 1)"}, 
                    {'range': [75, 100], 'color': "rgba(255, 0, 0, 1)"}  
                ],
            },
            #domain={'x': [0.05, 0.5], 'y': [0.15, 0.35]} 
        ))

        kpi_peligrosidad.update_layout(
            autosize=False,
            width=950,
            height=120,
            margin=dict(
                l=100,
                r=0,
                b=0,
                t=30,
                pad=4),
        
        )

        # GRAFICO DE BARRAS APILADAS
        df_grouped = df_bar.groupby(['TIPO_DELITO_DESC', 'FECHA']).agg({'CONTACTO_ID':'count'}).rename(columns={'CONTACTO_ID':'HECHOS'})
        df_grouped_totals = df_grouped.groupby('TIPO_DELITO_DESC')['HECHOS'].sum().reset_index()

        df_grouped_totals = df_grouped_totals.sort_values(by='HECHOS', ascending=True)

        x_data = df_grouped_totals['HECHOS']
        y_data = df_grouped_totals['TIPO_DELITO_DESC']

        max_val = max(x_data)
        min_val = min(x_data)

        def get_gradient_color(value, min_val, max_val):
            ratio = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
            r = int(255 - 30 * ratio)  
            g = int(255 - 120 * ratio) 
            b = int(200 - 150 * ratio)  
            return f'rgb({r},{g},{b})'

        # Crear figura
        fig_delitos = go.Figure()

        for x, y in zip(x_data, y_data):
            fig_delitos.add_trace(go.Bar(
                x=[x],
                y=[y],
                text=[x],
                orientation='h',
                marker=dict(
                    color=get_gradient_color(x, min_val, max_val),  # Aplicar degradado
                    line=dict(color='white', width=1)
                ),
                textfont=dict(color='black')  # Fuente blanca
            ))

        # Configuración de diseño
        fig_delitos.update_layout(
            height=400,
            xaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                title='Cantidad de Hechos',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                title='Tipo de Delito',
                title_font=dict(color='white'),
                tickfont=dict(color='white'),
                categoryorder='total ascending'
            ),
            barmode='stack',
            margin=dict(l=150, r=10, t=30, b=40),
            showlegend=False
        )

        return map_box, kpi_mes, kpi_semana, kpi_delito, kpi_peligrosidad, fig_delitos, df_locations
    
    def dashboard(self, _lat, _lon):
        comuna, barrio, hora, peligrosidad = self.clase_datos.get_location_data(_lat, _lon)
        map_box, kpi_mes, kpi_semana, kpi_delito, kpi_peligrosidad, fig_delito, df_locations = self.graph_dashboard_elements(peligrosidad, comuna, barrio, _lat, _lon)

        with st.container(border=True):
            col1, col2 = st.columns([16, 10])
            with col1:
                st.markdown("### Indicadores clave (KPIs) - Hechos")
                kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                with kpi_col1:
                    with st.container(border=True):
                        st.plotly_chart(kpi_mes)
                with kpi_col2:
                    with st.container(border=True):
                        st.plotly_chart(kpi_semana)
                with kpi_col3:
                    with st.container(border=True):
                        st.plotly_chart(kpi_delito)
                with st.container(border=True):
                    st.dataframe(df_locations, use_container_width=True, hide_index=True)
                with st.container(border=True):
                    st.plotly_chart(fig_delito, theme='streamlit')
            with col2:
                st.markdown("#### Mapa del delito")
                with st.container(border=True):
                    st.plotly_chart(kpi_peligrosidad)
                with st.container(border=True):
                    st.pydeck_chart(map_box, use_container_width=True, height=669)

    def container_select_data(self):
        # DEPENDENCIAS
        import datetime

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

        # INTERFAZ DE SIDEBAR

        with st.container(border=True):
            st.markdown("""## 📍 **Conocé tu situación actual**""")
            st.button("Ubicación actual", use_container_width=True)

        with st.container(border=True):
            st.markdown("""## 🗓️ **Consulta programada**""")
            destino = st.text_input("Ingresá destino aquí.")
            dia = st.date_input("Seleccioná un día", datetime.date(2023, 11, 1))
            franja_horaria = st.slider("¿En qué momento del día vas a concurrir?.",
                                        value=(time(11, 30)))
            #styled_df = df_table.style.background_gradient(cmap="YlOrBr")
            #st.markdown("Grilla horaria - Último año")
            #tabla_grilla = st.dataframe(styled_df, use_container_width=True, hide_index=False)


    def container_main_map(self, m):
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
        # SESSION STATES
        if "selected_location" not in st.session_state:
            st.session_state.selected_location = None

        ## DATOS
        año, mes_actual, mes_anterior, fecha_min, fecha_max = self.clase_datos.get_contextual_time_series()

        lista_delitos = self.clase_datos.get_contextual_crimes()

        # INTERFAZ CENTRAL
        subtitulo_funcionamiento = st.markdown("""
            ## 📝 ¿Cómo funciona?
            """)
        col1, col2, col3 = st.columns(3)
        #with col1:
        #    st.markdown("## 📅 Rango temporal de datos  \n"
        #                    "Nuestros análisis van a corresponder a los últimos **dos meses**, incluyendo: \n"  
        #                    f"- **Mes actual:** {mes_actual} {str(año)} \n"  
        #                    f"- **Mes anterior:** {mes_anterior} {str(año)} \n"  
        #                    f"- **Rango:** {fecha_min} - {fecha_max}")
        
        with col1:
            st.markdown("""
            - 📍 **Conocé tu situación actual:** Si estás en un punto en particular de la ciudad, hacé clic en **Ubicación actual** para obtener la información relevante.  
            """)

        with col2:
            st.markdown("""
            - 🗓️ **Consulta programada:** Si necesitás ir a algún lugar en un día y hora particular, seleccioná esos parámetros en la barra lateral y obtené el informe.
            """)

        with col3:
            st.markdown("""
            - 🌍 **Experiencia visual:** Para un enfoque más interactivo, hacé clic en el mapa sobre el punto al que querés dirigirte, y se generarán los datos relevantes para vos.
            """)

        subtitulo_expectativas = st.markdown("""
            ## 🧐 ¿Con qué información te vas a encontrar?
            """)
        
        expectativas = st.markdown("""
            Basados en un exhaustivo análisis del crimen en CABA y tu situación geografica podrás conocer:
            - **Puntos de inflexión:** Localizaciones específicas a tener en cuenta.
            - **Mapa del delito:** Para una visualización clara de lo que suele suceder cerca de donde vos estás.
            - **Lista de delitos:** Delitos más frecuentes y su cantidad de hechos.
            - **ÍNDICE DE PELIGROSIDAD:** Un indice de peligro basado en los algorítmos mejores entrenados de estudio criminalistico.
            """)

        
        #with col3:
        #    st.markdown("## 🚨 Nuestros delitos a analizar")
        #    st.markdown('\n'.join([f"- {delito}" for delito in lista_delitos]))

            
                    
                    ## ME GUSTARIA TENER AL LADO DE EL MARKWOWN ANTETIOR LA LISTA DE MIS DELITOS POR ITEMS PERO ARRIBA UN TITPO COMO ... NUESTROS DELITOS A ANALIZAR, (LA LISTA )
                    #st.markdown(
                    #            """
                    #            ### Puntos clave:
                    #            - Debemos tener en cuenta que en los horarios de la madrugada no hay tanta cantidad de delitos como en el resto del dia.
                    #            - Esto no significa que sea menos peligroso, sinó que hay menos ciudadanos en la calle.
                    #            
                    #            Por ende si se cometen crimenes frente a mayor cantidad de ciudadanos presentes en ese horario quizás estemos frente a **un momento del día bastante peligroso**.
                    #            """
                    #        )


        with st.container(border=True):
            st.markdown("""🌍 **Experiencia visual: Seleccioná un punto en el mapa.**""")
            map = st_folium(m, width="%100", height=500, use_container_width=True)
            if map.get("last_clicked"):
                _lat = map["last_clicked"]["lat"]
                _lon = map["last_clicked"]["lng"]
                st.session_state.selected_location = [_lat, _lon]
                st.rerun()

