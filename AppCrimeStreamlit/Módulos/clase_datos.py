# DATOS & TIEMPO
import pandas as pd
from datetime import datetime
import pytz

# MODELADO
from joblib import load

# LOCALIZACION
from geopy import Nominatim

# KMEANS
kmeans = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/kmeans.joblib')
scaler = load('C:/Users/20391117579/Dropbox/CrimeApp/Data Science Lab/Modelos/scaler.joblib')

class Datos:
    def __init__(self):
        self.scaler = scaler
        self.kmeans = kmeans
    
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
    