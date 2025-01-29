# DATOS & TIEMPO
import pandas as pd
from datetime import datetime
import pytz

# STREAMLIT
import streamlit as st

# MODELADO
from joblib import load

# LOCALIZACION
from geopy import Nominatim
from geopy.distance import geodesic

# BASE DE DATOS
from sqlalchemy import create_engine

# CONFIGURACION LOCA
import locale
locale.setlocale(locale.LC_TIME, 'es_ES')

# KMEANS
@st.cache_resource()
def load_models():
    kmeans = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/kmeans.joblib')
    scaler = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/scaler.joblib')
    return kmeans, scaler

kmeans, scaler = load_models()

class Datos:
    ### SQL
    def __init__(self):
        self.scaler = scaler
        self.kmeans = kmeans
        self.hostname = "localhost"
        self.dbname = "crimewarehouse"
        self.uname = "root"
        self.pwd = "admin1234"

        self.engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=self.hostname, db=self.dbname, user=self.uname, pw=self.pwd))
        
    @st.cache_data
    def get_df_by_query(_self, query):
        db = _self.engine
        df = pd.read_sql(query, db)
        print("ejecutando query")
        return df
    
    ### DATOS DE PAGINA DE SELECCION DE DATOS
    @staticmethod
    @st.cache_data
    def get_data_table(_df):
        # Configuración local
        # DF Table data
        _df['FECHA'] = pd.to_datetime(_df['FECHA'])
        _df['DIA_SEMANA'] = _df['FECHA'].dt.strftime("%A")

        df_data = pd.DataFrame(
            {'CONTACTO_ID':_df['CONTACTO_ID'].values,
             'Dia semana':_df['DIA_SEMANA'].values,
             'Hora':_df['FRANJA_HORARIA'].values}
        )

        orden_dias = ['lunes','martes','miércoles','jueves','viernes','sábado','domingo']
        df_data['Dia semana'] = pd.Categorical(_df['DIA_SEMANA'], categories=orden_dias, ordered=True)

        df_table = df_data.pivot_table(
            index = 'Hora',
            columns ='Dia semana',
            values = 'CONTACTO_ID',
            aggfunc ='count',
            fill_value=0,
            observed=False
        )

        return df_table

    ### DATOS DASHBOARD
    def get_current_location(self, lat, lon):
        zonas_peligro = pd.read_csv("C:/Users/20391117579/Dropbox/CrimeApp/Datasets/Zona peligro/zona_puntaje.csv")
        geolocator = Nominatim(user_agent="AppCrimeStreamlit")
        location = geolocator.reverse((lat, lon), exactly_one=True, language='es')
        direccion = location.raw['address']

        # Barrio
        barrio = direccion.get("suburb", "Sin definir")

        # Comuna
        comuna = direccion.get("state_district", "Sin definir")

        # Fecha
        hoy = datetime.now(tz=pytz.timezone('America/Argentina/Buenos_Aires')).strftime("%d-%m-%Y, %H")
        hoy = pd.to_datetime(hoy, format="%d-%m-%Y, %H")
        fecha = hoy.date()

        # Franja horaria
        franja_horaria = hoy.hour

        # Zona
        coordenadas = [[lat, lon]]
        x_scaled = self.scaler.transform(coordenadas)

        # Diccionario de datos
        dict_data = {
            'Fecha':fecha,
            'Franja Horaria': franja_horaria,
            'Comuna': comuna,
            'Barrio': barrio
        }

        dict_data = {k:[v] for k,v in dict_data.items()}
        df_data = pd.DataFrame(dict_data)

        df_data['cluster'] = self.kmeans.predict(x_scaled)
        df_data['Zona'] = df_data['cluster'] + 1

        def danger_zone(zona):
            return zonas_peligro.loc[zonas_peligro['Zona'] == zona, 'Puntaje Normalizado'].iloc[0]
        
        df_data['ZonaPeligroIndice'] = df_data['Zona'].apply(danger_zone)

        df_data = df_data[['Fecha','Franja Horaria','Comuna','Barrio','Zona','ZonaPeligroIndice']]

        return df_data
    

    # GENERAR ÍNDICE DE PELIGROSIDAD
    def get_hazard_index(self, df_data):
        df = df_data.rename(columns={'Fecha':'FECHA','Fraja Horaria':'FRANJA_HORARIA',
                                     'Comuna':'COMUNA_NUM','Barrio':'BARRIO_MUM',
                                     'Zona':'ZONA','ZonaPeligroIndice':'ZONA_PELIGRO_INDICE'})
            # Serie temporal
        df['FECHA'] = pd.to_datetime(df['FECHA'])
        df['MES'] = df['FECHA'].dt.month 
        df['DIA_DEL_MES'] = df['FECHA'].dt.day  
        df['DIA_DEL_AÑO'] = df['FECHA'].dt.day_of_year
        df['SEMANA_DEL_AÑO'] = df['FECHA'].dt.isocalendar().week
        df['SEMANA_DEL_AÑO'] = df['SEMANA_DEL_AÑO'].astype(int) 
        df['TRIMESTRE'] = df['FECHA'].dt.quarter  
        df['DIA_DE_LA_SEMANA'] = df['FECHA'].dt.dayofweek 
        
        df.replace('0:00', 0, inplace=True)
        df['FRANJA_HORARIA'] = df['FRANJA_HORARIA'].astype(int)

        df['ES_FIN_DE_SEMANA'] = df['DIA_DE_LA_SEMANA'].apply(lambda x: 1 if x in [5, 6] else 0)
        df['ESTACION'] = df['MES'].apply(lambda x: 4 if x in [12, 1, 2] else (1 if x in [3, 4, 5] else (2 if x in [6, 7, 8] else 3)))

        bins = [0, 6, 12, 18, 24]
        labels = [1, 2, 3, 4]
        df['HORARIO_CATEGORIZADO'] = pd.cut(df['FRANJA_HORARIA'], bins=bins, labels=labels, right=False)
        df['HORARIO_CATEGORIZADO'] = df['HORARIO_CATEGORIZADO'].astype(int)

        df_time_series = df[['FECHA', 'LATITUD', 'LONGITUD', 'ESTACION', 'MES', 'TRIMESTRE',
                                    'SEMANA_DEL_AÑO', 'DIA_DEL_AÑO', 'DIA_DEL_MES', 'DIA_DE_LA_SEMANA',
                                    'ES_FIN_DE_SEMANA', 'HORARIO_CATEGORIZADO', 'FRANJA_HORARIA',
                                    'ZONA', ]]
        
    
    def get_actual_location_table(self, lat, lon):
        clase_datos = Datos()
        # Localizacion actual
        df_data = clase_datos.get_current_location(lat, lon)
        comuna = df_data['Comuna'].values[0]
        comuna = comuna.upper()
        barrio = df_data['Barrio'].values[0]
        barrio = barrio.upper()
        hora = df_data['Franja Horaria'].values[0]
    
        # Obtenemos datos
        query = """
            SELECT
                fct.FECHA, fct.FRANJA_HORARIA, dimc.COMUNA_DESC, dimb.BARRIO_DESC, fct.CONTACTO_ID
            FROM
                FCT_HECHOS fct
            JOIN
                DIM_BARRIOS dimb
            ON
                fct.BARRIO_KEY = dimb.BARRIO_KEY
            JOIN
                DIM_COMUNAS dimc
            ON
                fct.COMUNA_KEY = dimc.COMUNA_KEY
            WHERE
                YEAR(FECHA) = (SELECT MAX(YEAR(FECHA)) FROM FCT_HECHOS)
                AND dimc.COMUNA_DESC = %(comuna)s
                AND dimb.BARRIO_DESC = %(barrio)s
            GROUP BY
                FECHA, COMUNA_DESC, BARRIO_DESC, CONTACTO_ID
            ORDER BY
                FECHA;
            """

            # Ejecutar consulta con parámetros
        df_db = pd.read_sql(query, self.engine, params={"comuna": comuna, "barrio": barrio})
        
        df_db['FECHA'] = pd.to_datetime(df_db['FECHA'])
        df_db['MES'] = df_db['FECHA'].dt.strftime("%b")

        df_tabla = pd.DataFrame(
            {
                'Fecha':[df_data['Fecha'].values[0]],
                'Hora': [df_data['Franja Horaria'].values[0]],
                'Comuna':[comuna],
                'Barrio':[barrio],
                'Zona 10':[df_data['ZonaPeligroIndice'].values[0]],
                barrio:[df_db.groupby('MES').agg({'CONTACTO_ID':'count'}).values.flatten().tolist()],
                'Franja horaria':[df_db.groupby('FRANJA_HORARIA').agg({'CONTACTO_ID':'count'}).values.flatten().tolist()]
            }
        )

        return df_tabla, comuna, barrio, hora
    
    def get_elements_dashbord(self, _lat, _lon, comuna, barrio):
        new_location = _lat, _lon
        # DATOS MAP BOX
        query = """
            SELECT
                fct.FECHA,
                fct.FRANJA_HORARIA,
                fct.LATITUD,
                fct.LONGITUD,
                dimb.BARRIO_DESC,
                dtd.TIPO_DELITO_DESC,
                fct.CONTACTO_ID
            FROM
                FCT_HECHOS fct
            JOIN
                DIM_BARRIOS dimb
            ON
                fct.BARRIO_KEY = dimb.BARRIO_KEY
            JOIN
                DIM_COMUNAS dimc
            ON
                fct.COMUNA_KEY = dimc.COMUNA_KEY
            JOIN
                DIM_TIPO_DELITO dtd
            ON
                fct.TIPO_DELITO_KEY = dtd.TIPO_DELITO_KEY
            WHERE 
                YEAR(fct.FECHA) = (SELECT MAX(YEAR(fct.FECHA)) FROM FCT_HECHOS fct)
                AND dimb.BARRIO_DESC = %(barrio)s
                AND dimc.COMUNA_DESC = %(comuna)s
            GROUP BY
            fct.FECHA, fct.FRANJA_HORARIA, fct.LATITUD, fct.LONGITUD, dimb.BARRIO_DESC, dtd.TIPO_DELITO_DESC ,fct.CONTACTO_ID
            ORDER BY
            FECHA;
            """
        df_map_box = pd.read_sql(query, con=self.engine, params={'comuna':comuna, 'barrio':barrio})

        # KPIS
        # KPI HECHOS MES ACTUAL VS ANTERIOR EN RADIO DE 5 KM
        df_map_box['FECHA'] = pd.to_datetime(df_map_box['FECHA'])
        df_map_box['MES'] = df_map_box['FECHA'].dt.month
      
        count_mes_actual = 0
        count_mes_anterior = 0
        locations_mes_actual = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['MES'] == datetime.now().month].values
        locations_mes_anterior = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['MES'] == (datetime.now() - pd.DateOffset(months=1)).month].values

        for location in locations_mes_actual:
            if geodesic(new_location, location).km <= 5:
                count_mes_actual += 1

        for location in locations_mes_anterior:
            if geodesic(new_location, location).km <= 5:
                count_mes_anterior += 1
        
        tupla_mes = count_mes_actual, count_mes_anterior

        # KPI SEMANA ACTUAL VS SEMANA ANTERIOR RADIO 5 KM
        df_map_box['SemanaDelAño'] = df_map_box['FECHA'].dt.isocalendar().week
        ultima_semana = int(df_map_box['SemanaDelAño'].max())
        semana_anterior = ultima_semana - 1

        count_semana_actual = 0
        count_semana_anterior = 0

        locations_semana_actual = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['SemanaDelAño'] == ultima_semana].values
        locations_semana_anterior = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['SemanaDelAño'] == semana_anterior].values

        for location in locations_semana_actual:
            if geodesic(new_location, location).km <= 2:
                count_semana_actual += 1

        for location in locations_semana_anterior:
            if geodesic(new_location, location).km <= 2:
                count_semana_anterior
        
        tupla_semana = count_semana_actual, count_mes_anterior

        # KPI DELITO PROMEDIO
        delito_promedio = df_map_box['TIPO_DELITO_DESC'].describe().top
        hechos_delito_promedio = int(df_map_box[df_map_box['TIPO_DELITO_DESC'] == df_map_box['TIPO_DELITO_DESC'].describe().top]['CONTACTO_ID'].count())

        # TABLA CONTEXTUAL
        def idem_locatios(locations):
            from collections import Counter

            contador = Counter(map(tuple,locations))

            repetidos = {location: count for location, count in contador.items() if count > 1}

            return repetidos

        def contextual_df(repetidos):
            lat = []
            lon = []
            hechos = []
            franja_horaria_promedio = []
            tipo_delito_moda = []

            for rep in repetidos.items():
                lat.append(rep[0][0])
                lon.append(rep[0][1])

                df_subset = df_map_box[(df_map_box['LATITUD'] == rep[0][0]) & (df_map_box['LONGITUD'] == rep[0][1])]

                hechos.append(rep[1])

                franja_horaria_promedio.append(df_subset['FRANJA_HORARIA'].mean())

                tipo_delito_moda.append(df_subset['TIPO_DELITO_DESC'].mode()[0])

            dict_data = {
                'LATITUD': lat,
                'LONGITUD': lon,
                'HECHOS': hechos,
                'FRANJA_HORARIA_PROMEDIO': franja_horaria_promedio,
                'TIPO_DELITO_MAS_FRECUENTE': tipo_delito_moda
                    }
            df_locations = pd.DataFrame(dict_data).sort_values(by='HECHOS', ascending=False).head(5)

            geolocator = Nominatim(user_agent="AppCrimeStreamlit")
            direcciones = []
            for i, row in df_locations.iterrows():
                try:
                    direccion = geolocator.reverse(
                            (row['LATITUD'], row['LONGITUD']),
                            exactly_one=True,
                            language='es'
                        ).raw['address']
                        
                    if 'house_number' in direccion and 'road' in direccion:
                            direcciones.append(f"{direccion['road']} {direccion['house_number']}")
                    elif 'tourism' in direccion and 'road' in direccion:
                            direcciones.append(f"{direccion['tourism']} {direccion['road']}")
                    elif 'road' in direccion:
                            direcciones.append(direccion['road'])
                    else:
                            direcciones.append("Dirección no disponible")
                except Exception as e:
                    print(f"Error con la ubicación {row['LATITUD']}, {row['LONGITUD']}: {e}")
                    direcciones.append("Error en geolocalización")

            df_locations['Direcciones'] = direcciones
            df_locations = df_locations.rename(columns={'HECHOS':'Hechos',
                                                                'FRANJA_HORARIA_PROMEDIO':'Franja horaria promedio',
                                                                'TIPO_DELITO_MAS_FRECUENTE':'Delito más frecuente'})
            return df_locations[['Direcciones', 'Franja horaria promedio', 'Delito más frecuente', 'Hechos']]
            
        df_locations = contextual_df(repetidos=idem_locatios(locations=df_map_box[['LATITUD','LONGITUD']][df_map_box['MES'] == datetime.now().month].values))

        return df_map_box, tupla_mes, tupla_semana, delito_promedio, hechos_delito_promedio, df_locations