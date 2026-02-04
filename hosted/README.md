# Hosted Flip 7 Service

This folder contains the hosted service implementation, infra, and scripts.

## Local testing

```bash
cd hosted/app
pytest -q
```

## Build Lambda artifact

```bash
./hosted/scripts/build_lambda.sh
```

## CLI helpers

Set API URL once:

```bash
export FLIP7_API_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com"
```

Seed tokens:

```bash
uv run flip7-admin-seed-token --label msnko
uv run flip7-admin-seed-token --label bernstern --admin
```

Submit a bot:

```bash
uv run flip7-api-submit-bot --token <token> --display-name "My Bot" --class-name MyBot --source ./my_bot.py
```

Check your bot:

```bash
uv run flip7-api-get-me --token <token>
```

Run a tournament (admin):

```bash
uv run flip7-admin-run-tournament --token <admin-token> --games-h2h 10 --games-all 10 --seed 42
```

Publish results (admin):

```bash
uv run flip7-admin-publish --token <admin-token> --run-id <run-id>
```

Get leaderboard:

```bash
uv run flip7-api-leaderboard
```

## Deploy (AWS SSO)

```bash
aws sso login --profile flip-seven
cd hosted/infra/terraform
terraform init
terraform apply

./hosted/scripts/build_lambda.sh
./hosted/scripts/deploy_lambda.sh flip-seven
```

## API routes
- `POST /bots/submit`
- `GET /bots/me`
- `POST /admin/tournament/run`
- `POST /admin/leaderboard/publish`
- `GET /leaderboard/current`

Note: Leaderboard results are updated nightly. A nicer UI for leaderboard viewing is coming soon.

## Nightly tournament

Infra includes an EventBridge rule that runs the tournament nightly:
- Head-to-head: 1,000 games
- All-vs-all: 10,000 games
- Seed: 42
- Auto-publish enabled
