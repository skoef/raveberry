#!/bin/bash

set -e

DJANGO_MOCK=1 python manage.py compilescss
DJANGO_MOCK=1 python manage.py migrate --noinput
scripts/create_users.sh

if [ -d /opt/raveberry/static-copy ]; then
    echo -n "Copying static files ... "
    cp -a /opt/raveberry/static/* /opt/raveberry/static-copy/
    echo "done"
fi

exec "${@}"
