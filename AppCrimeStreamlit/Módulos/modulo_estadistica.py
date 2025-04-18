# STREAMLIT 
import streamlit as st

# CLASES
from Módulos.clase_datos import Datos
from Módulos.clase_graficos import Graficos

# CLASE
class ModuloEstadistica:
    def __init__(self):
        kmeans, scaler_kmeans, scaler_d_tree, d_tree_model = self.get_models()
        self.clase_datos = Datos(kmeans=kmeans, scaler_kmeans=scaler_kmeans, scaler_d_tree=scaler_d_tree, d_tree_model=d_tree_model)
        self.clase_graficos = Graficos()

    def get_global_data(self):
        df_data = st.session_state.get("datos_estadistica", None)
        if df_data is None:
            st.error("Datos no cargados. Volvé al inicio.")
            st.stop()

        return df_data
    
    def get_models(self):
        modelos = st.session_state.get("modelos", None)
        if modelos is None:
            st.error("Modelos no cargados. Volvé al inicio.")
            st.stop()

        kmeans, scaler_kmeans, scaler_d_tree, d_tree_model = modelos

        return kmeans, scaler_kmeans, scaler_d_tree, d_tree_model

    def container_select_filter(self):
        ### DATOS GLOBALES
        df_data = self.get_global_data()

        ## DATOS DE FILTROS
        # AÑOS
        años = tuple(df_data['AÑO'].unique())

        # COMUNAS/BARRIOS
        comunas_barrios = {
            'COMUNA 1': [
                'RETIRO', 'SAN NICOLAS', 'PUERTO MADERO', 'SAN TELMO',
                'MONSERRAT', 'CONSTITUCION'
            ],
            'COMUNA 2': ['RECOLETA'],
            'COMUNA 3': ['BALVANERA', 'SAN CRISTOBAL'],
            'COMUNA 4': ['LA BOCA', 'BARRACAS', 'PARQUE PATRICIOS', 'NUEVA POMPEYA'],
            'COMUNA 5': ['ALMAGRO', 'BOEDO'],
            'COMUNA 6': ['CABALLITO'],
            'COMUNA 7': ['FLORES', 'PARQUE CHACABUCO'],
            'COMUNA 8': ['VILLA LUGANO', 'VILLA RIACHUELO', 'VILLA SOLDATI'],
            'COMUNA 9': ['LINIERS', 'MATADEROS', 'PARQUE AVELLANEDA'],
            'COMUNA 10': ['VILLA LURO', 'MONTE CASTRO', 'VELEZ SARSFIELD', 'FLORESTA', 'VERSALLES', 'VILLA REAL'],
            'COMUNA 11': ['VILLA DEVOTO', 'VILLA DEL PARQUE', 'VILLA SANTA RITA'],
            'COMUNA 12': ['VILLA PUEYRREDON', 'VILLA URQUIZA', 'SAAVEDRA', 'COGHLAN'],
            'COMUNA 13': ['BELGRANO', 'COLEGIALES', 'NUÑEZ'],
            'COMUNA 14': ['PALERMO'],
            'COMUNA 15': ['VILLA CRESPO', 'CHACARITA', 'AGRONOMIA', 'VILLA ORTUZAR', 'PARQUE CHAS', 'LA PATERNAL']
        }
        comunas = tuple(comunas_barrios.keys())

        # DELITOS
        delitos = tuple(df_data['TIPO_DELITO_DESC'].unique())

        # INTERFAZ DE SELECCION
        with st.sidebar:
            with st.container(border=True):
                # SELECT AÑO/MES
                año = st.selectbox(
                    "Año",
                    años,
                    index=None,
                    placeholder="Seleccionar año"
                )

                if año is not None:
                    meses_disponibles = (
                        df_data[df_data["AÑO"] == año]["MES_NUM"]
                        .dropna()
                        .unique()
                    )
                    meses_ordenados = sorted(meses_disponibles, key=lambda m: int(m))

                    mes = st.selectbox(
                        "Mes",
                        meses_ordenados,
                        index=None,
                        placeholder="Seleccionar mes"
                    )
                else:
                    mes = None

                # SELECT COMUNA/BARRIOS
                comuna = st.selectbox(
                    'Comuna',
                    comunas,
                    index=None,
                    placeholder="Seleccionar comuna"
                )

                if comuna is not None:
                    barrios_disponibles = (
                        df_data[df_data['COMUNA_DESC'] == comuna]['BARRIO_DESC']
                        .dropna()
                        .unique()
                    )
                    barrio = st.selectbox(
                        "Barrio",
                        barrios_disponibles,
                        index=None,
                        placeholder="Selecionar barrio"
                    )
                else:
                    barrio = None
                
                # DELITOS
                delito = st.selectbox(
                    'Delito',
                    delitos,
                    index=None,
                    placeholder="Seleccionar delito"
                )

                # FRANJA HORARIA
                franja_horaria = st.slider("Seleccionar rango horario", df_data['FRANJA_HORARIA'].min(), df_data['FRANJA_HORARIA'].max(), (6, 10))

                # DF FILTERED
                if st.button("Actualizar", type="primary"):
                    try:
                        df_filtered = self.clase_datos.get_filtered_df(df_data, año, mes, comuna, barrio, delito, franja_horaria)
                        return df_filtered
                    except Exception as e:
                        mensaje = f"Error al filtrar fuente de datos: {e}"
                        return mensaje

    def container_dashboard_estadistico(self, df_filtered):
        fig_kpi1, fig_kpi2, fig_kpi3, fig_kpi4, fig_line = self.clase_graficos.graph_estadistica_elements(df_filtered)

            # INTERFAZ DE DASHBOARD
        if df_filtered is not None and df_filtered.empty == False:
            with st.spinner("Generando dashboard..."):   
                with st.container(border=True):
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    with kpi_col1:
                        with st.container(border=True):
                            st.plotly_chart(fig_kpi1)
                    with kpi_col2:
                        with st.container(border=True):
                            st.plotly_chart(fig_kpi2)
                    with kpi_col3:
                        with st.container(border=True):
                            st.plotly_chart(fig_kpi3)
                    with kpi_col4:
                        with st.container(border=True):
                            st.plotly_chart(fig_kpi4)
                    with st.container(border=True):
                        st.plotly_chart(fig_line)
        else:
            st.warning("Aplique los filtros deseados para obtener el dashboard estadístico.")
        
        
