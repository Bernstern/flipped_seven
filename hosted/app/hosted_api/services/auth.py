from __future__ import annotations

from dataclasses import dataclass

import boto3

from hosted_api.config import Settings


@dataclass(frozen=True)
class AuthContext:
    token_id: str
    is_admin: bool
    submission_slot_bot_id: str | None
    user_label: str | None


def _parse_bearer(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def authenticate(headers: dict[str, str], settings: Settings) -> AuthContext | None:
    token = _parse_bearer(headers.get("Authorization") or headers.get("authorization"))
    if not token:
        return None

    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region, endpoint_url=settings.aws_endpoint_url)
    table = dynamodb.Table(settings.tokens_table)
    resp = table.get_item(Key={"token_id": token})
    item = resp.get("Item")
    if not item:
        return None

    return AuthContext(
        token_id=token,
        is_admin=bool(item.get("is_admin", False)),
        submission_slot_bot_id=item.get("submission_slot_bot_id"),
        user_label=item.get("user_label"),
    )
