from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    aws_region: str
    aws_endpoint_url: str | None
    bots_table: str
    runs_table: str
    tokens_table: str
    show_code_top_n: int
    default_bot_timeout_seconds: float


def load_settings() -> Settings:
    endpoint_url = os.environ.get("AWS_ENDPOINT_URL")
    return Settings(
        aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        aws_endpoint_url=endpoint_url if endpoint_url else None,
        bots_table=os.environ.get("BOTS_TABLE", "Flip7Bots"),
        runs_table=os.environ.get("RUNS_TABLE", "Flip7TournamentRuns"),
        tokens_table=os.environ.get("TOKENS_TABLE", "Flip7Tokens"),
        show_code_top_n=int(os.environ.get("SHOW_CODE_TOP_N", "0")),
        default_bot_timeout_seconds=float(os.environ.get("BOT_TIMEOUT_SECONDS", "1.0")),
    )
