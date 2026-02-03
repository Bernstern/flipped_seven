"""
TimeoutBot - A bot that intentionally times out for testing purposes.

This bot is used exclusively for testing timeout handling in the game engine.
It can be configured to timeout at specific decision points.
"""

import time
from typing import Literal

from flip7.bots.base import BaseBot
from flip7.types import ActionType, BotDecisionContext, NumberCard


class TimeoutBot(BaseBot):
    """
    A bot that intentionally times out at specified decision points.

    This bot is designed for testing timeout handling. It can be configured
    to timeout at different decision points:
    - hit_or_pass: Timeout during hit/pass decision
    - action_target: Timeout during action card target selection
    - second_chance: Timeout during Second Chance usage decision
    - none: Never timeout (normal behavior)

    Args:
        bot_name: Name of the bot
        timeout_on: Which decision point to timeout at
        timeout_duration: How long to sleep before timeout (default: 10 seconds)
    """

    def __init__(
        self,
        bot_name: str,
        timeout_on: Literal["hit_or_pass", "action_target", "second_chance", "none"] = "hit_or_pass",
        timeout_duration: float = 10.0,
    ):
        super().__init__(bot_name)
        self.timeout_on = timeout_on
        self.timeout_duration = timeout_duration

    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        """
        Decide whether to hit or pass.

        If configured to timeout on hit_or_pass, this will sleep for timeout_duration.
        Otherwise returns 'pass' immediately.
        """
        if self.timeout_on == "hit_or_pass":
            time.sleep(self.timeout_duration)

        return "pass"

    def decide_use_second_chance(
        self, context: BotDecisionContext, duplicate: NumberCard
    ) -> bool:
        """
        Decide whether to use Second Chance.

        If configured to timeout on second_chance, this will sleep for timeout_duration.
        Otherwise returns False immediately.
        """
        if self.timeout_on == "second_chance":
            time.sleep(self.timeout_duration)

        return False

    def choose_action_target(
        self,
        context: BotDecisionContext,
        action_type: ActionType,
        eligible_targets: list[str],
    ) -> str:
        """
        Choose a target for an action card.

        If configured to timeout on action_target, this will sleep for timeout_duration.
        Otherwise returns the first eligible target immediately.
        """
        if self.timeout_on == "action_target":
            time.sleep(self.timeout_duration)

        return eligible_targets[0]
