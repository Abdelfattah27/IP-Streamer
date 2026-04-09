from __future__ import annotations

from typing import Any

import httpx
from celery import shared_task

from .conf import (
    EVENT_SOURCE_CACHE,
    EVENT_SOURCE_IPINFO,
    EVENT_STATUS_DONE,
    EVENT_STATUS_ERROR,
    EVENT_STATUS_OK,
    EVENT_TYPE_COMPLETE,
    EVENT_TYPE_RESULT,
)
from .ip_lookup import (
    fetch_ip_info,
    get_cached_ip_result,
    increment_job_completed,
    publish_job_message,
    set_cached_ip_result,
)

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.RemoteProtocolError,
    httpx.NetworkError,
)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=2,
    ignore_result=True,
)
def process_ip_lookup_task(self, job_id: str, ip: str) -> None:
    event_payload: dict[str, Any]

    try:
        cached_payload = get_cached_ip_result(ip)
        if cached_payload is not None:
            event_payload = {
                "type": EVENT_TYPE_RESULT,
                "status": EVENT_STATUS_OK,
                "ip": ip,
                "source": EVENT_SOURCE_CACHE,
                "data": cached_payload,
            }
        else:
            ip_data = fetch_ip_info(ip)
            set_cached_ip_result(ip, ip_data)
            event_payload = {
                "type": EVENT_TYPE_RESULT,
                "status": EVENT_STATUS_OK,
                "ip": ip,
                "source": EVENT_SOURCE_IPINFO,
                "data": ip_data,
            }
    except RETRYABLE_EXCEPTIONS as exc:
        # Retry transient network failures with exponential backoff.
        if self.request.retries < self.max_retries:
            retry_countdown = min(2 ** (self.request.retries + 1), 30)
            raise self.retry(exc=exc, countdown=retry_countdown)

        event_payload = {
            "type": EVENT_TYPE_RESULT,
            "status": EVENT_STATUS_ERROR,
            "ip": ip,
            "source": EVENT_SOURCE_IPINFO,
            "error": (f"Transient ipinfo failure after retries: {exc}"),
        }
    except Exception as exc:  # noqa: BLE001
        event_payload = {
            "type": EVENT_TYPE_RESULT,
            "status": EVENT_STATUS_ERROR,
            "ip": ip,
            "source": EVENT_SOURCE_IPINFO,
            "error": str(exc),
        }

    publish_job_message(job_id, event_payload)

    completed, total = increment_job_completed(job_id)
    if total and completed >= total:
        publish_job_message(
            job_id,
            {
                "type": EVENT_TYPE_COMPLETE,
                "status": EVENT_STATUS_DONE,
                "completed": completed,
                "total": total,
            },
        )
