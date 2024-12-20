# STREAMLIT
import streamlit as st
from streamlit_option_menu import option_menu

# MODULO MAPA
from Módulos.modulo_map import folium_map, container_map
    
def main():
    #st.title("App BA Delito")
    with st.sidebar:
        selected = option_menu('Menú', ['Mapa', 'Estadística',"Tabla personal"],
            icons=['map', 'bar-chart', 'table'], menu_icon='cast', default_index=0)

    if selected == 'Mapa':
        col1, col2 = st.columns([4, 10])
        with col1:
            st.image(
                "C:/Users/20391117579/Dropbox/CrimeApp/Multimedia/image.png",  width=350)
        with col2:
            st.title("Ciudad Autónoma de Buenos Aires")

    # CONTAINER MAP
        m = folium_map()
        modulo_mapa = container_map(m)

    elif selected == 'Estadística':
            st.subheader('Estadística')
            st.write("Estadística")

    # CONTAINER ESTADISTICA

        
if __name__ == "__main__":
    st.set_page_config(
        page_title="App BA Delito",
        page_icon=":chart_with_upwards_trend:",
        layout="wide"
    )
    main()
