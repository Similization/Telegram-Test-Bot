from typing import Literal, List
from aiohttp.client_exceptions import ClientResponseError

from aiobalaboba import Balaboba


async def generate_trash(query: str, language: Literal["en", "ru"] = "en"):
    bb = Balaboba()
    text_types: List = await bb.get_text_types(language=language)
    try:
        response: str = await bb.balaboba(query=query, text_type=text_types[0])
        return response
    except ClientResponseError as e:
        return f"Some errors has occurred: {e.message}"
