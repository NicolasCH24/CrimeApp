# STREAMLIT
import streamlit as st

# REQUESTS
import requests

# MAPA - GRAFICOS
from streamlit_folium import st_folium

# TIEMPO
import datetime

# CLASES
from Módulos.clase_datos import Datos
from Módulos.clase_graficos import Graficos

# SESSION STATES
if "selected_location" not in st.session_state:
    st.session_state.selected_location = None

class ModuloMap:
    def __init__(self):
        self.clase_datos = Datos()
        self.clase_graficos = Graficos()

        #  DASHBOARD DEL DELITO        
    def dashboard(self, _lat, _lon):
        comuna, barrio, hora, peligrosidad = self.clase_datos.get_location_data(_lat, _lon)
        map_box, kpi_mes, kpi_semana, kpi_delito, kpi_peligrosidad, fig_delito, df_locations = self.clase_graficos.graph_dashboard_elements(peligrosidad, comuna, barrio, _lat, _lon)

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

        
        # MODULO MAPA - SELECTORES
    def container_select_data(self):
        from datetime import time

            # METODO DE BUSQUEDA DE LOCALIZACIÓN
        def geocode_address_with_retry(address, city='Caba', country='Argentina', retries=3):
            import time
            url = 'https://nominatim.openstreetmap.org/search'
            params = {
                    'street': address,
                    'city': city,
                    'country': country,
                    'format': 'json',
                    'limit': 3
                }
            headers = {
                    'User-Agent': 'MiAplicacion/1.0 (nico.sp903@gmail.com)'
                }
                
            for attempt in range(retries):
                response = requests.get(url, params=params, headers=headers)
                    
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        return data
                    else:
                        print("No se encontraron resultados.")
                        return None
                elif response.status_code == 429:
                    print("Se excedió el límite de solicitudes, reintentando...")
                    time.sleep(1)
                else:
                    print(f"Error: {response.status_code}")
                    return None
            return None
            
            # RETORNO DE BUSQUEDA
        def get_location_name_lat_lon(location_data):
            nombre = []
            lat = []
            lon = []
            datos_dir = []
            for location in location_data:
                nombre.append(location.get('display_name'))
                lat.append(location.get('lat'))
                lon.append(location.get('lon'))
                datos_dir = [nombre, lat, lon]

            return datos_dir
        # MODULO MAP
        # INTERFAZ DE SIDEBAR

        with st.container(border=True):
            st.markdown("""## 📍 **Conocé tu situación actual**""")
            st.button("Ubicación actual", use_container_width=True)

        with st.container(border=True):
            st.markdown("""## 🗓️ **Consulta programada**""")
            input_destino = st.text_input("Recuerde solo ingresar solo **calle y altura:**")
            location_data = geocode_address_with_retry(input_destino)
            if location_data:
                datos_dir = get_location_name_lat_lon(location_data)
                st.write(datos_dir[0][0])
            else:
                st.write("No se encontraron resultados")
            dia = st.date_input("Seleccioná un día", datetime.date(2023, 11, 1))
            franja_horaria = st.slider("¿En qué momento del día vas a concurrir?.",
                                            value=(time(11, 30)))
            
            ##st.session_state.selected_location[_lat, _lon]
    def container_main_map(self, m):
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

    ## **LLEVAR MARCADOR AL MAPA LUEGO DE HABER TENIDO LA DIRECCION POR PARTE DEL BUSCADOR**