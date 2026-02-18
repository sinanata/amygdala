"""Profile lookup and resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from amygdala.constants import SUPPORTED_EXTENSIONS
from amygdala.core.resolver import BASE_LANGUAGE_MAP
from amygdala.exceptions import ProfileNotFoundError
from amygdala.profiles.builtins import BUILTIN_PROFILES

if TYPE_CHECKING:
    from amygdala.profiles.models import ExtensionProfile


def get_profile(name: str) -> ExtensionProfile:
    """Return a built-in profile by name, or raise ProfileNotFoundError."""
    try:
        return BUILTIN_PROFILES[name]
    except KeyError:
        available = ", ".join(sorted(BUILTIN_PROFILES))
        raise ProfileNotFoundError(
            f"Unknown profile '{name}'. Available: {available}"
        ) from None


def list_profiles() -> list[str]:
    """Return sorted list of available profile names."""
    return sorted(BUILTIN_PROFILES)


def resolve_extensions(profile_names: list[str]) -> frozenset[str]:
    """Compute the effective extension set: base + all profile extensions."""
    result = set(SUPPORTED_EXTENSIONS)
    for name in profile_names:
        profile = get_profile(name)
        result |= profile.extensions
    return frozenset(result)


def resolve_language_map(profile_names: list[str]) -> dict[str, str]:
    """Compute the effective language map: base + all profile language maps."""
    result = dict(BASE_LANGUAGE_MAP)
    for name in profile_names:
        profile = get_profile(name)
        result.update(profile.language_map)
    return result


def resolve_exclude_patterns(
    base: list[str], profile_names: list[str],
) -> list[str]:
    """Compute deduplicated exclude patterns: base + all profile excludes."""
    seen: set[str] = set()
    result: list[str] = []
    for pattern in base:
        if pattern not in seen:
            seen.add(pattern)
            result.append(pattern)
    for name in profile_names:
        profile = get_profile(name)
        for pattern in profile.exclude_patterns:
            if pattern not in seen:
                seen.add(pattern)
                result.append(pattern)
    return result
