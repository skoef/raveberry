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

    def setUp(self):
        super().setUp()
        self._setup_test_library()

    def test_suggested_song(self):
        suggestion = json.loads(self.client.get(reverse('suggestions'), {'term': 'sk8board', 'playlist': 'false'}).content)[0]
        self.client.post(reverse('request_music'), {'key': suggestion['key'], 'query': '', 'playlist': 'false', 'platform': 'local'})
        state = self._poll_musiq_state(lambda state: state['current_song'], timeout=1)
        current_song = state['current_song']
        self.assertEqual(current_song['external_url'], 'local_library/Techno/Sk8board.mp3')
        self.assertEqual(current_song['artist'], 'AUDIONAUTIX.COM')
        self.assertEqual(current_song['title'], 'SK8BOARD')
        self.assertEqual(current_song['duration'], 126)

    def test_suggested_playlist(self):
        state = self._add_local_playlist()
        self.assertEqual(state['current_song']['external_url'], 'local_library/Hard Rock/ChecksForFree.mp3')
        self.assertEqual(state['song_queue'][0]['external_url'], 'local_library/Hard Rock/HeavyAction.mp3')
        self.assertEqual(state['song_queue'][1]['external_url'], 'local_library/Hard Rock/HiFiBrutality.mp3')
        self.assertEqual(state['song_queue'][2]['external_url'], 'local_library/Hard Rock/LongLiveDeath.mp3')
