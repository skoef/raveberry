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
