# Flip 7 Competition — Admin Guide

## 1) Seed a competitor label
Labels must be unique.

```bash
uv run flip7-admin-seed-token --label alice
```

Copy the printed token and share it with the competitor.

Admin token (for yourself):

```bash
uv run flip7-admin-seed-token --label bernstern --admin
```

## 2) Run a tournament

```bash
uv run flip7-admin-run-tournament \
  --token "$ADMIN_TOKEN" \
  --games-h2h 10 \
  --games-all 10 \
  --seed 42
```

## 3) Publish results

```bash
uv run flip7-admin-publish --token "$ADMIN_TOKEN" --run-id <run-id>
```

## 4) View leaderboard

```bash
uv run flip7-api-leaderboard | jq
```

## Notes
- Submissions overwrite previous submissions for the same token.
- Tournament results use internal names `owner_label:bot_id` to avoid collisions.
- Leaderboard results are updated nightly.
- A UI for leaderboard viewing is coming soon.
