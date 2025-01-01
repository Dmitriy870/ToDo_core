FROM python:3.12-slim


WORKDIR /app


COPY pyproject.toml poetry.lock /app/


RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi


COPY todocore /app

ENV PYTHONPATH "${PYTHONPATH}:/app/"


COPY entrypoint.sh /entrypoint.sh
COPY entrypoint_celery.sh /entrypoint_celery.sh
RUN chmod +x /entrypoint.sh /entrypoint_celery.sh


EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
