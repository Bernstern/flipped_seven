from __future__ import annotations

from hosted_api.config import Settings
from hosted_api.services.db import dynamodb_resource


def set_submission_slot(settings: Settings, token_id: str, bot_id: str) -> None:
    table = dynamodb_resource(settings).Table(settings.tokens_table)
    table.update_item(
        Key={"token_id": token_id},
        UpdateExpression="SET submission_slot_bot_id=:b",
        ExpressionAttributeValues={":b": bot_id},
    )


def get_token(settings: Settings, token_id: str) -> dict | None:
    table = dynamodb_resource(settings).Table(settings.tokens_table)
    resp = table.get_item(Key={"token_id": token_id})
    return resp.get("Item")
