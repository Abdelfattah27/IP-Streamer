from __future__ import annotations

import ipaddress
import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import httpx
import redis
import redis.asyncio as redis_async
from django.conf import settings
from django.core.cache import cache

from .conf import (
    CACHE_KEY_PREFIX,
    CHANNEL_PREFIX,
    EVENTS_KEY_PREFIX,
    IP_VALIDATION_REASON_INVALID,
    IP_VALIDATION_REASON_NOT_PUBLIC,
    JOB_KEY_PREFIX,
)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_public_ips(
    ip_values: list[str],
) -> tuple[list[str], list[dict[str, str]]]:
    valid_ips: list[str] = []
    rejected_ips: list[dict[str, str]] = []

    for candidate in ip_values:
        try:
            parsed_ip = ipaddress.ip_address(candidate)
        except ValueError:
            rejected_ips.append(
                {"ip": candidate, "reason": IP_VALIDATION_REASON_INVALID}
            )
            continue

        normalized_ip = str(parsed_ip)
        if not parsed_ip.is_global:
            rejected_ips.append(
                {
                    "ip": normalized_ip,
                    "reason": IP_VALIDATION_REASON_NOT_PUBLIC,
                }
            )
            continue

        valid_ips.append(normalized_ip)

    return valid_ips, rejected_ips


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


@lru_cache(maxsize=1)
def get_async_redis_client() -> redis_async.Redis:
    return redis_async.from_url(settings.REDIS_URL, decode_responses=True)


def get_job_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}:{job_id}"


def get_job_events_key(job_id: str) -> str:
    return f"{EVENTS_KEY_PREFIX}:{job_id}"


def get_job_channel(job_id: str) -> str:
    return f"{CHANNEL_PREFIX}:{job_id}"


def get_ip_cache_key(ip: str) -> str:
    return f"{CACHE_KEY_PREFIX}:{ip}"


def initialize_job(job_id: str, total_tasks: int) -> None:
    client = get_redis_client()
    job_key = get_job_key(job_id)
    pipeline = client.pipeline()
    pipeline.hset(
        job_key,
        mapping={
            "total": total_tasks,
            "completed": 0,
            "created_at": now_utc_iso(),
        },
    )
    pipeline.expire(job_key, settings.IP_LOOKUP_JOB_TTL_SECONDS)
    pipeline.execute()


def get_cached_ip_result(ip: str) -> Any:
    return cache.get(get_ip_cache_key(ip))


def set_cached_ip_result(ip: str, payload: dict[str, Any]) -> None:
    cache.set(
        get_ip_cache_key(ip),
        payload,
        timeout=settings.IP_LOOKUP_CACHE_TTL_SECONDS,
    )


def fetch_ip_info(ip: str) -> dict[str, Any]:
    url = f"{settings.IPINFO_BASE_URL.rstrip('/')}/{ip}/?token={settings.IPINFO_TOKEN}"
    print(f"Fetching IP info for {ip} from {url}")
    headers = {"Accept": "application/json"}
    response = httpx.get(
        url,
        headers=headers,
        timeout=settings.IPINFO_HTTP_TIMEOUT_SECONDS,
    )

    parsed_payload: Any = None
    try:
        parsed_payload = response.json()
    except ValueError:
        parsed_payload = None

    if response.status_code >= 400:
        error_message = ""
        if isinstance(parsed_payload, dict):
            raw_error = parsed_payload.get("error")
            if isinstance(raw_error, dict):
                error_message = str(
                    raw_error.get("title") or raw_error.get("message") or ""
                )
            elif raw_error:
                error_message = str(raw_error)

        if not error_message:
            error_message = response.text[:200]

        raise RuntimeError(
            "ipinfo request failed with "
            f"status {response.status_code}: "
            f"{error_message or 'Unknown error'}"
        )

    if not isinstance(parsed_payload, dict):
        raise RuntimeError("ipinfo returned an unexpected response body.")

    return parsed_payload


def publish_job_message(job_id: str, payload: dict[str, Any]) -> str:
    client = get_redis_client()
    message_payload = dict(payload)
    message_payload.setdefault("job_id", job_id)
    message_payload.setdefault("message_id", uuid.uuid4().hex)
    message_payload.setdefault("sent_at", now_utc_iso())

    encoded_message = json.dumps(
        message_payload,
        separators=(",", ":"),
        default=str,
    )

    pipeline = client.pipeline()
    pipeline.rpush(get_job_events_key(job_id), encoded_message)
    pipeline.expire(
        get_job_events_key(job_id),
        settings.IP_LOOKUP_JOB_TTL_SECONDS,
    )
    pipeline.publish(get_job_channel(job_id), encoded_message)
    pipeline.execute()

    return encoded_message


def increment_job_completed(job_id: str) -> tuple[int, int]:
    client = get_redis_client()
    job_key = get_job_key(job_id)
    total_raw = client.hget(job_key, "total")
    if total_raw is None:
        return 0, 0

    completed_raw = client.hincrby(job_key, "completed", 1)
    client.expire(job_key, settings.IP_LOOKUP_JOB_TTL_SECONDS)

    return int(completed_raw), int(total_raw)


def format_sse(payload: dict[str, Any], event: str | None = None) -> str:
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(payload, separators=(',', ':'), default=str)}")
    return "\n".join(lines) + "\n\n"
