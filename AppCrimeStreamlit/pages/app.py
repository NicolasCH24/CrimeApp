# STREAMLIT
import streamlit as st
from streamlit_option_menu import option_menu

# MODULOS Y CLASES
from Módulos.modulo_map import ModuloMap
from Módulos.modulo_estadistica import ModuloEstadistica
from Módulos.clase_graficos import Graficos

# MODULOS
modulo_mapa = ModuloMap()
modulo_estadistica = ModuloEstadistica()

# CLASES
clase_graficos = Graficos()

### INTERFAZ

# HEADER
st.markdown("""
        <div style='display: flex; align-items: center; gap: 10px;'>
            <img src="https://i.pinimg.com/originals/e7/14/98/e71498bc0ed791e366ace0ed2d52dd3b.png" alt="Logo BA" width="100"/>
            <h2 style='margin: 0;'>Ciudad Autónoma de Buenos Aires</h2>
        </div>
        <hr style='border: 2px solid #336ACC;'/>
    """, unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    selected = option_menu('Menú', ['Mapa', 'Estadística',"Tabla personal"],
        icons=['map', 'bar-chart', 'table'], menu_icon='cast', default_index=0)

# MAPA
if selected == 'Mapa':
    # SESSIONS STATES
    if "selected_location" not in st.session_state:
        st.session_state.selected_location = None
    
    if "selected_hour" not in st.session_state:
        st.session_state.selected_hour = None

    if "hide_informativa" not in st.session_state:
        st.session_state.hide_informativa = False

    with st.sidebar:
        mapa = modulo_mapa.container_select_data()

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

# ESTADISTICA
elif selected == 'Estadística':
# CONTAINER FILTROS
    df_filtered = modulo_estadistica.container_select_filter()

# CONTAINER DASHBOARD
    if df_filtered is not None and df_filtered.empty == False:
        dashboard = modulo_estadistica.container_dashboard_estadistico(df_filtered)
    else:
        st.warning("Aplique los filtros correspondientes o haga clic en **Actualizar** para obtener el informe.")
