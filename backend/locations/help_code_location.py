import requests

from django.conf import settings
from .models import Location
from django.utils import timezone


def fetch_coordinates(address):
    try:
        base_url = "https://geocode-maps.yandex.ru/1.x"
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": settings.YANDEX_API_KEY,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    except requests.exceptions.HTTPError:
        return None

    return lon, lat


def adds_address(address):
    coordinates = fetch_coordinates(address)
    if coordinates:
        lon, lat = coordinates
        request_date = timezone.now()
    else:
        return False

    Location.objects.update_or_create(
        address=address,
        defaults={
            'lat': lat,
            'lon': lon,
            'request_date': request_date,
        }
    )

