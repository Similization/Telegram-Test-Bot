import json
from typing import Optional

import geocoder

import requests
from requests import Response


def get_country_location(
    city: str, token: str, country_code: Optional[str] = None
) -> (str, str):
    if country_code is None:
        url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={token}"
    else:
        url = f"https://api.openweathermap.org/geo/1.0/direct?q={city},{country_code}&limit=1&appid={token}"
    req_city_location: Response = requests.get(url=url)
    city_location_data: dict = json.loads(req_city_location.text)[0]
    return city_location_data["lat"], city_location_data["lon"]


def get_latitude_and_longitude(
    city: str, token: str, country_code: Optional[str] = None
) -> (str, str):
    if city is None:
        data = geocoder.ip("me")
        return data.latlng
    else:
        return get_country_location(city=city, country_code=country_code, token=token)


def get_weather(
    token: str, city: Optional[str] = None, country_code: Optional[str] = None
) -> dict:
    lat, lon = get_latitude_and_longitude(
        city=city, country_code=country_code, token=token
    )
    result = requests.get(
        url=f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={token}&units=metric"
    )
    return json.loads(result.text)


# need to change openweathermap tariff to make this function workable
def get_weather_for(
    city: str, country_code: str, token: str, days_count: int = 1
) -> dict:
    lat, lon = get_latitude_and_longitude(
        city=city, country_code=country_code, token=token
    )
    result = requests.get(
        url=f"api.openweathermap.org/data/2.5/forecast/daily?"
        f"lat={lat}&lon={lon}&cnt={days_count}&appid={token}&units=metric"
    )
    return json.loads(result.text)


def yandex_get_current_weather(city: str, country_code: str, token: str, y_token: str):
    lat, lon = get_country_location(city=city, country_code=country_code, token=token)
    resp_loc = requests.get(
        url=f"https://api.weather.yandex.ru/v2/informers?lat={lat}&lon={lon}",
        headers={"X-Yandex-API-Key": f"{y_token}"},
    )
    return json.loads(resp_loc.text)
