import json
import os
import pathlib
import sys
import urllib.request

from django.conf import settings
from django.test import TransactionTestCase, Client
from django.urls import reverse

from tests import util
from tests.mixins import ConnectionHandlerMixin, MusicTestMixin


class LocaldriveTests(ConnectionHandlerMixin, MusicTestMixin, TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super(LocaldriveTests, cls).setUpClass()

    def setUp(self):
        super().setUp()
        util.download_test_library()

        test_library = os.path.join(os.path.join(settings.BASE_DIR, 'test_library'))
        self.client.post(reverse('scan_library'), {'library_path': test_library})
        # need to split the scan_progress as it contains no-break spaces
        self._poll_state('settings_state', lambda state: ' '.join(state['scan_progress'].split()) == '6 / 6 / 6')
        self.client.post(reverse('create_playlists'))
        self._poll_state('settings_state', lambda state: ' '.join(state['scan_progress'].split()) == '6 / 6 / 6')

    def test_suggested_song(self):
        suggestion = json.loads(self.client.get(reverse('suggestions'), {'term': 'sk8board', 'playlist': 'false'}).content)[0]
        self.client.post(reverse('request_music'), {'key': suggestion['key'], 'query': '', 'playlist': 'false', 'platform': 'local'})
        state = self._poll_musiq_state(lambda state: state['current_song'])
        current_song = state['current_song']
        self.assertEqual(current_song['external_url'], 'local_library/Techno/Sk8board.mp3')
        self.assertEqual(current_song['artist'], 'AUDIONAUTIX.COM')
        self.assertEqual(current_song['title'], 'SK8BOARD')
        self.assertEqual(current_song['duration'], 126)

    def test_suggested_playlist(self):
        suggestion = json.loads(self.client.get(reverse('suggestions'), {'term': 'hard rock', 'playlist': 'true'}).content)[0]
        self.client.post(reverse('request_music'), {'key': suggestion['key'], 'query': '', 'playlist': 'true', 'platform': 'local'})
        state = self._poll_musiq_state(lambda state: len(state['song_queue']) == 3 and all(song['confirmed'] for song in state['song_queue']))
        self.assertEqual(state['current_song']['external_url'], 'local_library/Hard Rock/ChecksForFree.mp3')
        self.assertEqual(state['song_queue'][0]['external_url'], 'local_library/Hard Rock/HeavyAction.mp3')
        self.assertEqual(state['song_queue'][1]['external_url'], 'local_library/Hard Rock/HiFiBrutality.mp3')
        self.assertEqual(state['song_queue'][2]['external_url'], 'local_library/Hard Rock/LongLiveDeath.mp3')
