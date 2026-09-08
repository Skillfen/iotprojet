"""Elasticsearch persistence layer for sensor readings."""

import json
import logging

from elasticsearch import Elasticsearch
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class ElasticsearchRepository:
    """Wraps Elasticsearch access: readiness check, index bootstrap, document writes."""

    def __init__(self, host: str, index: str, mapping_path: str):
        self._client = Elasticsearch(host)
        self._index = index
        self._mapping_path = mapping_path

    @retry(stop=stop_after_attempt(10), wait=wait_fixed(3), reraise=True)
    def wait_until_ready(self) -> None:
        """Block (with retries) until Elasticsearch responds to a ping."""
        if not self._client.ping():
            raise ConnectionError("Elasticsearch is not reachable yet")

    def ensure_index_exists(self) -> None:
        """Create the index from the shared mapping file if it doesn't exist yet."""
        if self._client.indices.exists(index=self._index):
            logger.info("Index '%s' already exists.", self._index)
            return

        with open(self._mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        self._client.indices.create(index=self._index, body=mapping)
        logger.info("Created index '%s'.", self._index)

    def save(self, document: dict) -> None:
        self._client.index(index=self._index, document=document)
