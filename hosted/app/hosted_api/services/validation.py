from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flip7.bots.base import BaseBot
from flip7.bots.random_bot import RandomBot
from flip7.bots.scaredy_bot import ScaredyBot
from flip7.core.game_engine import GameEngine
from flip7.types.cards import ActionType, ModifierCard, NumberCard
from flip7.types.events import BotDecisionContext
from flip7.types.game_state import PlayerTableau

from hosted_api.services.bot_loader import load_bot_class


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    error: str | None


def _sample_context() -> BotDecisionContext:
    my_tableau = PlayerTableau(
        player_id="test_bot",
        number_cards=(NumberCard(3), NumberCard(7)),
        modifier_cards=(ModifierCard("+4"),),
        second_chance=False,
        is_active=True,
        is_busted=False,
        is_frozen=False,
        is_passed=False,
    )

    opponent_tableau = PlayerTableau(
        player_id="opponent",
        number_cards=(NumberCard(5), NumberCard(10)),
        modifier_cards=(),
        second_chance=True,
        is_active=True,
        is_busted=False,
        is_frozen=False,
        is_passed=False,
    )

    return BotDecisionContext(
        my_tableau=my_tableau,
        opponent_tableaus={"opponent": opponent_tableau},
        deck_remaining=50,
        my_current_score=25,
        opponent_scores={"opponent": 30},
        current_round=3,
        target_score=200,
    )


def _validate_decisions(bot: BaseBot) -> None:
    context = _sample_context()
    decision = bot.decide_hit_or_pass(context)
    if decision not in ("hit", "pass"):
        raise RuntimeError("decide_hit_or_pass must return 'hit' or 'pass'")

    duplicate = NumberCard(7)
    sc = bot.decide_use_second_chance(context, duplicate)
    if not isinstance(sc, bool):
        raise RuntimeError("decide_use_second_chance must return a boolean")

    eligible = ["test_bot", "opponent"]
    target = bot.choose_action_target(context, ActionType.FLIP_THREE, eligible)
    if target not in eligible:
        raise RuntimeError("choose_action_target must return an eligible player id")


def _smoke_match(bot_class: type[BaseBot], bot_timeout_seconds: float, games: int = 5) -> None:
    for i in range(games):
        player_ids = ["custom", "random", "scaredy"]
        bots = {
            "custom": bot_class("custom"),
            "random": RandomBot("random"),
            "scaredy": ScaredyBot("scaredy"),
        }
        engine = GameEngine(
            game_id=f"smoke_{i}",
            player_ids=player_ids,
            bots=bots,
            event_log_path=Path("/tmp") / f"smoke_{i}.jsonl",
            seed=i,
            bot_timeout=bot_timeout_seconds,
            enable_logging=False,
        )
        engine.execute_game()


def validate_bot(source_code: str, class_name: str | None, bot_timeout_seconds: float) -> ValidationResult:
    try:
        bot_class = load_bot_class(source_code, class_name)
        bot = bot_class("test_bot")
        _validate_decisions(bot)
        _smoke_match(bot_class, bot_timeout_seconds)
        return ValidationResult(ok=True, error=None)
    except Exception as exc:
        return ValidationResult(ok=False, error=str(exc))
