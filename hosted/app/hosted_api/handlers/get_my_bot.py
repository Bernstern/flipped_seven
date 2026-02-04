from __future__ import annotations

from hosted_api.config import load_settings
from hosted_api.handlers.response import error, ok
from hosted_api.services.auth import authenticate
from hosted_api.services.bots import get_bot_by_owner


def handler(event, _context):
    settings = load_settings()
    auth = authenticate(event.get("headers") or {}, settings)
    if not auth:
        return error("Unauthorized", status_code=401)

    bot = get_bot_by_owner(settings, auth.token_id)
    if not bot:
        return ok({"bot": None})

    # Hide source code from user responses
    bot.pop("source_code", None)
    return ok({"bot": bot})
