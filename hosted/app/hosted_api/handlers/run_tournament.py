from __future__ import annotations

import json

from hosted_api.config import load_settings
from hosted_api.handlers.response import error, ok
from hosted_api.services.auth import authenticate
from hosted_api.services.bots import list_approved_bots
from hosted_api.services.runs import create_run, publish_run, update_run_status
from hosted_api.services.tournament import TournamentConfig, run_tournament
from hosted_api.services.tokens import get_token


def handler(event, _context):
    settings = load_settings()
    auth = authenticate(event.get("headers") or {}, settings)
    if not auth or not auth.is_admin:
        return error("Unauthorized", status_code=401)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error("Invalid JSON", status_code=400)

    games_h2h = int(body.get("games_per_matchup_h2h", 100))
    games_all = int(body.get("games_per_matchup_all", 100))
    seed = body.get("seed")
    if seed is not None:
        seed = int(seed)

    bots = list_approved_bots(settings)
    if len(bots) < 2:
        return error("Need at least 2 approved bots to run a tournament", status_code=400)

    for bot in bots:
        token = get_token(settings, bot["owner_token_id"])
        bot["owner_label"] = token.get("user_label") if token else "unknown"

    run_id = create_run(settings, auth.token_id, seed)
    update_run_status(settings, run_id, "running")

    config = TournamentConfig(
        games_per_matchup_head_to_head=games_h2h,
        games_per_matchup_all_vs_all=games_all,
        bot_timeout_seconds=settings.default_bot_timeout_seconds,
        seed=seed,
    )

    try:
        results = run_tournament(bots, config)
        update_run_status(settings, run_id, "complete", results)
        auto_publish = bool(body.get("auto_publish", False))
        if auto_publish:
            publish_run(settings, run_id)
        return ok({"run_id": run_id, "status": "complete"}, status_code=201)
    except Exception as exc:
        update_run_status(settings, run_id, "failed", {"error": str(exc)})
        return error(f"Tournament failed: {exc}", status_code=500)
