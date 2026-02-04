from __future__ import annotations

import boto3

from hosted_api.config import Settings


def dynamodb_resource(settings: Settings):
    return boto3.resource(
        "dynamodb",
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )
