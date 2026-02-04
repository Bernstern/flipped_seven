from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from boto3.dynamodb.conditions import Attr

from hosted_api.config import Settings
from hosted_api.services.db import dynamodb_resource


@dataclass(frozen=True)
class BotRecord:
    bot_id: str
    owner_token_id: str
    display_name: str
    class_name: str | None
    source_code: str
    status: str
    validation_error: str | None
    created_at: int
    updated_at: int
    last_validated_at: int | None


def create_bot(
    settings: Settings,
    owner_token_id: str,
    display_name: str,
    class_name: str | None,
    source_code: str,
) -> BotRecord:
    now = int(time.time())
    bot_id = str(uuid.uuid4())
    item = {
        "bot_id": bot_id,
        "owner_token_id": owner_token_id,
        "display_name": display_name,
        "class_name": class_name,
        "source_code": source_code,
        "status": "pending",
        "validation_error": None,
        "created_at": now,
        "updated_at": now,
        "last_validated_at": None,
    }
    table = dynamodb_resource(settings).Table(settings.bots_table)
    table.put_item(Item=item)
    return BotRecord(**item)  # type: ignore[arg-type]


def overwrite_bot(
    settings: Settings,
    bot_id: str,
    display_name: str,
    class_name: str | None,
    source_code: str,
) -> None:
    now = int(time.time())
    table = dynamodb_resource(settings).Table(settings.bots_table)
    table.update_item(
        Key={"bot_id": bot_id},
        UpdateExpression=(
            "SET display_name=:d, class_name=:c, source_code=:s, "
            "#status=:st, validation_error=:e, updated_at=:u"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":d": display_name,
            ":c": class_name,
            ":s": source_code,
            ":st": "validating",
            ":e": None,
            ":u": now,
        },
    )


def update_bot_status(
    settings: Settings,
    bot_id: str,
    status: str,
    validation_error: str | None = None,
) -> None:
    now = int(time.time())
    table = dynamodb_resource(settings).Table(settings.bots_table)
    table.update_item(
        Key={"bot_id": bot_id},
        UpdateExpression="SET #status=:s, validation_error=:e, updated_at=:u, last_validated_at=:v",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":s": status,
            ":e": validation_error,
            ":u": now,
            ":v": now,
        },
    )


def get_bot_by_owner(settings: Settings, owner_token_id: str) -> dict | None:
    table = dynamodb_resource(settings).Table(settings.bots_table)
    resp = table.scan(
        FilterExpression=Attr("owner_token_id").eq(owner_token_id),
        Limit=1,
    )
    items = resp.get("Items") or []
    return items[0] if items else None


def get_bot(settings: Settings, bot_id: str) -> dict | None:
    table = dynamodb_resource(settings).Table(settings.bots_table)
    resp = table.get_item(Key={"bot_id": bot_id})
    return resp.get("Item")


def list_approved_bots(settings: Settings) -> list[dict]:
    table = dynamodb_resource(settings).Table(settings.bots_table)
    resp = table.scan(
        FilterExpression=Attr("status").eq("approved"),
    )
    return resp.get("Items") or []
