import json

from hosted_api.handlers.submit_bot import handler


BOT_CODE = """
from flip7.bots.base import BaseBot
from flip7.types.events import BotDecisionContext
from flip7.types.cards import ActionType, NumberCard
from typing import Literal

class MyBot(BaseBot):
    def decide_hit_or_pass(self, context: BotDecisionContext) -> Literal["hit", "pass"]:
        return "pass"

    def decide_use_second_chance(self, context: BotDecisionContext, duplicate: NumberCard) -> bool:
        return True

    def choose_action_target(self, context: BotDecisionContext, action: ActionType, eligible: list[str]) -> str:
        return eligible[0]
"""


def test_submit_bot_happy_path(dynamodb):
    tokens = dynamodb.Table("Flip7Tokens")
    tokens.put_item(Item={"token_id": "tok-1", "is_admin": False, "submission_slot_bot_id": None})

    event = {
        "headers": {"Authorization": "Bearer tok-1"},
        "body": json.dumps({"display_name": "My Bot", "class_name": "MyBot", "source_code": BOT_CODE}),
    }

    resp = handler(event, None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert body["status"] in {"approved", "rejected"}
