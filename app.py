from flask import Flask, render_template, request, redirect, url_for
import folium
from pymongo import MongoClient
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
import os

app = Flask(__name__)

# Configuration de MongoDB
mongo_uri = "mongodb://localhost:27017/"  # Modifie ceci si nécessaire
client = MongoClient(mongo_uri)
db = client["VelibDB"]
collection = db["VelibTempsReel"]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        address = request.form['address']
        return redirect(url_for('map', address=address))
    return render_template('index.html')

@app.route('/map')
def map():
    address = request.args.get('address')

    # Obtenir les coordonnées de l'adresse
    geolocator = Nominatim(user_agent="velib_locator")
    location = geolocator.geocode(address)

    if not location:
        return "Adresse non trouvée.", 404

    address_coordinates = (location.latitude, location.longitude)

    # Créer une carte centrée sur l'adresse saisie
    map_address = folium.Map(location=address_coordinates, zoom_start=14)

    # Ajouter un marqueur pour l'adresse saisie en rouge
    folium.Marker(
        location=address_coordinates,
        popup=f"Adresse : {address}",
        icon=folium.Icon(color='red')
    ).add_to(map_address)

    # Récupérer les données de la collection
    stations = collection.find()
    nearby_stations = []

    # Vérifier la distance de chaque station
    for station in stations:
        name = station['name']
        lat = station['coordonnees_geo']['lat']
        lon = station['coordonnees_geo']['lon']
        num_bikes = station['numbikesavailable']
        station_coordinates = (lat, lon)

        # Calculer la distance
        distance = great_circle(address_coordinates, station_coordinates).meters

        if distance <= 500:  # Si la station est à moins de 500 mètres
            nearby_stations.append((name, lat, lon, num_bikes, distance))
            folium.Marker(
                location=station_coordinates,
                popup=f"{name} - Vélos disponibles: {num_bikes} - Distance: {distance:.2f} m",
                icon=folium.Icon(color='green')
            ).add_to(map_address)

    # Enregistrer la carte dans un fichier HTML
    map_file = 'templates/map.html'
    map_address.save(map_file)

    return render_template('map.html', nearby_stations=nearby_stations, address=address)

if __name__ == '__main__':
    app.run(debug=True)
