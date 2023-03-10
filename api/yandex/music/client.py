from typing import List, Optional

from aiogram.dispatcher.filters.state import State, StatesGroup
from yandex_music import Client, Playlist, Track, TrackShort


class YAMState(StatesGroup):
    playlist_list = State()
    playlist_current = State()
    track_current = State()


class YandexMusicClient:
    def __init__(self, token: str):
        self.__client = Client(token=token)
        self.__client.init()
        self.__playlist_list_now: Optional[List[Playlist]] = None
        self.__playlist_now: Optional[Playlist] = None
        self.__track_list_now: Optional[List[Track]] = None

    @staticmethod
    def __get_full_tracks(short_track_list: List[TrackShort]) -> List[Track]:
        full_tracks: List[Track] = []
        for short_track in short_track_list:
            full_track = short_track.fetch_track()
            full_tracks.append(full_track)
        return full_tracks

    @staticmethod
    def get_artists_name_from_track(track: Track) -> str:
        return ", ".join([artist.name for artist in track.artists])

    def get_playlist_list(self) -> Optional[List[Playlist]]:
        self.__playlist_list_now = self.__client.users_playlists_list()
        return self.__playlist_list_now

    def get_playlist_by_title(self, title: str) -> Optional[Playlist]:
        for playlist in self.__playlist_list_now:
            if playlist.title == title:
                self.__playlist_now = playlist
                return self.__playlist_now
        return None

    def get_tracks_from_playlist(self) -> Optional[List[Track]]:
        if self.__playlist_now is None:
            return None
        short_track_list = self.__playlist_now.fetch_tracks()
        self.__track_list_now = self.__get_full_tracks(
            short_track_list=short_track_list
        )
        return self.__track_list_now

    def get_track_list(self) -> Optional[List[Track]]:
        return self.__track_list_now

    def get_track_by_title(self, title: str) -> Optional[Track]:
        for track in self.__track_list_now:
            if track.title == title:
                return track
        return None
