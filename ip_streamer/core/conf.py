from __future__ import annotations

# Redis key prefixes
JOB_KEY_PREFIX = "ip_lookup:job"
EVENTS_KEY_PREFIX = "ip_lookup:events"
CHANNEL_PREFIX = "ip_lookup:channel"
CACHE_KEY_PREFIX = "ip_lookup:result"

# Event values
EVENT_TYPE_RESULT = "result"
EVENT_TYPE_COMPLETE = "complete"
EVENT_TYPE_TIMEOUT = "timeout"

EVENT_STATUS_OK = "ok"
EVENT_STATUS_ERROR = "error"
EVENT_STATUS_DONE = "done"
EVENT_STATUS_CONNECTED = "connected"
EVENT_STATUS_CLOSED = "closed"

EVENT_SOURCE_CACHE = "cache"
EVENT_SOURCE_IPINFO = "ipinfo"

# Redis pub/sub envelope values
PUBSUB_TYPE_FIELD = "type"
PUBSUB_MESSAGE_TYPE = "message"
PUBSUB_DATA_FIELD = "data"

# SSE constants
SSE_EVENT_READY = "ready"
SSE_EVENT_TIMEOUT = "timeout"
SSE_HEARTBEAT_PAYLOAD = ": keep-alive\n\n"
SSE_CONTENT_TYPE = "text/event-stream"

# Response and route constants
LOOKUP_SSE_ROUTE_NAME = "lookup-sse"
LOOKUP_UNKNOWN_OR_EXPIRED_DETAIL = "Unknown or expired job_id."


# IP validation reasons
IP_VALIDATION_REASON_INVALID = "invalid_ip"
IP_VALIDATION_REASON_NOT_PUBLIC = "not_public_ip"
