import os
from pathlib import Path
from typing import List, Optional, Tuple

from aiogram.dispatcher.filters.state import State, StatesGroup
from yandex_music import Client, Playlist, Track, TrackShort


class YAMState(StatesGroup):
    start = State()
    playlist_list = State()
    playlist = State()
    track = State()


class YandexMusicClient:
    def __init__(self, token: str, music_count: int = 10):
        self.__client = Client(token=token)
        self.__client.init()
        self.__page: int = 1
        self.__state: Optional[YAMState] = None
        self.__count = music_count
        self.__queue: List[List[Playlist] | Playlist | List[Track]] = []
        self.__now: Optional[List[Playlist] | Playlist | List[Track]] = None

    @staticmethod
    def __is_track_exist(path_to_track: str) -> bool:
        p = Path(path_to_track)
        return p.exists()

    @staticmethod
    def __create_directory(path_to_file: str):
        p = Path(path_to_file)
        if p.exists():
            return
        os.makedirs(name=path_to_file, exist_ok=True)

    @staticmethod
    def get_full_tracks(short_track_list: List[TrackShort]) -> List[Track]:
        full_tracks: List[Track] = []
        for short_track in short_track_list:
            full_track = short_track.fetch_track()
            full_tracks.append(full_track)
        return full_tracks

    @staticmethod
    def get_music_by_title(
            music_list: List[Playlist | Track],
            title: str
    ) -> Optional[Playlist | Track]:
        for music in music_list:
            if music.title == title:
                return music
        return None

    @staticmethod
    def get_artists_name_from_track(track: Track) -> str:
        return ", ".join([artist.name for artist in track.artists])

    def __queue_is_empty(self):
        return len(self.__queue) == 0

    def get_music_list(self) -> List[Playlist] | List[Track]:
        if type(self.__now) is Playlist:
            return self.get_tracks_from_playlist(playlist=self.__now)
        else:
            return self.__now

    def next_page(self) -> bool:
        """
        Set current page to the next page, if it less than page count.
        """
        if not self.__queue_is_empty():
            music_list = self.get_music_list()
            page_count = (len(music_list) + self.__count - 1) // self.__count
            if page_count > self.__page:
                self.__page += 1
                return True
        return False

    def previous_page(self) -> bool:
        """
        Set current page to the previous page, if it bigger than 1.
        """
        if self.__page > 1:
            self.__page -= 1
            return True
        return False

    def set_to_default_page(self):
        self.__page = 1

    def get_part(self, music_list: List[Playlist | Track]) -> List:
        """
        Get part of current object.
        Starts from self.__page and takes self.__count elements
        """
        return music_list[(self.__page - 1) * self.__count: self.__page * self.__count]

    def get_now_part(self):
        return self.get_part(music_list=self.get_music_list())

    def get_now(self) -> Optional[List[Playlist] | Playlist | List[Track]]:
        return self.__now

    def put_to_queue(self, music: List[Playlist] | Playlist | List[Track]):
        if not self.__queue_is_empty() and self.__queue[-1] == music:
            return
        self.__queue.append(music)
        self.__now = self.__queue[-1]

    def remove_from_queue(self) -> Optional[List[Playlist] | Playlist | List[Track]]:
        if self.__queue_is_empty():
            return None

        removed_element = self.__queue.pop(-1)
        if self.__queue_is_empty():
            self.__now = None
        else:
            self.__now = self.__queue[-1]
        return removed_element

    def __download_track(
            self,
            track: Track, path_to_music_directory: str = "music/",
            path_to_track: str = "tracks/"
    ) -> str:
        """
        Download 1 track to chosen path.
        """
        track_title = f"{track.title} - {self.get_artists_name_from_track(track=track)}.mp3"
        full_track_path = path_to_music_directory + path_to_track + track_title
        if not self.__is_track_exist(path_to_track=full_track_path):
            self.__create_directory(path_to_file=path_to_music_directory + path_to_track)
            track.download(filename=f'{full_track_path}', codec='mp3', bitrate_in_kbps=192)
        return full_track_path

    def __download_playlist(self, playlist: Playlist):
        """
        Download all tracks from playlist to chosen path.
        """
        playlist_tracks = self.get_full_tracks(playlist.fetch_tracks())
        list_of_paths = []
        for track in playlist_tracks:
            full_track_path = self.__download_track(track=track, path_to_track=f"{playlist.title}/")
            list_of_paths.append(full_track_path)
        return tuple(list_of_paths)

    def download(self, music: Playlist | Track) -> Tuple[str] | str:
        """
        Download music.
        """
        # if type(music) is list:
        #     for music_one in music:
        #         self.download(music=music_one)
        if type(music) is Playlist:
            return self.__download_playlist(playlist=music)
        else:
            return self.__download_track(track=music)

    def set_state(self, state: YAMState):
        self.__state = state

    def get_state(self) -> Optional[YAMState]:
        return self.__state

    def get_client_playlist_list(self) -> List[Playlist]:
        return self.__client.users_playlists_list()

    def get_tracks_from_playlist(self, playlist: Playlist) -> Optional[List[Track]]:
        short_track_list = playlist.fetch_tracks()
        return self.get_full_tracks(short_track_list=short_track_list)
