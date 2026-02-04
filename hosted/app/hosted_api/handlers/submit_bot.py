from __future__ import annotations

import json

from hosted_api.config import load_settings
from hosted_api.handlers.response import error, ok
from hosted_api.services.auth import authenticate
from hosted_api.services.bots import create_bot, get_bot, overwrite_bot, update_bot_status
from hosted_api.services.tokens import set_submission_slot
from hosted_api.services.validation import validate_bot


def handler(event, _context):
    settings = load_settings()
    auth = authenticate(event.get("headers") or {}, settings)
    if not auth:
        return error("Unauthorized", status_code=401)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error("Invalid JSON", status_code=400)

    display_name = body.get("display_name")
    source_code = body.get("source_code")
    class_name = body.get("class_name")

    if not display_name or not source_code:
        return error("display_name and source_code are required", status_code=400)

    bot_id = auth.submission_slot_bot_id
    if bot_id:
        existing = get_bot(settings, bot_id)
        if existing:
            overwrite_bot(settings, bot_id, display_name, class_name, source_code)
        else:
            bot = create_bot(settings, auth.token_id, display_name, class_name, source_code)
            bot_id = bot.bot_id
    else:
        bot = create_bot(settings, auth.token_id, display_name, class_name, source_code)
        bot_id = bot.bot_id

    update_bot_status(settings, bot_id, "validating")
    result = validate_bot(source_code, class_name, settings.default_bot_timeout_seconds)
    if result.ok:
        update_bot_status(settings, bot_id, "approved", None)
        set_submission_slot(settings, auth.token_id, bot_id)
        return ok({"bot_id": bot_id, "status": "approved"}, status_code=201)

    update_bot_status(settings, bot_id, "rejected", result.error)
    return ok({"bot_id": bot_id, "status": "rejected", "error": result.error}, status_code=201)
