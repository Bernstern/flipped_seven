#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path

import boto3
import requests
from boto3.dynamodb.conditions import Attr


def _api_url(args: argparse.Namespace) -> str:
    url = args.api_url or os.environ.get("FLIP7_API_URL")
    if not url:
        raise SystemExit("API URL required via --api-url or FLIP7_API_URL")
    return url.rstrip("/")


def _auth_headers(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def cmd_seed_token(args: argparse.Namespace) -> None:
    token = secrets.token_hex(32)
    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(args.table)
    existing = table.scan(
        FilterExpression=Attr("user_label").eq(args.label),
        Limit=1,
    ).get("Items")
    if existing:
        raise SystemExit(f"user_label already exists: {args.label}")
    table.put_item(
        Item={
            "token_id": token,
            "user_label": args.label,
            "is_admin": args.admin,
            "submission_slot_bot_id": None,
        }
    )
    print(token)


def cmd_submit_bot(args: argparse.Namespace) -> None:
    api_url = _api_url(args)
    source = Path(args.source).read_text(encoding="utf-8")
    body = {
        "display_name": args.display_name,
        "class_name": args.class_name,
        "source_code": source,
    }
    resp = requests.post(
        f"{api_url}/bots/submit",
        headers={**_auth_headers(args.token), "Content-Type": "application/json"},
        data=json.dumps(body),
        timeout=30,
    )
    print(resp.status_code)
    print(resp.text)


def cmd_get_me(args: argparse.Namespace) -> None:
    api_url = _api_url(args)
    resp = requests.get(
        f"{api_url}/bots/me",
        headers=_auth_headers(args.token),
        timeout=30,
    )
    print(resp.status_code)
    print(resp.text)


def cmd_run_tournament(args: argparse.Namespace) -> None:
    api_url = _api_url(args)
    body = {
        "games_per_matchup_h2h": args.games_h2h,
        "games_per_matchup_all": args.games_all,
        "seed": args.seed,
    }
    resp = requests.post(
        f"{api_url}/admin/tournament/run",
        headers={**_auth_headers(args.token), "Content-Type": "application/json"},
        data=json.dumps(body),
        timeout=30,
    )
    print(resp.status_code)
    print(resp.text)


def cmd_publish(args: argparse.Namespace) -> None:
    api_url = _api_url(args)
    body = {"run_id": args.run_id}
    resp = requests.post(
        f"{api_url}/admin/leaderboard/publish",
        headers={**_auth_headers(args.token), "Content-Type": "application/json"},
        data=json.dumps(body),
        timeout=30,
    )
    print(resp.status_code)
    print(resp.text)


def cmd_leaderboard(args: argparse.Namespace) -> None:
    api_url = _api_url(args)
    resp = requests.get(
        f"{api_url}/leaderboard/current",
        timeout=30,
    )
    print(resp.status_code)
    print(resp.text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Flip7 hosted API CLI")
    parser.add_argument("--api-url", help="API base URL (or FLIP7_API_URL)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    seed = sub.add_parser("seed-token", help="Seed a DynamoDB token")
    seed.add_argument("--label", required=True)
    seed.add_argument("--admin", action="store_true")
    seed.add_argument("--profile", default="flip-seven")
    seed.add_argument("--region", default="us-east-1")
    seed.add_argument("--table", default="Flip7Tokens")
    seed.set_defaults(func=cmd_seed_token)

    submit = sub.add_parser("submit-bot", help="Submit a bot")
    submit.add_argument("--token", required=True)
    submit.add_argument("--display-name", required=True)
    submit.add_argument("--class-name")
    submit.add_argument("--source", required=True)
    submit.set_defaults(func=cmd_submit_bot)

    me = sub.add_parser("get-me", help="Get current user's bot status")
    me.add_argument("--token", required=True)
    me.set_defaults(func=cmd_get_me)

    run = sub.add_parser("run-tournament", help="Run a tournament (admin)")
    run.add_argument("--token", required=True)
    run.add_argument("--games-h2h", type=int, default=10)
    run.add_argument("--games-all", type=int, default=10)
    run.add_argument("--seed", type=int)
    run.set_defaults(func=cmd_run_tournament)

    publish = sub.add_parser("publish", help="Publish a run (admin)")
    publish.add_argument("--token", required=True)
    publish.add_argument("--run-id", required=True)
    publish.set_defaults(func=cmd_publish)

    leaderboard = sub.add_parser("leaderboard", help="Get current leaderboard")
    leaderboard.set_defaults(func=cmd_leaderboard)

    return parser


def _command_from_argv0() -> str | None:
    name = os.path.basename(sys.argv[0])
    mapping = {
        "flip7-admin-seed-token": "seed-token",
        "flip7-api-submit-bot": "submit-bot",
        "flip7-api-get-me": "get-me",
        "flip7-admin-run-tournament": "run-tournament",
        "flip7-admin-publish": "publish",
        "flip7-api-leaderboard": "leaderboard",
    }
    return mapping.get(name)


def main() -> None:
    forced_cmd = _command_from_argv0()
    parser = build_parser()
    if forced_cmd:
        args = parser.parse_args([forced_cmd, *sys.argv[1:]])
    else:
        args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
