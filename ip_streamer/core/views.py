from __future__ import annotations

import json
import time
from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from .conf import (
    EVENT_STATUS_CLOSED,
    EVENT_TYPE_COMPLETE,
    EVENT_TYPE_TIMEOUT,
    PUBSUB_MESSAGE_TYPE,
)
from .ip_lookup import (
    format_sse,
    get_async_redis_client,
    get_job_channel,
    get_job_events_key,
    get_job_key,
)
from .serializers import LookupRequestSerializer, LookupResponseSerializer


def _decode_event(message: str) -> dict[str, Any]:
    try:
        parsed = json.loads(message)
    except json.JSONDecodeError:
        return {}

    if isinstance(parsed, dict):
        return parsed
    return {}


class LookupAPIView(GenericAPIView):
    serializer_class = LookupRequestSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Submit IPs for asynchronous lookup",
        operation_description=(
            "Validates IPs, creates a lookup job, dispatches async tasks, "
            "and returns job metadata with an SSE URL."
        ),
        request_body=LookupRequestSerializer,
        responses={
            202: LookupResponseSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        sse_url = request.build_absolute_uri(
            reverse(
                "lookup-sse",
                kwargs={"job_id": result["job_id"]},
            )
        )

        result["sse_url"] = sse_url

        return Response(result, status=status.HTTP_202_ACCEPTED)


class LookupSSEView(View):
    http_method_names = ["get"]

    async def get(
        self,
        request: HttpRequest,
        job_id: str,
    ) -> JsonResponse | StreamingHttpResponse:
        redis_client = get_async_redis_client()
        if not await redis_client.exists(get_job_key(job_id)):
            return JsonResponse(
                {"detail": "Unknown or expired job_id."},
                status=404,
            )

        channel = get_job_channel(job_id)
        pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
        await pubsub.subscribe(channel)

        backlog_messages = await redis_client.lrange(
            get_job_events_key(job_id),
            0,
            -1,
        )
        heartbeat_seconds = settings.IP_LOOKUP_SSE_HEARTBEAT_SECONDS
        max_idle_seconds = settings.IP_LOOKUP_SSE_MAX_IDLE_SECONDS

        async def stream_events():
            seen_message_ids: set[str] = set()
            stream_start = time.monotonic()
            last_emit = stream_start

            try:
                yield format_sse(
                    {"job_id": job_id, "status": "connected"},
                    event="ready",
                )

                for raw_message in backlog_messages:
                    parsed = _decode_event(raw_message)
                    message_id = parsed.get("message_id")
                    if isinstance(message_id, str):
                        seen_message_ids.add(message_id)

                    yield f"data: {raw_message}\n\n"
                    last_emit = time.monotonic()

                    if parsed.get("type") == EVENT_TYPE_COMPLETE:
                        return

                while True:
                    envelope = await pubsub.get_message(timeout=1.0)
                    now = time.monotonic()

                    if envelope and envelope.get("type") == PUBSUB_MESSAGE_TYPE:
                        message = envelope.get("data", "")
                        if isinstance(message, bytes):
                            message = message.decode("utf-8")

                        parsed = _decode_event(message)
                        message_id = parsed.get("message_id")
                        if (
                            isinstance(message_id, str)
                            and message_id in seen_message_ids
                        ):
                            continue

                        if isinstance(message_id, str):
                            seen_message_ids.add(message_id)

                        yield f"data: {message}\n\n"
                        last_emit = now

                        if parsed.get("type") == EVENT_TYPE_COMPLETE:
                            break
                    else:
                        if now - last_emit >= heartbeat_seconds:
                            yield ": keep-alive\n\n"
                            last_emit = now

                    if now - stream_start >= max_idle_seconds:
                        yield format_sse(
                            {
                                "job_id": job_id,
                                "type": EVENT_TYPE_TIMEOUT,
                                "status": EVENT_STATUS_CLOSED,
                            },
                            event="timeout",
                        )
                        break
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()

        response = StreamingHttpResponse(
            stream_events(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class LookupTemplateView(TemplateView):
    template_name = "lookup.html"
