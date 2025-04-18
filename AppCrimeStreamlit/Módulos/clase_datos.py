# DATOS & TIEMPO
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# STREAMLIT
import streamlit as st

# MODELADO
from joblib import load

# LOCALIZACION
from geopy import Nominatim
from geopy.distance import geodesic
from collections import Counter

# BASE DE DATOS
from sqlalchemy import create_engine, text
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

# RECURSOS DE CACHE
@st.cache_resource()
def load_models():
    kmeans = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/kmeans.joblib')
    scaler_kmeans = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/scaler.joblib')
    scaler_d_tree = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/scaler_d_tree.joblib')
    d_tree_model = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/d_tree_reg.joblib')
    return kmeans, scaler_kmeans, scaler_d_tree, d_tree_model
        
class Datos:
    ### SQL & ML
    def __init__(self, kmeans, scaler_kmeans, scaler_d_tree, d_tree_model):
        self.scaler = scaler_kmeans
        self.kmeans = kmeans
        self.scaler_d_tree = scaler_d_tree
        self.d_tree_model = d_tree_model
        self.hostname = "localhost"
        self.dbname = "crimewarehouse"
        self.uname = "root"
        self.pwd = "admin1234"

        self.engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=self.hostname, db=self.dbname, user=self.uname, pw=self.pwd))
            
    def engine_mysql(self):
        engine = create_engine(
            'mysql+pymysql://',
            connect_args = {
                'user': self.uname,
                'password': self.pwd, 
                'host': self.hostname,
                'db':self.dbname},
            isolation_level="READ COMMITTED"
            )
        return engine
        
    @contextmanager
    def db_session(self):
        engine = self.engine_mysql()
        Session = sessionmaker(bind = engine)
        session = Session()
        try:
            print("🟢 Sesión de base de datos establecida...")
            yield session
        except Exception as e:
            session.rollback() 
            raise e
        finally:
            print("🔴 Cerrando sesión de base de datos...")
            session.close() 
    
    ### DATOS DE SELECCION DE DATOS E INFORMACION
    @st.cache_data()
    def get_contextual_time_series(_self):
        query = text("""
        SELECT
        FECHA
        FROM
        FCT_HECHOS
        WHERE YEAR(FECHA) = (SELECT MAX(YEAR(FECHA)) FROM FCT_HECHOS)
        """)

        with _self.db_session() as connection:
            result = connection.execute(query)
            datos = result.fetchall()
        
        df = pd.DataFrame(datos)

        df['FECHA'] = pd.to_datetime(df['FECHA'])

        df['mes_desc'] = df['FECHA'].dt.month_name(locale='es')
        df['mes'] = df['FECHA'].dt.month

        mes_actual = int(df['mes'].max())
        if mes_actual == 1:
            mes_anterior = 12
        else:
            mes_anterior = mes_actual - 1

        df = df[df['mes'].isin((mes_actual, mes_anterior))].sort_values(by='FECHA', ascending=False)

        fecha_min = df['FECHA'].dt.strftime("%Y-%m-%d").min()
        fecha_max = df['FECHA'].dt.strftime("%Y-%m-%d").max()
        mes_actual = df['mes_desc'].head(1).values[0]
        mes_anterior = df['mes_desc'].tail(1).values[0]
        año = df['FECHA'].dt.year.unique()[0]

        return año, mes_actual, mes_anterior, fecha_min, fecha_max
    
    @st.cache_data()
    def get_contextual_crimes(_self):
        query = text("""
                SELECT
                TIPO_DELITO_DESC
                FROM
                DIM_TIPO_DELITO""")
        
        with _self.db_session() as connection:
            result = connection.execute(query)
            datos = result.fetchall()

        lista_delitos = pd.DataFrame(datos)
        lista_delitos = lista_delitos['TIPO_DELITO_DESC'].unique()
        
        return lista_delitos

    ### DATOS DASHBOARD
    def get_current_location(self, lat, lon, hora):
        zonas_peligro = pd.read_csv("C:/Users/20391117579/Dropbox/CrimeApp/Datasets/Zona peligro/zona_puntaje.csv")
        geolocator = Nominatim(user_agent="AppCrimeStreamlit")
        location = geolocator.reverse((lat, lon), exactly_one=True, language='es')
        direccion = location.raw['address']

        # BARRIO
        barrio = direccion.get("suburb", "Sin definir")

        # COMUNA
        comuna = direccion.get("state_district", "Sin definir")

        # FECHA
        hoy = datetime.now(tz=pytz.timezone('America/Argentina/Buenos_Aires')).strftime("%d-%m-%Y, %H")
        hoy = pd.to_datetime(hoy, format="%d-%m-%Y, %H")
        fecha = hoy.date()

        # FRANJA HORARIA
        franja_horaria = hora

        # ZONA
        coordenadas = [[lat, lon]]
        x_scaled = self.scaler.transform(coordenadas)

        # DATA DICT
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
        pd.set_option('future.no_silent_downcasting', True)
        
        df = df_data.rename(columns={'Fecha':'FECHA','Franja Horaria':'FRANJA_HORARIA',
                                     'Comuna':'COMUNA_NUM','Barrio':'BARRIO_NUM',
                                     'Zona':'ZONA','ZonaPeligroIndice':'ZONA_PELIGRO_INDICE'})
        # SERIE TEMPORAL
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

        # LOCALIZACION
        df['COMUNA_NUM'] = df['COMUNA_NUM'].apply(lambda x: 
                                                    1 if x == 'Comuna 1' else 
                                                    2 if x == 'Comuna 2' else 
                                                    3 if x == 'Comuna 3' else 
                                                    4 if x == 'Comuna 4' else 
                                                    5 if x == 'Comuna 5' else 
                                                    6 if x == 'Comuna 6' else 
                                                    7 if x == 'Comuna 7' else 
                                                    8 if x == 'Comuna 8' else 
                                                    9 if x == 'Comuna 9' else 
                                                    10 if x == 'Comuna 10' else 
                                                    11 if x == 'Comuna 11' else 
                                                    12 if x == 'Comuna 12' else 
                                                    13 if x == 'Comuna 13' else 
                                                    14 if x == 'Comuna 14' else 
                                                    15 if x == 'Comuna 15' else None)

        barrio_dict = {
            'Retiro': 1, 'San Nicolas': 2, 'Puerto Madero': 3, 'San Telmo': 4, 'Monserrat': 5, 'Constitucion': 6,
            'Recoleta': 7, 'Balvanera': 8, 'San Cristobal': 9, 'Boca': 10, 'Barracas': 11, 'Parque Patricios': 12, 
            'Nueva Pompeya': 13, 'Almagro': 14, 'Boedo': 15, 'Caballito': 16, 'Flores': 17, 'Parque Chacabuco': 18,
            'Villa Soldati': 19, 'Villa Riachuelo': 20, 'Villa Lugano': 21, 'Liniers': 22, 'Mataderos': 23, 
            'Parque Avellaneda': 24, 'Villa Real': 25, 'Monte Castro': 26, 'Versalles': 27, 'Floresta': 28, 
            'Velez Sarsfield': 29, 'Villa Luro': 30, 'Villa Devoto': 31, 'Villa Del Parque': 32, 'Villa Santa Rita': 33, 
            'Villa Gral. Mitre': 34, 'Coghlan': 35, 'Saavedra': 36, 'Villa Urquiza': 37, 'Villa Pueyrredon': 38, 
            'Nuñez': 39, 'Belgrano': 40, 'Colegiales': 41, 'Palermo': 42, 'Chacarita': 43, 'Villa Crespo': 44, 
            'Paternal': 45, 'Villa Ortuzar': 46, 'Agronomia': 47, 'Parque Chas': 48
        }
        df['BARRIO_NUM'] = df['BARRIO_NUM'].map(barrio_dict)

        # ESCALADO DE DATOS Y PREDICCION
        df = df[['ESTACION', 'TRIMESTRE', 'MES', 'SEMANA_DEL_AÑO', 'DIA_DEL_AÑO', 'DIA_DEL_MES', 'ES_FIN_DE_SEMANA', 'DIA_DE_LA_SEMANA', 'HORARIO_CATEGORIZADO', 'FRANJA_HORARIA', 'ZONA', 'ZONA_PELIGRO_INDICE', 'COMUNA_NUM', 'BARRIO_NUM']]
        df_scaled = self.scaler_d_tree.transform(df)
        peligrosidad = round(float(self.d_tree_model.predict(df_scaled)) * 100)

        return peligrosidad
    
    def get_location_data(self, lat, lon, hora):
        # Localizacion actual
        df_data = self.get_current_location(lat, lon, hora)
        # Peligrosidad 
        peligrosidad = self.get_hazard_index(df_data)
        # Datos
        comuna = df_data['Comuna'].values[0]
        comuna = comuna.upper()
        barrio = df_data['Barrio'].values[0]
        barrio = barrio.upper()

        return comuna, barrio, peligrosidad
    
    def get_dashboard_data(self, _lat, _lon, comuna, barrio, hora):
        # TODA LA INFORMACION DE ESTE DASHBOARD CORRESPONDE A LOS DELITOS DE LOS ULTIMOS TRES MESES
        # SI HAY HORA REALIZAMOS ESTE FILTRO
        if hora:
            new_location = _lat, _lon
            query = text("""
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
                    AND dimb.BARRIO_DESC = :barrio
                    AND dimc.COMUNA_DESC = :comuna
                GROUP BY
                fct.FECHA, fct.FRANJA_HORARIA, fct.LATITUD, fct.LONGITUD, dimb.BARRIO_DESC, dtd.TIPO_DELITO_DESC ,fct.CONTACTO_ID
                ORDER BY
                FECHA;
                """)
            with self.db_session() as connection:
                result = connection.execute(query, {'barrio':barrio, 'comuna':comuna})
                datos = result.fetchall()

            df_map_box = pd.DataFrame(datos)

            # TRANSFORMACIONES
            df_map_box['FECHA'] = pd.to_datetime(df_map_box['FECHA'])
            df_map_box['MES'] = df_map_box['FECHA'].dt.month
            df_map_box['HORA'] = df_map_box['FECHA'].dt.hour

            # ULTIMOS TRES MESES
            mes_actual = datetime.now().month
            if mes_actual == 1:
                mes_anterior = 12
                mes_anteroposterior = mes_anterior - 1
            else:
                mes_anterior = mes_actual - 1
                mes_anteroposterior = mes_anterior - 1

            df_map_box = df_map_box[df_map_box['MES'].isin((mes_actual, mes_anterior, mes_anteroposterior))]
            df_map_box = df_map_box[df_map_box['FRANJA_HORARIA'] == hora]

            # KPI HECHOS MES ACTUAL VS MES ANTERIOR EN RADIO DE 1 KM
            count_mes_actual = 0
            count_mes_anterior = 0
            locations_mes_actual = df_map_box[df_map_box['MES'] == mes_actual][['LATITUD', 'LONGITUD']].values
            locations_mes_anterior = df_map_box[df_map_box['MES'] == mes_anterior][['LATITUD', 'LONGITUD']].values

            for location in locations_mes_actual:
                if geodesic(new_location, location).km <= 1.5:
                    count_mes_actual += 1

            for location in locations_mes_anterior:
                if geodesic(new_location, location).km <= 1.5:
                    count_mes_anterior += 1
            
            tupla_mes = count_mes_actual, count_mes_anterior

            # KPI SEMANA ACTUAL VS SEMANA ANTERIOR RADIO 1 KM
            df_map_box['SemanaDelAño'] = df_map_box['FECHA'].dt.isocalendar().week
            ultima_semana = int(df_map_box['SemanaDelAño'].max())
            semana_anterior = ultima_semana - 1

            count_semana_actual = 0
            count_semana_anterior = 0

            locations_semana_actual = df_map_box[df_map_box['SemanaDelAño'] == ultima_semana][['LATITUD', 'LONGITUD']].values
            locations_semana_anterior = df_map_box[df_map_box['SemanaDelAño'] == semana_anterior][['LATITUD', 'LONGITUD']].values

            for location in locations_semana_actual:
                if geodesic(new_location, location).km <= 1.5:
                    count_semana_actual += 1

            for location in locations_semana_anterior:
                if geodesic(new_location, location).km <= 1.5:
                    count_semana_anterior += 1
            
            tupla_semana = count_semana_actual, count_semana_anterior

            # KPI DELITO PROMEDIO
            delito_promedio = df_map_box['TIPO_DELITO_DESC'].describe().top
            hechos_delito_promedio = int(df_map_box[df_map_box['TIPO_DELITO_DESC'] == df_map_box['TIPO_DELITO_DESC'].describe().top]['CONTACTO_ID'].count())

            # TABLA CONTEXTUAL - ES EL OBJETO VISUAL QUE ESTA FILTRADO LOCALIZACION Y HORA SELECCIONADA
            def idem_locations(locations):
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

                    tipo_delito_moda.append(df_subset['TIPO_DELITO_DESC'].mode()[0])

                dict_data = {
                    'LATITUD': lat,
                    'LONGITUD': lon,
                    'HECHOS': hechos,
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
                                                            'TIPO_DELITO_MAS_FRECUENTE':'Delito más frecuente'})
                return df_locations[['Direcciones', 'Delito más frecuente', 'Hechos']]
             
            df_locations = contextual_df(repetidos=idem_locations(locations=df_map_box[['LATITUD','LONGITUD']].values))
            
            return df_map_box, tupla_mes, tupla_semana, delito_promedio, hechos_delito_promedio, df_locations
        
        # SINO EJECUTAMOS CON LA LOCALIZACION DEL MAPA
        else:
            new_location = _lat, _lon
            query = text("""
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
                """)
            
            with self.db_session() as connection:
                result = connection.execute(query, {'barrio':barrio, 'comuna':comuna})
                datos = result.fetchall()

            df_map_box = pd.DataFrame(datos)

            # KPI HECHOS MES ACTUAL VS ANTERIOR EN RADIO DE 1 KM
            df_map_box['FECHA'] = pd.to_datetime(df_map_box['FECHA'])
            df_map_box['MES'] = df_map_box['FECHA'].dt.month

            # ULTIMOS TRES MESES
            mes_actual = datetime.now().month
            if mes_actual == 1:
                mes_anterior = 12
                mes_anteroposterior = mes_anterior - 1
            else:
                mes_anterior = mes_actual - 1
                mes_anteroposterior = mes_anterior - 1

            df_map_box = df_map_box[df_map_box['MES'].isin((mes_actual, mes_anterior, mes_anteroposterior))]

            count_mes_actual = 0
            count_mes_anterior = 0
            locations_mes_actual = df_map_box[df_map_box['MES'] == mes_actual][['LATITUD', 'LONGITUD']].values
            locations_mes_anterior = df_map_box[df_map_box['MES'] == mes_anterior][['LATITUD', 'LONGITUD']].values

            for location in locations_mes_actual:
                if geodesic(new_location, location).km <= 1:
                    count_mes_actual += 1

            for location in locations_mes_anterior:
                if geodesic(new_location, location).km <= 1:
                    count_mes_anterior += 1
            
            tupla_mes = count_mes_actual, count_mes_anterior

            # KPI SEMANA ACTUAL VS SEMANA ANTERIOR RADIO 1 KM
            df_map_box['SemanaDelAño'] = df_map_box['FECHA'].dt.isocalendar().week
            ultima_semana = int(df_map_box['SemanaDelAño'].max())
            semana_anterior = ultima_semana - 1

            count_semana_actual = 0
            count_semana_anterior = 0

            locations_semana_actual = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['SemanaDelAño'] == ultima_semana].values
            locations_semana_anterior = df_map_box[['LATITUD', 'LONGITUD']][df_map_box['SemanaDelAño'] == semana_anterior].values

            for location in locations_semana_actual:
                if geodesic(new_location, location).km <= 1:
                    count_semana_actual += 1

            for location in locations_semana_anterior:
                if geodesic(new_location, location).km <= 1:
                    count_semana_anterior
            
            tupla_semana = count_semana_actual, count_mes_anterior

            # KPI DELITO PROMEDIO
            delito_promedio = df_map_box['TIPO_DELITO_DESC'].describe().top
            hechos_delito_promedio = int(df_map_box[df_map_box['TIPO_DELITO_DESC'] == df_map_box['TIPO_DELITO_DESC'].describe().top]['CONTACTO_ID'].count())

            # TABLA CONTEXTUAL
            def idem_locatios(locations):
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
        
    ### DATOS ESTADÍSTICA
    # 1 - OBTENEMOS TODOS LOS DATOS
    # 2 - GENERAMOS UN FILTRO
    # 3 - LUEGO CREAMOS LOS DATOS DE CADA TARJETA
    @st.cache_data()
    def get_all_data(_self):
        query = text("""
                    SELECT
                        fct.FECHA,
                        fct.FRANJA_HORARIA,
                        fct.CONTACTO_ID,
                        dimc.COMUNA_DESC,
                        dimb.BARRIO_DESC,
                        dtd.TIPO_DELITO_DESC
                    FROM
                        FCT_HECHOS fct
                    INNER JOIN
                        DIM_COMUNAS dimc
                    ON fct.COMUNA_KEY = dimc.COMUNA_KEY
                    INNER JOIN
                        DIM_BARRIOS dimb
                    ON fct.BARRIO_KEY = dimb.BARRIO_KEY
                    INNER JOIN
                        DIM_TIPO_DELITO dtd
                    ON fct.TIPO_DELITO_KEY = dtd.TIPO_DELITO_KEY
                    """)
        try:
            with _self.db_session() as connection:
                result = connection.execute(query)
                data = result.fetchall()

            df_data = pd.DataFrame(data)

            ## TRANSFORMACIONES
            df_data['FECHA'] = pd.to_datetime(df_data['FECHA'])
            df_data['AÑO'] = df_data['FECHA'].dt.year
            df_data['MES_NUM'] = df_data['FECHA'].dt.month
            df_data['MES'] = df_data['FECHA'].dt.month_name(locale='es')

            return df_data
        
        except Exception as e:
            print(f"Error al obtener consulta de datos general: {e}")

    
    def get_filtered_df(self, df_data, año, mes, comuna, barrio, delito, franja_horaria):
        try:
            hora_min = np.min(franja_horaria)
            hora_max = np.max(franja_horaria) + 1
            horarios = tuple(np.arange(start=hora_min, stop=hora_max, step=1))
            if df_data is not None and df_data.empty == False:
                df_filtered = df_data
                print("Fuente de datos correcta.")
                dict_filtro = {'AÑO':año, 'MES':mes, 'COMUNA':comuna, 'BARRIO':barrio, 'DELITO':delito, 'FRANJA_HORARIA':horarios}
                clean_dict = {k: dict_filtro[k] for k in dict_filtro if not pd.isna(dict_filtro[k])}
            else:
                print("Fuente de datos vacía o inexistente.")

            for i in clean_dict.items():
                if i[0] == 'AÑO':
                    df_filtered = df_filtered[df_filtered['AÑO'] == i[1]]
                elif i[0] == 'MES':
                    df_filtered = df_filtered[df_filtered['MES_NUM'] == i[1]]
                elif i[0] == 'COMUNA':
                    df_filtered = df_filtered[df_filtered['COMUNA_DESC'] == i[1]]
                elif i[0] == 'BARRIO':
                    df_filtered = df_filtered[df_filtered['BARRIO_DESC'] == i[1]]
                elif i[0] == 'DELITO':
                    df_filtered = df_filtered[df_filtered['TIPO_DELITO_DESC'] == i[1]]
                elif i[0] == 'FRANJA_HORARIA':
                    df_filtered = df_filtered[df_filtered['FRANJA_HORARIA'].isin(i[1])]

            return df_filtered

        except Exception as e:
            mensaje = f"Error al generar el filtro global de datos: {e}"
            return mensaje
        
    def get_stat_kpis(self, df_filtered):
        # CANTIDAD DE HECHOS
        hechos = df_filtered['CONTACTO_ID'].count()
        
        # DELITO MAS FRECUENTE
        delito_top = df_filtered.groupby('TIPO_DELITO_DESC')['CONTACTO_ID'].count().sort_values(ascending=False).head(1)

        # COMUNA CON MAS HECHOS
        comuna_top = df_filtered.groupby('COMUNA_DESC')['CONTACTO_ID'].count().sort_values(ascending=False).head(1)

        # BARRIO CON MAS HECHOS
        barrio_top = df_filtered.groupby('BARRIO_DESC')['CONTACTO_ID'].count().sort_values(ascending=False).head(1)

        return hechos, delito_top, comuna_top, barrio_top

    def get_stat_lines(self, df_filtered):
        # TRANSFORMACIONES
        df_filtered['PERIODO'] = df_filtered['FECHA'].dt.to_period('M')
        df_lines = df_filtered.groupby('PERIODO')['CONTACTO_ID'].count().reset_index()
        df_lines['PERIODO'] = df_lines['PERIODO'].dt.to_timestamp()

        return df_lines

    def get_stat_grilla(self):
        # GRILLA HORA/DIA
        pass

    def get_stat_bar_comuna(self):
        # BARRAS HECHOS POR COMUNA
        pass

    def get_stat_map(self):
        # HECHOS POR BARRIOS
        pass
        

