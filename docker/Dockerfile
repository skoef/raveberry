FROM raveberry/raveberry-dependencies

RUN pip install psycopg2 &&\
	pip install -U youtube-dl &&\
	pip install raveberry --no-deps --target /opt &&\
	pip install https://github.com/DarwinAwardWinner/rganalysis/archive/master.zip &&\
	ln -s /usr/lib/python3/dist-packages/audiotools /usr/local/lib/python3.7/site-packages/ && \
	rm -rf ~/.cache/pip

EXPOSE 9000

COPY docker/entrypoint.sh /entrypoint.sh
# disabled EmbedThumbnail in youtube
COPY core/musiq/youtube.py /opt/raveberry/core/musiq/youtube.py
# override some settings logic
COPY main/settings.py /opt/raveberry/main/settings.py
# enable serving static files from django
COPY core/urls.py /opt/raveberry/core/urls.py
COPY static /opt/raveberry/static

WORKDIR /opt/raveberry

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/local/bin/daphne", "--bind", "0.0.0.0", "--port", "9000", "main.asgi:application"]
