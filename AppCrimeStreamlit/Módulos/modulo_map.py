# STREAMLIT
import streamlit as st

# MAPA - GRAFICOS
from streamlit_folium import st_folium
from geopy import Nominatim

# CLASES
from Módulos.clase_datos import Datos
from Módulos.clase_graficos import Graficos

# SESSION STATES
if "selected_street" not in st.session_state:
    st.session_state.selected_street = None

if "selected_location" not in st.session_state:
    st.session_state.selected_location = None

if "selected_hour" not in st.session_state:
    st.session_state.selected_hour = None

class ModuloMap:
    def __init__(self):
        self.clase_datos = Datos()
        self.clase_graficos = Graficos()

    # CONTAINER SELECTORES
    def container_select_data(self):
        from datetime import time

        # RETORNO DE BUSQUEDA
        @st.cache_resource()
        def create_geolocator():
            geolocator = Nominatim(user_agent="my-app", timeout=4)
            return geolocator
            
            # METODO DE BUSQUEDA DE LOCALIZACIÓN
        def geocode_address_with_retry(address):
            geolocator = create_geolocator()
            if address:
                try:
                    response = geolocator.geocode(f"{address}, Ciudad Autónoma de Buenos Aires, Argentina", language='es_ESP', country_codes="AR", exactly_one=True)
                except Exception as e:
                    print("No se ha encontrado resultados.")

                if response:
                    location = response.address.split(",")[0] + "," + response.address.split(",")[2]
                    latitude = response.latitude
                    longitude = response.longitude
                    datos_dir = [location, latitude, longitude]
                    return datos_dir
                else:
                    mensaje = "No se han encontrado resultados"
                    return mensaje
            else:
                mensaje = "Por favor indique una localización correspondiente."
                return mensaje

        # INTERFAZ DE SIDEBAR
        with st.container(border=True):
            st.markdown("""## 📍 **Conocé tu situación actual**""")
            st.button("Ubicación actual", use_container_width=True)

        with st.container(border=True):
            datos_dir = []
            st.markdown("""## 🗓️ **Consulta programada**""")
            input_destino = st.text_input("Recuerde solo ingresar solo **calle y altura:**")
            franja_horaria = st.slider("¿En qué momento del día vas a concurrir?.",
                                            value=(time(11, 30)))
            button_data = st.button(label="Buscar", icon=':material/touch_app:')
            if button_data and input_destino:
                datos_dir = geocode_address_with_retry(input_destino)
                if datos_dir:
                    st.write(f"Resultado: {datos_dir[0]}")
                    st.info(f"Opta por ir a las: {franja_horaria.hour}")
                else:
                    st.write("No se encontraron resultados")
            else:
                button_data == False
            if datos_dir != [] and franja_horaria:
                st.session_state.selected_hour = franja_horaria.hour
                st.session_state.selected_location = [float(datos_dir[1]), float(datos_dir[2])]
                st.session_state.selected_street = datos_dir[0]
            ##st.session_state.selected_location[_lat, _lon]


    # CONTAINER MAIN MAP
    def container_main_map(self, m):
        # INTERFAZ CENTRAL
        subtitulo_funcionamiento = st.markdown("""
                ## 📝 ¿Cómo funciona?
                """)
        col1, col2, col3 = st.columns(3)
            
        with col1:
            st.markdown("""
                - 📍 **Conocé tu situación actual:** Si estás en un punto en particular de la ciudad, hacé clic en **Ubicación actual** para obtener la información relevante.  
                """)

        with col2:
            st.markdown("""
                - 🗓️ **Consulta programada:** Si necesitás ir a algún lugar en una hora particular, seleccioná esos parámetros en la barra lateral y obtené el informe.
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
        
        with st.expander("""🌍 **Experiencia visual: Seleccioná un punto en el mapa.**"""):
            with st.container(border=True):
                map = st_folium(m, width="%100", height=500, use_container_width=True)
                if map.get("last_clicked"):
                    _lat = map["last_clicked"]["lat"]
                    _lon = map["last_clicked"]["lng"]
                    st.session_state.selected_location = [_lat, _lon]
                    st.rerun()

    # CONTAINER INFORMATIVO PRE DASHBOARD
    def container_informativo(self):
        lista_delitos = self.clase_datos.get_contextual_crimes()
        st.markdown("## 🚨 Nuestros delitos a analizar")
        st.markdown('\n'.join([f"- {delito}" for delito in lista_delitos]))
  
        st.markdown(
                    """
                    ### Puntos clave:
                    - Debemos tener en cuenta que en los horarios de la madrugada no hay tanta cantidad de delitos como en el resto del dia.
                    - Esto no significa que sea menos peligroso, sinó que hay menos ciudadanos en la calle.
                                    
                    Por ende si se cometen crimenes frente a mayor cantidad de ciudadanos presentes en ese horario quizás estemos frente a **un momento del día bastante peligroso**.
                    """)

    #  DASHBOARD DEL DELITO        
    def dashboard(self, _lat, _lon, hora):
        with st.spinner("Generando dashboard..."):
            comuna, barrio, peligrosidad = self.clase_datos.get_location_data(_lat, _lon, hora)
            map_box, kpi_mes, kpi_semana, kpi_delito, kpi_peligrosidad, fig_delito, df_locations = self.clase_graficos.graph_dashboard_elements(peligrosidad, comuna, barrio, _lat, _lon, hora)
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
                        st.info("Esta tabla contiene los sucedido en tu zona y horario seleccionado.")
                        st.dataframe(df_locations, use_container_width=True, hide_index=True)
                    with st.container(border=True):
                        st.plotly_chart(fig_delito, theme='streamlit')
                with col2:
                    st.markdown("#### Mapa del delito")
                    with st.container(border=True):
                        st.plotly_chart(kpi_peligrosidad)
                    with st.container(border=True):
                        st.pydeck_chart(map_box, use_container_width=True, height=739)

    ## **LLEVAR MARCADOR AL MAPA LUEGO DE HABER TENIDO LA DIRECCION POR PARTE DEL BUSCADOR**