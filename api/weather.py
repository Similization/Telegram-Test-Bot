import json
from typing import Optional, Tuple

import geocoder

import requests
from requests import Response


def get_country_location(
    city: str, token: str, country_code: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    if country_code is None or country_code == "":
        url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={token}"
    else:
        url = f"https://api.openweathermap.org/geo/1.0/direct?q={city},{country_code}&limit=1&appid={token}"
    req_city_location: Response = requests.get(url=url)
    if len(req_city_location.text) == 0 or req_city_location.status_code != 200:
        return None
    city_location_data: dict = json.loads(req_city_location.text)[0]
    return city_location_data["lat"], city_location_data["lon"]


def get_latitude_and_longitude(
    token: str, city: Optional[str] = None, country_code: Optional[str] = None
) -> Optional[Tuple[str, str]]:
    if city is None or city == "":
        data = geocoder.ip("me")
        return data.latlng
    return get_country_location(city=city, country_code=country_code, token=token)


def get_weather(
    token: str, city: Optional[str] = None, country_code: Optional[str] = None
) -> Optional[dict]:
    optional_latitude_and_longitude = get_latitude_and_longitude(
        city=city, country_code=country_code, token=token
    )
    if optional_latitude_and_longitude is None:
        return None
    lat, lon = optional_latitude_and_longitude
    result = requests.get(
        url=f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={token}&units=metric"
    )
    return json.loads(result.text)


# need to change openweathermap tariff to make this function workable
def get_weather_for(
    city: str, country_code: str, token: str, days_count: int = 1
) -> Optional[dict]:
    optional_latitude_and_longitude = get_latitude_and_longitude(
        city=city, country_code=country_code, token=token
    )
    if optional_latitude_and_longitude is None:
        return None
    lat, lon = optional_latitude_and_longitude
    result = requests.get(
        url=f"api.openweathermap.org/data/2.5/forecast/daily?"
        f"lat={lat}&lon={lon}&cnt={days_count}&appid={token}&units=metric"
    )
    return json.loads(result.text)
