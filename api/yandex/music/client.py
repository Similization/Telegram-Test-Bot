from typing import List

from aiogram.dispatcher.filters.state import State, StatesGroup
from yandex_music import Client, Status, Playlist


class YAMState(StatesGroup):
    playlist_list = State()
    playlist_current = State()
    track_current = State()


class YandexMusicClient:
    def __init__(self, token: str):
        self.client = Client(token=token)
        self.client.init()

    def get_status(self) -> Status:
        return self.client.me

    def get_playlists(self) -> List[Playlist]:
        return self.client.users_playlists_list()
