import json
import time

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from tests import util


class ConnectionHandlerMixin:
    @classmethod
    def setUpClass(cls):
        client = Client()
        util.admin_login(client)

        client.post(reverse('start_player_loop'))
        
    @classmethod
    def tearDownClass(cls):
        client = Client()
        util.admin_login(client)

        client.post(reverse('stop_player_loop'))

class MusicTestMixin:

    def setUp(self):
        self.client = Client()
        util.admin_login(self.client)

        # reduce number of downloaded songs for the test
        self.client.post(reverse('set_max_playlist_items'), {'value': '5'})

    def tearDown(self):
        self.client.login(username='admin', password='admin')

        # restore player state
        self.client.post(reverse('set_autoplay'), {'value': 'false'})
        self._poll_musiq_state(lambda state: not state['autoplay'])

        # ensure that the player is not waiting for a song to finish
        self.client.post(reverse('remove_all'))
        self._poll_musiq_state(lambda state: len(state['song_queue']) == 0)
        self.client.post(reverse('skip_song'))
        self._poll_musiq_state(lambda state: not state['current_song'])

    def _poll_state(self, state_url, break_condition, timeout=10):
        timeout *= 10
        counter = 0
        while counter < timeout:
            state = json.loads(self.client.get(reverse(state_url)).content)
            if break_condition(state):
                break
            time.sleep(0.1)
            counter += 1
        else:
            self.fail('enqueue timeout')
        return state

    def _poll_musiq_state(self, break_condition, timeout=10):
        return self._poll_state('musiq_state', break_condition, timeout=timeout)

    def _poll_current_song(self):
        state = self._poll_musiq_state(lambda state: state['current_song'])
        current_song = state['current_song']
        return current_song

