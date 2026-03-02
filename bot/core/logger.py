from __future__ import annotations

from pathlib import Path
import logging


def setup_logging(log_dir: str) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    root.addHandler(stream)

    file_handler = logging.FileHandler(Path(log_dir) / "engine.log")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
