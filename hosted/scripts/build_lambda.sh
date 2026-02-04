#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="$ROOT_DIR/hosted/app"
BUILD_DIR="$ROOT_DIR/hosted/.build"
ZIP_PATH="$ROOT_DIR/hosted/.build/flip7_hosted_lambda.zip"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

VENV_PY="$APP_DIR/.venv/bin/python"
if [[ -x "$VENV_PY" ]]; then
  SITE_PACKAGES="$("$VENV_PY" - <<'PY'
import sysconfig
print(sysconfig.get_paths()["purelib"])
PY
)"
  cp -R "$SITE_PACKAGES"/* "$BUILD_DIR/"
else
  python -m pip install -r <(python - <<'PY'
import tomllib
from pathlib import Path

data = tomllib.loads(Path("hosted/app/pyproject.toml").read_text())
print("\n".join(data["project"]["dependencies"]))
PY
  ) -t "$BUILD_DIR" >/dev/null
fi

cp -R "$APP_DIR/hosted_api" "$BUILD_DIR/"
cp -R "$ROOT_DIR/flip7" "$BUILD_DIR/"

cd "$BUILD_DIR"
python - <<'PY'
import zipfile
from pathlib import Path

zip_path = Path("flip7_hosted_lambda.zip")
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in Path(".").rglob("*"):
        if path.is_file():
            zf.write(path, path.as_posix())
print(zip_path)
PY

mkdir -p "$ROOT_DIR/hosted/artifacts"
cp "$ZIP_PATH" "$ROOT_DIR/hosted/artifacts/"

echo "Built: $ROOT_DIR/hosted/artifacts/flip7_hosted_lambda.zip"
