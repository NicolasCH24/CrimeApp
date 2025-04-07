# STREAMLIT
import streamlit as st
from streamlit_option_menu import option_menu

# TIEMPOS
import time

# MODULOS Y CLASES
from Módulos.modulo_map import ModuloMap
from Módulos.clase_graficos import Graficos

# MODULOS
modulo_mapa = ModuloMap()

# CLASES
clase_graficos = Graficos()

with st.sidebar:
    selected = option_menu('Menú', ['Mapa', 'Estadística',"Tabla personal"],
        icons=['map', 'bar-chart', 'table'], menu_icon='cast', default_index=0)
    
    mapa = modulo_mapa.container_select_data()

if selected == 'Mapa':
    # SESSIONS STATES
    if "selected_location" not in st.session_state:
        st.session_state.selected_location = None
    
    if "selected_hour" not in st.session_state:
        st.session_state.selected_hour = None

    if "hide_informativa" not in st.session_state:
        st.session_state.hide_informativa = False

    col1, col2 = st.columns([4, 10])
    with col1:
        st.image(
            "C:/Users/20391117579/Dropbox/CrimeApp/Multimedia/image.png",  width=350)
    with col2:
        st.title("Ciudad Autónoma de Buenos Aires")

    # CONTAINER MODULO MAPA & DASHBOARD
    m = clase_graficos.folium_map()
    if st.session_state.selected_location and st.session_state.selected_hour:
        if st.button("Regresar"):
            mapa = modulo_mapa.container_main_map(m)
            st.session_state.selected_location = None
            st.session_state.selected_hour = None
        else:
            informativa = modulo_mapa.container_informativo()
            dashboard = modulo_mapa.dashboard(_lat=st.session_state.selected_location[0], _lon=st.session_state.selected_location[1], hora=st.session_state.selected_hour)
    else:
        mapa = modulo_mapa.container_main_map(m)

elif selected == 'Estadística':
    st.subheader('Estadística')
    st.write("Estadística")
# CONTAINER ESTADISTICA