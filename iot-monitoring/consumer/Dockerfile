# Build context is the repo root (see docker-compose.yml) so the shared
# elasticsearch mapping file can be copied into the image.
FROM python:3.12-slim

WORKDIR /app

COPY consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer/app ./app
COPY consumer/mqtt_consumer.py .
COPY elasticsearch/init_index.json ./elasticsearch/init_index.json

ENV ELASTICSEARCH_MAPPING_PATH=/app/elasticsearch/init_index.json

CMD ["python", "mqtt_consumer.py"]
