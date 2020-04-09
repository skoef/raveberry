from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


class ConnectionHandlerMixin:
    @classmethod
    def tearDownClass(cls):
        User.objects.create_superuser('admin', '', 'admin')

        client = Client()
        client.login(username='admin', password='admin')
        client.post(reverse('stop_player_loop'))
