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
    def __init__(self):
        self.scaler = scaler
        self.kmeans = kmeans
        self.hostname = "localhost"
        self.dbname = "crimewarehouse"
        self.uname = "root"
        self.pwd = "admin1234"

        self.engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=self.hostname, db=self.dbname, user=self.uname, pw=self.pwd))
    
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
    
    @st.cache_data
    def get_df_by_query(_self, query):
        db = _self.engine
        df = pd.read_sql(query, db)
        print("ejecutando query")

        return df
    
    @staticmethod
    @st.cache_data
    def get_data_table(_df):
        # Configuración local
        # DF Table data
        print("obteniendo tabla")
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
    
    def get_actual_location_table(self, lat, lon):
        # Localizacion actual
        df_data = self.get_current_location(lat, lon)
        comuna = df_data['Comuna'].values[0]
        comuna = comuna.upper()
        barrio = df_data['Barrio'].values[0]
        barrio = barrio.upper()
    
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

        return df_tabla