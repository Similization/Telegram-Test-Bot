from typing import List

from aiogram.dispatcher.filters.state import State, StatesGroup
from yandex_music import ClientAsync, Status, Playlist


class YAMState(StatesGroup):
    playlist_list = State()
    playlist_current = State()
    track_current = State()


class YandexMusicAsyncClient:
    def __init__(self, token: str):
        self.client = ClientAsync(token=token)

    async def create(self):
        await self.client.init()

    async def get_status(self) -> Status:
        return self.client.me

    async def get_playlists(self) -> List[Playlist]:
        return await self.client.users_playlists_list()
