# STREAMLIT
import streamlit as st
from streamlit_option_menu import option_menu

# MODULO MAPA
from Módulos.modulo_map import folium_map
    
def main():
    #st.title("App BA Delito")

    with st.sidebar:
        selected = option_menu('Menú', ['Mapa', 'Estadística'],
            icons=['map', 'bar-chart'], menu_icon='cast', default_index=1)

    if selected == 'Mapa':
        col1, col2 = st.columns([5.3,20])
        with col1:
            st.image("C:/Users/20391117579/Dropbox/CrimeApp/Multimedia/image.png", width=350)
        with col2:
            st.title("Ciudad Autónoma de Buenos Aires")
        map = folium_map()

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