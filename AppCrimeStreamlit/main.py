# STREAMLIT
import streamlit as st

# CLASES
from Módulos.clase_datos import Datos, load_models

# TITULO APP
st.set_page_config(page_title="App BA Delito",
        page_icon=":chart_with_upwards_trend:",
        layout="wide",
        initial_sidebar_state='collapsed')

st.write("# Bienvenido al sistema de GCBA para la detección del delito por la ciudad. 👋")

st.markdown(
    """
    Este sistema está diseñado para trabajar con algorítmos de 
    Aprendizaje automático y herramientas Inteligencia artificial.
    ### Sitios y documentación de interés.
    - Documentación [CrimeApp](https://github.com/NicolasCH24/CrimeApp)
    - Fuente de datos [GCBA](https://mapa.seguridadciudad.gob.ar/)
    - Para cualquier pregunta en Linkedin [Desarrollador](https://www.linkedin.com/in/nicolas-chaparro-012aa325a/)
    ### Portfolio y proyectos
    - Portfolio [GitHub] (https://github.com/NicolasCH24)
    - DataEngineer TAsk [Infraestructura de datos del empléo en Argentina](https://github.com/NicolasCH24/Portfolio/tree/main/DataEngineerWH)
"""
)

if st.button("Comenzar", icon=':material/touch_app:', use_container_width=False):
    with st.spinner("Cargando datos..."):
        # CARGAMOS MODELOS
        modelos = load_models()
        st.session_state['modelos'] = modelos
        kmeans, scaler_kmeans, scaler_d_tree, d_tree_model = modelos

        # CARGAMOS DATOS
        clase_datos = Datos(kmeans=kmeans, scaler_kmeans=scaler_kmeans, scaler_d_tree=scaler_d_tree, d_tree_model=d_tree_model)
        df_datos = clase_datos.get_all_data()
        st.session_state['datos_estadistica'] = df_datos
    st.switch_page('C:/Users/20391117579/Dropbox/CrimeApp/AppCrimeStreamlit/pages/app.py')