from __future__ import annotations

import importlib.util
import sys
import tempfile
import uuid
from pathlib import Path

from flip7.bots.base import BaseBot


def load_bot_class(source_code: str, class_name: str | None) -> type[BaseBot]:
    module_id = f"user_bot_{uuid.uuid4().hex}"
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        bot_file = tmp_path / f"{module_id}.py"
        bot_file.write_text(source_code, encoding="utf-8")

        spec = importlib.util.spec_from_file_location(module_id, bot_file)
        if spec is None or spec.loader is None:
            raise RuntimeError("Failed to load bot module")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_id] = module
        spec.loader.exec_module(module)

        if class_name:
            obj = getattr(module, class_name, None)
            if obj is None or not isinstance(obj, type):
                raise RuntimeError(f"Class '{class_name}' not found in submission")
            if not issubclass(obj, BaseBot):
                raise RuntimeError(f"Class '{class_name}' does not extend BaseBot")
            return obj

        for _, obj in module.__dict__.items():
            if isinstance(obj, type) and issubclass(obj, BaseBot) and obj is not BaseBot:
                return obj

    raise RuntimeError("No bot class found in submission")
