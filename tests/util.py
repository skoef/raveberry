from django.contrib.auth.models import User


def admin_login(client):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', '', 'admin')
    client.login(username='admin', password='admin')
