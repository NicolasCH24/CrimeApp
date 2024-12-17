# STREAMLIT
import streamlit as st
from streamlit_option_menu import option_menu

# MODULO MAPA
from Módulos.modulo_map import folium_map
from streamlit_folium import st_folium
    
def main():
    st.title("App BA Delito")

    with st.sidebar:
        selected = option_menu('Menú', ['Mapa', 'Estadística'],
            icons=['map', 'bar-chart'], menu_icon='cast', default_index=1)

    if selected == 'Mapa':
        col1, col2, col3 = st.columns([0.5,10,0.5])
        with col2:
            st.subheader("Mapa interactivo")
            with st.container(border=True):
                m = folium_map()
                st_folium(m, height=700, width='100%')
    elif selected == 'Estadística':
            st.subheader('Estadística')
            st.write("Estadística")

        
if __name__ == "__main__":
    st.set_page_config(
        page_title="App BA Delito",
        page_icon=":chart_with_upwards_trend:",
        layout="wide"
    )
    main()