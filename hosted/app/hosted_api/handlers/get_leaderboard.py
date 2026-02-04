from __future__ import annotations

from hosted_api.config import load_settings
from hosted_api.handlers.response import ok
from hosted_api.services.runs import get_current_leaderboard


def handler(_event, _context):
    settings = load_settings()
    current = get_current_leaderboard(settings)
    if not current:
        return ok({"leaderboard": None})

    return ok({"leaderboard": current})
