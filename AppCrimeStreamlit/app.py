# STREAMLIT
import streamlit as st
from streamlit_option_menu import option_menu

# MODULO MAPA
from Módulos.modulo_map import ModuloMap
    
def main():
    modulo_mapa = ModuloMap()
    configuracion_pag = st.set_page_config(
        page_title="App BA Delito",
        page_icon=":chart_with_upwards_trend:",
        layout="wide"
    )
    with st.sidebar:
        selected = option_menu('Menú', ['Mapa', 'Estadística',"Tabla personal"],
            icons=['map', 'bar-chart', 'table'], menu_icon='cast', default_index=0)

    if selected == 'Mapa':
        # SESSIONS STATES
        if "selected_location" not in st.session_state:
            st.session_state.selected_location = None

        col1, col2 = st.columns([4, 10])
        with col1:
            st.image(
                "C:/Users/20391117579/Dropbox/CrimeApp/Multimedia/image.png",  width=350)
        with col2:
            st.title("Ciudad Autónoma de Buenos Aires")

    # CONTAINER MODULO MAPA & DASHBOARD
        m = modulo_mapa.folium_map()
        if st.session_state.selected_location:
            if st.button("Regresar"):
                mapa = modulo_mapa.container_map(m)
                st.session_state.selected_location = None
            else:
                dashboard = modulo_mapa.container_dashboard(_lat=st.session_state.selected_location[0], _lon=st.session_state.selected_location[1])
        else:
            mapa = modulo_mapa.container_map(m)


    elif selected == 'Estadística':
            st.subheader('Estadística')
            st.write("Estadística")

    # CONTAINER ESTADISTICA

if __name__ == "__main__":
    main()

### MEJORAR DASHBOARD