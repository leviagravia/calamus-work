"""Minimal non-fatal logging helpers for the GTK shell.

Calamus is intentionally quiet in normal use, but broad ``except`` blocks must
not silently swallow runtime problems during development and release testing.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

_LOGGER_NAME = "calamus"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG if os.environ.get("CALAMUS_DEBUG") else logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(handler)
    return logger


def log_nonfatal(context: str, exc: BaseException | None = None) -> None:
    logger = get_logger()
    if exc is None:
        logger.debug("%s", context)
    else:
        logger.debug("%s: %s", context, exc, exc_info=bool(os.environ.get("CALAMUS_DEBUG")))
