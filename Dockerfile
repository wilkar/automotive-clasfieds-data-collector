FROM python:3.11.2

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=1.3.1
ENV WORKDIR=/automotive-classfieds-data-collector

WORKDIR /automotive-classfieds-data-collector
RUN curl -sSL https://install.python-poetry.org | python \
    && ln -s ${POETRY_HOME}/bin/poetry /usr/local/bin/poetry \
    && poetry config virtualenvs.create false \
    && cp -r ~/.config/ /etc/skel/

COPY ./pyproject.toml ./poetry.lock $WORKDIR/
COPY ./ $WORKDIR/
RUN mkdir -p /var/log/app /var/data/app
RUN poetry install

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]