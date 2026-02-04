#!/usr/bin/env bash
set -euo pipefail

PROFILE=${1:-}
REGION=${2:-us-east-1}
if [[ -z "$PROFILE" ]]; then
  echo "Usage: deploy_lambda.sh <aws-profile> [region]"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ZIP_PATH="$ROOT_DIR/hosted/artifacts/flip7_hosted_lambda.zip"

if [[ ! -f "$ZIP_PATH" ]]; then
  echo "Missing artifact: $ZIP_PATH"
  exit 1
fi

FUNCTIONS=(
  "flip7-submit-bot"
  "flip7-get-my-bot"
  "flip7-run-tournament"
  "flip7-publish-leaderboard"
  "flip7-get-leaderboard"
)

export AWS_PAGER=""
export AWS_DEFAULT_REGION="$REGION"

retry_update() {
  local fn="$1"
  local attempts=0
  local max_attempts=5
  local delay=2
  while true; do
    attempts=$((attempts + 1))
    if aws --profile "$PROFILE" --region "$REGION" --no-cli-pager \
      lambda update-function-code --function-name "$fn" --zip-file "fileb://$ZIP_PATH" >/dev/null; then
      return 0
    fi
    if [[ $attempts -ge $max_attempts ]]; then
      echo "Failed to deploy $fn after $attempts attempts"
      return 1
    fi
    sleep "$delay"
    delay=$((delay * 2))
  done
}

for fn in "${FUNCTIONS[@]}"; do
  echo "Deploying $fn"
  retry_update "$fn"
done

echo "Deployment complete."
