from __future__ import annotations

import json

from hosted_api.config import load_settings
from hosted_api.handlers.response import error, ok
from hosted_api.services.auth import authenticate
from hosted_api.services.runs import publish_run


def handler(event, _context):
    settings = load_settings()
    auth = authenticate(event.get("headers") or {}, settings)
    if not auth or not auth.is_admin:
        return error("Unauthorized", status_code=401)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error("Invalid JSON", status_code=400)

    run_id = body.get("run_id")
    if not run_id:
        return error("run_id is required", status_code=400)

    publish_run(settings, run_id)
    return ok({"run_id": run_id, "status": "current"})
