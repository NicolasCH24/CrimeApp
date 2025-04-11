
# MAPA - GRAFICOS
import folium as fl
import plotly.graph_objects as go
import pydeck as pdk

# LOCALIZACION
from Módulos.clase_datos import Datos

# MAPA
from folium.elements import MacroElement
from jinja2 import Template


class AddMarkerOnClick(MacroElement):
    """
    Al hacer clic en el mapa, agrega un marcador en la ubicación clicada con un popup que muestra las coordenadas
    y un botón para eliminar el marcador.
    """
    _template = Template(u"""
        {% macro script(this, kwargs) %}
            var lastMarker = null;  // Variable para almacenar el último marcador creado

            function onMapClick(e) {
                var lat = e.latlng.lat.toFixed(6);
                var lng = e.latlng.lng.toFixed(6);
                var popupContent = "Latitud: " + lat + "<br>Longitud: " + lng;

                // Si existe un marcador previo, eliminarlo
                if (lastMarker !== null) {
                    {{this._parent.get_name()}}.removeLayer(lastMarker);
                }

                // Crear el nuevo marcador
                lastMarker = L.marker([lat, lng]).addTo({{this._parent.get_name()}});
                lastMarker.bindPopup(popupContent);

                // Configurar el evento para eliminar el marcador al cerrar el popup
                lastMarker.on('popupclose', function() {
                    if (lastMarker !== null) {
                        {{this._parent.get_name()}}.removeLayer(lastMarker);
                        lastMarker = null;  // Reiniciar la variable
                    }
                });
            }

            // Agregar el evento de clic al mapa
            {{this._parent.get_name()}}.on('click', onMapClick);
        {% endmacro %}
    """)


    def __init__(self):
        super().__init__()
        self._name = 'AddMarkerOnClick'

class Graficos:
    def __init__(self):
        self.clase_datos = Datos()

    # FUNCIONALIDADES

    def folium_map(self):
        m = fl.Map(location=[-34.6083, -58.3712], zoom_start=12)
        m.add_child(AddMarkerOnClick())
        return m

    def graph_dashboard_elements(self, peligrosidad, comuna, barrio, _lat, _lon, hora):
        df_map_box, tupla_mes, tupla_semana, delito_promedio, hechos_delito_promedio, df_locations = self.clase_datos.get_dashboard_data(_lat, _lon, comuna, barrio, hora)
        df_bar = df_map_box
        df_map_box = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['FRANJA_HORARIA'] == hora]

        # MAP BOX
        map_box = pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v11',
            initial_view_state=pdk.ViewState(
                latitude=_lat,
                longitude=_lon,
                zoom=13.7,
                pitch=55,
            ),
            layers=[
                pdk.Layer(
                    "GridLayer",
                    df_map_box,
                    pickable=True,
                    extruded=True,
                    cell_size=100,
                    elevation_scale=1,
                    get_position='[LONGITUD, LATITUD]',
                ),
                #pdk.Layer(
                #    'ScatterplotLayer',
                #    data=df_map_box,
                #    get_position='[LONGITUD, LATITUD]',
                #    get_color='[200, 30, 0, 160]',
                #    get_radius=20,
                #),
            ],
        )

        # KPI MES
        kpi_mes = go.Figure()
        kpi_mes.add_trace(go.Indicator(
            mode="number+delta",
            value=tupla_mes[0],
            title={"text": "Mes actual - Mes anterior",
                "font": {"size": 14, "color": "#0A122A"}},
            delta={'reference': tupla_mes[1]}))

        kpi_mes.update_layout(
            autosize=False,
            width=950,
            height=120,
            margin=dict(l=0, r=0, b=0, t=30, pad=4),
        )

        # KPI SEMANA
        kpi_semana = go.Figure()
        kpi_semana.add_trace(go.Indicator(
            mode="number+delta",
            value=tupla_semana[0],
            title={'text': "Semana actual - Semana anterior",
                "font": {"size": 14, "color": "#0A122A"}},
            delta={'reference': tupla_semana[1]}
        ))

        kpi_semana.update_layout(
            autosize=False,
            width=950,
            height=120,
            margin=dict(l=0, r=0, b=0, t=30, pad=4),
        )

        # KPI DELITO PROMEDIO
        kpi_delito = go.Figure()
        kpi_delito.add_trace(go.Indicator(
            mode="number",
            value=hechos_delito_promedio,
            title={'text': f"Delito promedio - {delito_promedio}",
                "font": {"size": 14, "color": "#0A122A"}},
        ))

        kpi_delito.update_layout(
            autosize=False,
            width=950,
            height=120,
            margin=dict(l=0, r=0, b=0, t=30, pad=4),
        )

        # KPI PELIGROSIDAD
        if peligrosidad <= 25:
            color_barra = "rgba(255, 255, 153, 1)"
        elif peligrosidad <= 50:
            color_barra = "rgba(255, 204, 102, 1)"
        elif peligrosidad <= 75:
            color_barra = "rgba(255, 140, 0, 1)"
        else:
            color_barra = "rgba(255, 0, 0, 1)"

        kpi_peligrosidad = go.Figure()
        kpi_peligrosidad.add_trace(go.Indicator(
            mode="number+gauge",
            value=peligrosidad,
            title={'text': "% Peligrosidad",
                "font": {"size": 14, "color": "#0A122A"}},
            number={'suffix': " %",
                    'font': {'size': 20, 'color': '#0A122A'}},
            gauge={
                'shape': "bullet",
                'axis': {'range': [0, 100], 'visible': False},
                'bar': {'color': color_barra},
                'steps': [
                    {'range': [0, 25], 'color': "rgba(255, 255, 153, 1)"},
                    {'range': [25, 50], 'color': "rgba(255, 204, 102, 1)"},
                    {'range': [50, 75], 'color': "rgba(255, 140, 0, 1)"},
                    {'range': [75, 100], 'color': "rgba(255, 0, 0, 1)"}
                ],
            },
        ))

        kpi_peligrosidad.update_layout(
            autosize=False,
            width=950,
            height=120,
            margin=dict(l=100, r=0, b=0, t=30, pad=4),
        )

        # BARRAS APILADAS
        df_grouped = df_bar.groupby(['TIPO_DELITO_DESC', 'FECHA']).agg({'CONTACTO_ID': 'count'}).rename(columns={'CONTACTO_ID': 'HECHOS'})
        df_grouped_totals = df_grouped.groupby('TIPO_DELITO_DESC')['HECHOS'].sum().reset_index()
        df_grouped_totals = df_grouped_totals.sort_values(by='HECHOS', ascending=True)

        x_data = df_grouped_totals['HECHOS']
        y_data = df_grouped_totals['TIPO_DELITO_DESC']

        max_val = max(x_data)
        min_val = min(x_data)

        def get_gradient_color(value, min_val, max_val):
            ratio = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
            r = int(255 - 30 * ratio)
            g = int(255 - 120 * ratio)
            b = int(200 - 150 * ratio)
            return f'rgb({r},{g},{b})'

        fig_delitos = go.Figure()
        for x, y in zip(x_data, y_data):
            fig_delitos.add_trace(go.Bar(
                x=[x],
                y=[y],
                text=[x],
                orientation='h',
                marker=dict(
                    color=get_gradient_color(x, min_val, max_val),
                    line=dict(color='white', width=1)
                ),
                textfont=dict(color='#0A122A')
            ))

        fig_delitos.update_layout(
            height=400,
            xaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                title='Cantidad de Hechos',
                title_font=dict(color='#0A122A'),
                tickfont=dict(color='#0A122A')
            ),
            yaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                title='Tipo de Delito',
                title_font=dict(color='#0A122A'),
                tickfont=dict(color='#0A122A'),
                categoryorder='total ascending'
            ),
            barmode='stack',
            margin=dict(l=150, r=10, t=30, b=40),
            showlegend=False
        )

        return map_box, kpi_mes, kpi_semana, kpi_delito, kpi_peligrosidad, fig_delitos, df_locations
