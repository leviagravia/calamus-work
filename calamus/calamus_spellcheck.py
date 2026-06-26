"""Hunspell integration for Calamus."""
from __future__ import annotations

import shutil
import subprocess


def hunspell_dict(lang: str) -> str:
    return "it_IT" if lang == "it" else "en_US"


def hunspell_base_command(lang: str):
    if not shutil.which("hunspell"):
        return None
    return ["hunspell", "-d", hunspell_dict(lang)]


def hunspell_misspelled_words(text: str, lang: str):
    base = hunspell_base_command(lang)
    if not base:
        return None
    proc = subprocess.run(base + ["-l"], input=text, text=True, capture_output=True, timeout=20)
    if proc.returncode not in (0, 1):
        err = (proc.stderr or "").strip()
        raise RuntimeError(err or "Hunspell failed.")
    return {word.strip() for word in proc.stdout.splitlines() if word.strip()}


def hunspell_suggestions(word: str, lang: str) -> list[str]:
    base = hunspell_base_command(lang)
    if not base:
        return []
    proc = subprocess.run(base + ["-a"], input=word + "\n", text=True, capture_output=True, timeout=10)
    suggestions: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("&") and ":" in line:
            suggestions = [x.strip() for x in line.split(":", 1)[1].split(",") if x.strip()]
            break
    return suggestions[:12]
