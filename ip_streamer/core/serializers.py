from __future__ import annotations
import uuid
from .tasks import process_ip_lookup_task
from rest_framework import serializers
from .ip_lookup import initialize_job, validate_public_ips


class RejectedIPSerializer(serializers.Serializer):
    ip = serializers.CharField()
    reason = serializers.CharField()


class LookupResponseSerializer(serializers.Serializer):
    job_id = serializers.UUIDField(format="hex_verbose")
    accepted_count = serializers.IntegerField(min_value=0)
    rejected_count = serializers.IntegerField(min_value=0)
    accepted_ips = serializers.ListField(child=serializers.IPAddressField())
    rejected_ips = RejectedIPSerializer(many=True)
    sse_url = serializers.URLField()


class LookupRequestSerializer(serializers.Serializer):
    ips = serializers.ListField(
        child=serializers.CharField(allow_blank=False, trim_whitespace=True),
        allow_empty=False,
        required=True,
    )

    def validate_ips(self, value):
        valid_ips, rejected_ips = validate_public_ips(value)

        if not valid_ips:
            raise serializers.ValidationError(
                {
                    "detail": "No valid public IPs were found in the request.",
                    "rejected_ips": rejected_ips,
                }
            )

        # store for later use in create()
        self._valid_ips = valid_ips
        self._rejected_ips = rejected_ips

        return value

    def create(self, validated_data):
        valid_ips = self._valid_ips
        rejected_ips = self._rejected_ips

        job_id = str(uuid.uuid4())

        initialize_job(job_id=job_id, total_tasks=len(valid_ips))

        for ip in valid_ips:
            process_ip_lookup_task.delay(job_id=job_id, ip=ip)

        return {
            "job_id": job_id,
            "accepted_count": len(valid_ips),
            "rejected_count": len(rejected_ips),
            "accepted_ips": valid_ips,
            "rejected_ips": rejected_ips,
        }
