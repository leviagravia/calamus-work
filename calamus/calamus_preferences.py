"""GTK-free aggregate user preferences for Calamus W106."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from calamus_appearance_preferences import (
    APPEARANCE_LIGHT,
    APPEARANCE_MODES,
    appearance_settings_overrides,
    load_appearance_preference,
)
from calamus_line_numbers import line_number_settings_overrides, load_line_number_preference
from calamus_opacity import load_opacity_preference, opacity_settings_overrides
from calamus_typography import FontPreference, load_font_preference
from calamus_view_preferences import load_text_wrap_preference, normalize_boolean

DEFAULT_SPELL_LANGUAGE = "it"


def normalize_spell_language(value: Any, default: str = DEFAULT_SPELL_LANGUAGE) -> str:
    if not isinstance(default, str) or not default.strip():
        raise ValueError("default spell language must be a non-empty string")
    if isinstance(value, str):
        candidate = value.strip()
        if candidate and "\x00" not in candidate and "\n" not in candidate and "\r" not in candidate:
            return candidate
    return default.strip()


@dataclass(frozen=True)
class PreferencesSnapshot:
    font_family: str = "Monospace"
    font_size: int = 12
    word_wrap: bool = True
    spell_lang: str = DEFAULT_SPELL_LANGUAGE
    inline_spell: bool = False
    always_on_top: bool = False
    appearance_mode: str = APPEARANCE_LIGHT
    opacity_percent: int = 88
    line_numbers: bool = True
    trim_trailing_on_save: bool = False

    def __post_init__(self) -> None:
        # Reuse existing typed normalizers as validation at construction time.
        font = load_font_preference({"font_family": self.font_family, "font_size": self.font_size})
        if font.family != self.font_family or font.size != self.font_size:
            raise ValueError("font preference is not normalized")
        if not isinstance(self.word_wrap, bool):
            raise TypeError("word_wrap must be boolean")
        if normalize_spell_language(self.spell_lang) != self.spell_lang:
            raise ValueError("spell_lang is not normalized")
        if self.inline_spell is not False:
            raise ValueError("inline spell-check remains disabled in W106")
        if not isinstance(self.always_on_top, bool):
            raise TypeError("always_on_top must be boolean")
        if self.appearance_mode not in APPEARANCE_MODES:
            raise ValueError("appearance_mode is invalid")
        opacity = load_opacity_preference({"opacity": self.opacity_percent})
        if opacity.percent != self.opacity_percent:
            raise ValueError("opacity_percent is not normalized")
        if not isinstance(self.line_numbers, bool):
            raise TypeError("line_numbers must be boolean")
        if not isinstance(self.trim_trailing_on_save, bool):
            raise TypeError("trim_trailing_on_save must be boolean")

    def updated(self, **changes: Any) -> "PreferencesSnapshot":
        return replace(self, **changes)

    def to_settings_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "word_wrap": self.word_wrap,
            "spell_lang": self.spell_lang,
            "inline_spell": False,
            "always_on_top": self.always_on_top,
            "trim_trailing_on_save": self.trim_trailing_on_save,
        }
        data.update(appearance_settings_overrides(self.appearance_mode))
        data.update(opacity_settings_overrides(self.opacity_percent))
        data.update(line_number_settings_overrides(self.line_numbers))
        return data


def decode_preferences(settings: Mapping[str, Any] | None) -> PreferencesSnapshot:
    if settings is None:
        settings = {}
    if not isinstance(settings, Mapping):
        raise TypeError("settings must be a mapping")
    font: FontPreference = load_font_preference(settings)
    appearance = load_appearance_preference(settings)
    opacity = load_opacity_preference(settings)
    line_numbers = load_line_number_preference(settings)
    return PreferencesSnapshot(
        font_family=font.family,
        font_size=font.size,
        word_wrap=load_text_wrap_preference(settings),
        spell_lang=normalize_spell_language(settings.get("spell_lang")),
        inline_spell=False,
        always_on_top=normalize_boolean(settings.get("always_on_top"), False),
        appearance_mode=appearance.mode,
        opacity_percent=opacity.percent,
        line_numbers=line_numbers.enabled,
        trim_trailing_on_save=normalize_boolean(settings.get("trim_trailing_on_save"), False),
    )
