import os
from typing import List, Optional

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
        try:
            open(file=path_to_track, mode="a+")
            return True
        except OSError:
            return False

    @staticmethod
    def __create_directory(path_to_file: str):
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

    def get_from_now_part_by_title(self, title: str) -> Optional[Playlist | Track]:
        # list[playlist] | playlist
        music_list = self.__now
        if type(self.__now) is Playlist:
            music_list = self.get_tracks_from_playlist(playlist=self.__now)
        return self.get_music_by_title(
            music_list=self.get_part(music_list=music_list),
            title=title
        )

    def __queue_is_empty(self):
        return len(self.__queue) == 0

    def next_page(self):
        """
        Set current page to the next page, if it less than page count.
        """
        if self.__queue_is_empty():
            return
        page_count = (len(self.__queue[-1]) + self.__count - 1) // self.__count
        if page_count > self.__page:
            self.__page += 1

    def previous_page(self):
        """
        Set current page to the previous page, if it bigger than 1.
        """
        if self.__page > 1:
            self.__page -= 1

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

    def get_now(self) -> Optional[List[Playlist] | Playlist | List[Track]]:
        return self.__now

    def __download_track(
            self,
            track: Track, path_to_music_directory: str = "music/",
            path_to_track: str = "tracks/"
    ):
        """
        Download 1 track to chosen path.
        """
        track_title = f"{track.title} - {self.get_artists_name_from_track(track=track)}.mp3"
        full_track_path = path_to_music_directory + path_to_track + track_title
        if self.__is_track_exist(path_to_track=full_track_path):
            return
        self.__create_directory(path_to_file=path_to_music_directory + path_to_track)
        track.download(f'{full_track_path}')

    def __download_playlist(self, playlist: Playlist):
        """
        Download all tracks from playlist to chosen path.
        """
        playlist_tracks = self.get_full_tracks(playlist.fetch_tracks())
        for track in playlist_tracks:
            self.__download_track(track=track, path_to_track=f"{playlist.title}/")

    def download(self, music: List | Playlist | Track):
        """
        Download music.
        """
        if type(music) is list:
            for music_one in music:
                self.download(music=music_one)
        if type(music) is Playlist:
            self.__download_playlist(playlist=music)
        else:
            self.__download_track(track=music)

    def set_state(self, state: YAMState):
        self.__state = state

    def get_state(self) -> Optional[YAMState]:
        return self.__state

    def get_part(self, music_list: List[Playlist | Track]) -> List:
        """
        Get part of current object.
        Starts from self.__page and takes self.__count elements
        """
        return music_list[self.__page - 1: self.__page * self.__count]

    def get_client_playlist_list(self) -> List[Playlist]:
        return self.__client.users_playlists_list()

    def get_tracks_from_playlist(self, playlist: Playlist) -> Optional[List[Track]]:
        short_track_list = playlist.fetch_tracks()
        return self.get_full_tracks(short_track_list=short_track_list)
