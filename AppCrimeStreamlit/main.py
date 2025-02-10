# STREAMLIT
import streamlit as st

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
    st.switch_page('C:/Users/20391117579/Dropbox/CrimeApp/AppCrimeStreamlit/pages/app.py')