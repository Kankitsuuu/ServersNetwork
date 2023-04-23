import os
import requests
import socket
from geopy.distance import geodesic

api_key = os.getenv('ABSTRACT_API_KEY')


# Need to change API key to environ variable
def get_location(ip_address: str = None):
    try:
        url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={api_key}'
        if ip_address:
            url += f'&ip_address={ip_address}'
        response = requests.get(url)
        data = response.json()
    except Exception as e:
        print(e)
        return
    return data['latitude'], data['longitude']


def get_location_by_url(url: str):
    try:
        response = requests.head(url)
        print(response.status_code)
        hostname = url.split(response.request.path_url)[0].split('//')[1]
        address = socket.gethostbyname(hostname)
        print(hostname, address)
        return get_location(address)
    except Exception as e:
        print(e)
        return


def get_local_data():
    try:
        url = f'https://ipgeolocation.abstractapi.com/v1/?api_key={api_key}'
        response = requests.get(url)
    except Exception as e:
        print(e)
        return
    return response.json()


def get_distance(location_1: tuple, location_2: tuple):
    return geodesic(location_1, location_2).km


