from __future__ import annotations

import time
import uuid

from decimal import Decimal

from boto3.dynamodb.conditions import Attr

from hosted_api.config import Settings
from hosted_api.services.db import dynamodb_resource


def _to_dynamo(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(v) for v in value]
    return value


def create_run(settings: Settings, triggered_by: str, seed: int | None) -> str:
    run_id = str(uuid.uuid4())
    now = int(time.time())
    item = {
        "run_id": run_id,
        "triggered_by": triggered_by,
        "status": "queued",
        "seed": seed,
        "results": None,
        "created_at": now,
        "completed_at": None,
        "is_current": False,
    }
    table = dynamodb_resource(settings).Table(settings.runs_table)
    table.put_item(Item=item)
    return run_id


def update_run_status(settings: Settings, run_id: str, status: str, results: dict | None = None) -> None:
    now = int(time.time())
    table = dynamodb_resource(settings).Table(settings.runs_table)
    results_payload = _to_dynamo(results) if results is not None else None
    table.update_item(
        Key={"run_id": run_id},
        UpdateExpression="SET #status=:s, results=:r, completed_at=:c",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":s": status, ":r": results_payload, ":c": now},
    )


def publish_run(settings: Settings, run_id: str) -> None:
    table = dynamodb_resource(settings).Table(settings.runs_table)
    # Clear existing current
    scan = table.scan(FilterExpression=Attr("is_current").eq(True))
    for item in scan.get("Items") or []:
        table.update_item(
            Key={"run_id": item["run_id"]},
            UpdateExpression="SET is_current=:v",
            ExpressionAttributeValues={":v": False},
        )
    table.update_item(
        Key={"run_id": run_id},
        UpdateExpression="SET is_current=:v",
        ExpressionAttributeValues={":v": True},
    )


def get_current_leaderboard(settings: Settings) -> dict | None:
    table = dynamodb_resource(settings).Table(settings.runs_table)
    scan = table.scan(FilterExpression=Attr("is_current").eq(True), Limit=1)
    items = scan.get("Items") or []
    return items[0] if items else None
