"""
Internationalization (i18n) module for the backend.

Provides translation functions and language detection middleware.
"""

import json
from contextvars import ContextVar
from pathlib import Path
from typing import Literal

# Supported languages
SupportedLanguage = Literal["pl", "en"]
SUPPORTED_LANGUAGES: list[SupportedLanguage] = ["pl", "en"]
DEFAULT_LANGUAGE: SupportedLanguage = "pl"

# Context variable to store current language per request
current_language: ContextVar[SupportedLanguage] = ContextVar(
    "current_language", default=DEFAULT_LANGUAGE
)

# Translation cache
_translations: dict[SupportedLanguage, dict[str, str]] = {}


def _load_translations() -> None:
    """Load all translation files into memory."""
    i18n_dir = Path(__file__).parent.parent / "i18n"

    for lang in SUPPORTED_LANGUAGES:
        file_path = i18n_dir / f"{lang}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                _translations[lang] = json.load(f)
        else:
            _translations[lang] = {}


def get_translation(key: str, lang: SupportedLanguage | None = None, **kwargs) -> str:
    """
    Get a translated string for the given key.

    Args:
        key: The translation key (e.g., "errors.not_found")
        lang: Language code. If None, uses current request language.
        **kwargs: Format arguments for the translation string.

    Returns:
        Translated string, or the key itself if not found.
    """
    if not _translations:
        _load_translations()

    if lang is None:
        lang = current_language.get()

    # Get translation for the specified language, fallback to default
    translations = _translations.get(lang, {})
    if key not in translations:
        translations = _translations.get(DEFAULT_LANGUAGE, {})

    text = translations.get(key, key)

    # Apply format arguments if any
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return text


def t(key: str, **kwargs) -> str:
    """
    Shorthand for get_translation using current request language.

    Args:
        key: The translation key
        **kwargs: Format arguments for the translation string.

    Returns:
        Translated string
    """
    return get_translation(key, **kwargs)


def set_language(lang: str) -> SupportedLanguage:
    """
    Set the current language for the request context.

    Args:
        lang: Language code (will be normalized)

    Returns:
        The actual language set (normalized to supported language)
    """
    # Normalize language code (e.g., "en-US" -> "en")
    normalized = lang.split("-")[0].lower() if lang else DEFAULT_LANGUAGE

    if normalized not in SUPPORTED_LANGUAGES:
        normalized = DEFAULT_LANGUAGE

    current_language.set(normalized)  # type: ignore
    return normalized  # type: ignore


def get_current_language() -> SupportedLanguage:
    """Get the current language for the request context."""
    return current_language.get()


def parse_accept_language(header: str | None) -> SupportedLanguage:
    """
    Parse Accept-Language header and return the best matching language.

    Args:
        header: Accept-Language header value

    Returns:
        Best matching supported language
    """
    if not header:
        return DEFAULT_LANGUAGE

    # Parse header (e.g., "en-US,en;q=0.9,pl;q=0.8")
    languages_with_quality: list[tuple[str, float]] = []

    for part in header.split(","):
        part = part.strip()
        if not part:
            continue

        if ";q=" in part:
            lang, quality = part.split(";q=")
            try:
                quality_value = float(quality)
            except ValueError:
                quality_value = 0.0
        else:
            lang = part
            quality_value = 1.0

        # Normalize language code
        lang = lang.split("-")[0].lower()
        languages_with_quality.append((lang, quality_value))

    # Sort by quality (highest first)
    languages_with_quality.sort(key=lambda x: x[1], reverse=True)

    # Find first supported language
    for lang, _ in languages_with_quality:
        if lang in SUPPORTED_LANGUAGES:
            return lang  # type: ignore

    return DEFAULT_LANGUAGE


# Initialize translations on module load
_load_translations()
