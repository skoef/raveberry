import os

from django.http import HttpResponseBadRequest

from core.musiq import song_utils
from core.musiq.music_provider import SongProvider
from main import settings


class LocalSongProvider(SongProvider):
    """
    A class handling local files on the drive.
    If the library is at /home/pi/Music/ and SONGS_CACHE_DIR is at /home/pi/raveberry
    there will be a symlink /home/pi/raveberry/local_library to /home/pi/Music

    Example values for a file at /home/pi/Music/Artist/Title.mp3 are:
    id: Artist/Title.mp3
    external_url: local_library/Artist/Title.mp3
    internal_url: file:///home/pi/local_library/Artist/Title.mp3
    """

    @staticmethod
    def get_id_from_external_url(url):
        return url[len('local_library/'):]

    def __init__(self, musiq, query, key):
        super().__init__(musiq, query, key)
        self.type = 'local'

    def check_cached(self):
        return os.path.isfile(self.get_path())

    def check_downloadable(self):
        # Local files can not be downloaded from the internet
        self.error = 'Local file missing'
        return False

    def get_metadata(self):
        metadata = song_utils.get_metadata(self.get_path())

        metadata['internal_url'] = self.get_internal_url()
        metadata['external_url'] = self.get_external_url()
        if not metadata['title']:
            metadata['title'] = metadata['external_url']

        return metadata

    def get_path(self):
        path = os.path.join(settings.SONGS_CACHE_DIR, self.get_external_url())
        path = path.replace('~', os.environ['HOME'])
        path = os.path.abspath(path)
        return path

    def get_internal_url(self):
        return 'file://' + self.get_path()

    def get_external_url(self):
        return 'local_library/' + self.id

    def request_radio(self, ip):
        return HttpResponseBadRequest('No automatic suggestion for local files available (yet).')

