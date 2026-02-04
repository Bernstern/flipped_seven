# Flip 7 Competition — Competitor Guide

## 1) Get your token (from admin)
The admin will create a unique label and give you a token. Keep it secret; it is your API key.

Set it locally:

```bash
export FLIP7_API_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com"
export MY_TOKEN="<token-from-admin>"
```

## 2) Write your bot
Create a file like `my_bot.py` with a class that extends `BaseBot`:

```python
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
```

**Allowed dependencies:** Python stdlib plus `numpy`, `pandas`, `scikit-learn`.

## 3) Submit your bot

```bash
uv run flip7-api-submit-bot \
  --token "$MY_TOKEN" \
  --display-name "my-bot" \
  --class-name MyBot \
  --source ./my_bot.py
```

Submissions **replace your previous submission** (same token).

## 4) Check your status

```bash
uv run flip7-api-get-me --token "$MY_TOKEN"
```

## 5) Leaderboard

```bash
uv run flip7-api-leaderboard | jq
```

Leaderboard results are updated nightly. A nicer UI for leaderboard viewing is coming soon.
