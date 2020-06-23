FROM raveberry/raveberry-dependencies

RUN pip install psycopg2 &&\
	pip install -U youtube-dl &&\
	pip install raveberry --no-deps --target /opt &&\
	rm -rf ~/.cache/pip

EXPOSE 9000

COPY entrypoint.sh /entrypoint.sh
# disabled EmbedThumbnail in youtube
COPY youtube.py /opt/raveberry/core/musiq/youtube.py

WORKDIR /opt/raveberry

ENTRYPOINT ["/entrypoint.sh"]
