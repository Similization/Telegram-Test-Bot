from typing import Optional

from aiogram import Bot

from api.yandex.music.client import YandexMusicClient


class ReprezzentBot(Bot):
    def __init__(self, token):
        super().__init__(token)
        self.yam_client: Optional[YandexMusicClient] = None

    def create_yandex_music_client(self, token: str):
        self.yam_client = YandexMusicClient(token=token)
