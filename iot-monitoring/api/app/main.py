"""Read-only REST API exposing the sensor data stored in Elasticsearch."""

import logging
from typing import Optional

from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException, Query

from .config import settings

logging.basicConfig(level="INFO", format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("iot_api")

app = FastAPI(title="IoT Monitoring API", version="1.0.0")
es_client = Elasticsearch(settings.elasticsearch_host)


@app.get("/health")
def health():
    """Report API and Elasticsearch connectivity status."""
    try:
        es_ok = es_client.ping()
    except Exception:
        es_ok = False
    return {"status": "ok" if es_ok else "degraded", "elasticsearch": es_ok}


@app.get("/readings/latest")
def latest_readings(
    device: Optional[str] = Query(default=None),
    limit: int = Query(default=20, le=200),
):
    """Return the most recent sensor readings, optionally filtered by device."""
    query = {"match_all": {}} if device is None else {"term": {"device": device}}
    try:
        result = es_client.search(
            index=settings.elasticsearch_index,
            query=query,
            sort=[{"timestamp": {"order": "desc"}}],
            size=limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Elasticsearch query failed: {exc}") from exc

    return [hit["_source"] for hit in result["hits"]["hits"]]


@app.get("/stats/anomalies")
def anomaly_stats():
    """Return the total number of anomalies recorded so far."""
    try:
        result = es_client.count(index=settings.elasticsearch_index, query={"term": {"anomaly": True}})
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Elasticsearch query failed: {exc}") from exc
    return {"anomaly_count": result["count"]}


@app.get("/devices")
def list_devices():
    """Return the distinct device identifiers seen so far."""
    try:
        result = es_client.search(
            index=settings.elasticsearch_index,
            size=0,
            aggs={"devices": {"terms": {"field": "device", "size": 100}}},
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Elasticsearch query failed: {exc}") from exc
    buckets = result["aggregations"]["devices"]["buckets"]
    return [b["key"] for b in buckets]
