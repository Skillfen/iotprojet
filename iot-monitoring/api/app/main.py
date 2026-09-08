"""Read-only REST API exposing the sensor data stored in Elasticsearch."""

import logging
from datetime import datetime, timedelta, timezone
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


@app.get("/alerts/recent")
def recent_alerts(limit: int = Query(default=20, le=200)):
    """Return the most recent anomalous readings, newest first (alerting feed)."""
    try:
        result = es_client.search(
            index=settings.elasticsearch_index,
            query={"term": {"anomaly": True}},
            sort=[{"timestamp": {"order": "desc"}}],
            size=limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Elasticsearch query failed: {exc}") from exc
    return [hit["_source"] for hit in result["hits"]["hits"]]


@app.get("/stats/summary")
def stats_summary():
    """Return a per-device monitoring summary: last reading, anomaly count, staleness."""
    try:
        devices_result = es_client.search(
            index=settings.elasticsearch_index,
            size=0,
            aggs={"devices": {"terms": {"field": "device", "size": 100}}},
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Elasticsearch query failed: {exc}") from exc

    summaries = []
    for bucket in devices_result["aggregations"]["devices"]["buckets"]:
        device = bucket["key"]
        try:
            latest = es_client.search(
                index=settings.elasticsearch_index,
                query={"term": {"device": device}},
                sort=[{"timestamp": {"order": "desc"}}],
                size=1,
            )
            anomaly_count = es_client.count(
                index=settings.elasticsearch_index,
                query={"bool": {"must": [{"term": {"device": device}}, {"term": {"anomaly": True}}]}},
            )["count"]
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Elasticsearch query failed: {exc}") from exc

        last_hit = latest["hits"]["hits"][0]["_source"] if latest["hits"]["hits"] else None
        stale = True
        if last_hit:
            last_seen = datetime.fromisoformat(last_hit["timestamp"])
            stale = (datetime.now(timezone.utc) - last_seen) > timedelta(seconds=settings.stale_after_seconds)

        summaries.append({
            "device": device,
            "reading_count": bucket["doc_count"],
            "anomaly_count": anomaly_count,
            "last_reading": last_hit,
            "stale": stale,
        })

    return summaries
