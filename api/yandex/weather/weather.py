import requests
import json
from api.weather import get_country_location


def yandex_get_current_weather(city: str, country_code: str, token: str, y_token: str):
    lat, lon = get_country_location(city=city, country_code=country_code, token=token)
    resp_loc = requests.get(
        url=f"https://api.weather.yandex.ru/v2/informers?lat={lat}&lon={lon}",
        headers={"X-Yandex-API-Key": f"{y_token}"},
    )
    return json.loads(resp_loc.text)
