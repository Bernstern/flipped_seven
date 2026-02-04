#!/usr/bin/env bash
set -euo pipefail

echo "Local tests (requires localstack if using endpoint):"
cd "$(dirname "${BASH_SOURCE[0]}")/../app"
pytest -q
