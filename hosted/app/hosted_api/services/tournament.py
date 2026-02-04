from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flip7.tournament.round_robin_runner import run_round_robin_tournament

from hosted_api.services.bot_loader import load_bot_class


@dataclass(frozen=True)
class TournamentConfig:
    games_per_matchup_head_to_head: int
    games_per_matchup_all_vs_all: int
    bot_timeout_seconds: float
    seed: int | None


def run_tournament(bot_entries: list[dict], config: TournamentConfig) -> dict:
    bot_classes = []
    metadata = []
    for entry in bot_entries:
        source = entry["source_code"]
        class_name = entry.get("class_name")
        owner_label = entry.get("owner_label", "unknown")
        bot_id = entry["bot_id"]
        internal_name = f"{owner_label}:{bot_id}"
        base_cls = load_bot_class(source, class_name)
        wrapped_cls = type(internal_name, (base_cls,), {})
        bot_classes.append(wrapped_cls)
        metadata.append(
            {
                "internal_name": internal_name,
                "owner_label": owner_label,
                "bot_id": bot_id,
                "display_name": entry.get("display_name"),
                "class_name": class_name,
            }
        )

    output_root = Path("/tmp") / "tournament_results"
    output_h2h = output_root / "head_to_head"
    output_all = output_root / "all_vs_all"

    results_h2h = run_round_robin_tournament(
        tournament_name="Hosted - Head-to-Head",
        games_per_matchup=config.games_per_matchup_head_to_head,
        players_per_game=2,
        bot_classes=bot_classes,
        bot_timeout_seconds=config.bot_timeout_seconds,
        output_dir=output_h2h,
        save_replays=False,
        tournament_seed=config.seed,
    )

    results_all = run_round_robin_tournament(
        tournament_name="Hosted - All-vs-All",
        games_per_matchup=config.games_per_matchup_all_vs_all,
        players_per_game=len(bot_classes),
        bot_classes=bot_classes,
        bot_timeout_seconds=config.bot_timeout_seconds,
        output_dir=output_all,
        save_replays=False,
        tournament_seed=None if config.seed is None else config.seed + 1_000_000,
    )

    return {
        "bot_metadata": metadata,
        "head_to_head": results_h2h,
        "all_vs_all": results_all,
    }
