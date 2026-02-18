"""Tests for extension profiles system."""

from __future__ import annotations

import pytest

from amygdala.constants import SUPPORTED_EXTENSIONS
from amygdala.core.resolver import BASE_LANGUAGE_MAP
from amygdala.exceptions import ProfileNotFoundError
from amygdala.profiles.builtins import BUILTIN_PROFILES
from amygdala.profiles.models import ExtensionProfile
from amygdala.profiles.registry import (
    get_profile,
    list_profiles,
    resolve_exclude_patterns,
    resolve_extensions,
    resolve_language_map,
)


class TestExtensionProfileModel:
    def test_minimal(self):
        p = ExtensionProfile(name="test")
        assert p.name == "test"
        assert p.description == ""
        assert p.extensions == frozenset()
        assert p.language_map == {}
        assert p.exclude_patterns == []

    def test_full(self):
        p = ExtensionProfile(
            name="custom",
            description="A custom profile",
            extensions=frozenset({".xyz", ".abc"}),
            language_map={".xyz": "xyz-lang"},
            exclude_patterns=["build/"],
        )
        assert ".xyz" in p.extensions
        assert p.language_map[".xyz"] == "xyz-lang"
        assert "build/" in p.exclude_patterns


class TestBuiltinProfiles:
    EXPECTED_PROFILES = ["unity", "unreal", "python", "node", "react", "nextjs"]

    @pytest.mark.parametrize("name", EXPECTED_PROFILES)
    def test_profile_exists(self, name: str):
        assert name in BUILTIN_PROFILES

    @pytest.mark.parametrize("name", EXPECTED_PROFILES)
    def test_profile_has_extensions(self, name: str):
        assert len(BUILTIN_PROFILES[name].extensions) > 0

    @pytest.mark.parametrize("name", EXPECTED_PROFILES)
    def test_profile_has_exclude_patterns(self, name: str):
        assert len(BUILTIN_PROFILES[name].exclude_patterns) > 0

    def test_unity_has_shader(self):
        assert ".shader" in BUILTIN_PROFILES["unity"].extensions

    def test_unreal_has_uproject(self):
        assert ".uproject" in BUILTIN_PROFILES["unreal"].extensions

    def test_python_has_pyi(self):
        assert ".pyi" in BUILTIN_PROFILES["python"].extensions

    def test_node_has_mjs(self):
        assert ".mjs" in BUILTIN_PROFILES["node"].extensions

    def test_react_has_scss(self):
        assert ".scss" in BUILTIN_PROFILES["react"].extensions

    def test_nextjs_has_mdx(self):
        assert ".mdx" in BUILTIN_PROFILES["nextjs"].extensions


class TestGetProfile:
    def test_valid(self):
        p = get_profile("unity")
        assert p.name == "unity"

    def test_invalid_raises(self):
        with pytest.raises(ProfileNotFoundError, match="bogus"):
            get_profile("bogus")


class TestListProfiles:
    def test_returns_sorted(self):
        names = list_profiles()
        assert names == sorted(names)
        assert len(names) == 6


class TestResolveExtensions:
    def test_no_profiles_returns_base(self):
        result = resolve_extensions([])
        assert result == SUPPORTED_EXTENSIONS

    def test_single_profile_adds_extensions(self):
        result = resolve_extensions(["unity"])
        assert ".shader" in result
        # Base extensions still present
        assert ".py" in result

    def test_multiple_profiles_compose(self):
        result = resolve_extensions(["unity", "unreal"])
        assert ".shader" in result
        assert ".uproject" in result
        assert ".py" in result

    def test_invalid_profile_raises(self):
        with pytest.raises(ProfileNotFoundError):
            resolve_extensions(["nonexistent"])


class TestResolveLanguageMap:
    def test_no_profiles_returns_base(self):
        result = resolve_language_map([])
        assert result == BASE_LANGUAGE_MAP

    def test_single_profile_adds_mappings(self):
        result = resolve_language_map(["unity"])
        assert result[".shader"] == "shaderlab"
        # Base mappings still present
        assert result[".py"] == "python"

    def test_multiple_profiles_compose(self):
        result = resolve_language_map(["unity", "unreal"])
        assert result[".shader"] == "shaderlab"
        assert result[".usf"] == "hlsl"

    def test_invalid_profile_raises(self):
        with pytest.raises(ProfileNotFoundError):
            resolve_language_map(["nonexistent"])


class TestResolveExcludePatterns:
    def test_no_profiles_returns_base(self):
        base = ["*.pyc", "__pycache__"]
        result = resolve_exclude_patterns(base, [])
        assert result == base

    def test_single_profile_adds_patterns(self):
        base = ["*.pyc"]
        result = resolve_exclude_patterns(base, ["unity"])
        assert "*.pyc" in result
        assert "Library/" in result

    def test_deduplicates(self):
        base = ["node_modules/"]
        result = resolve_exclude_patterns(base, ["node"])
        assert result.count("node_modules/") == 1

    def test_multiple_profiles_compose(self):
        result = resolve_exclude_patterns([], ["unity", "unreal"])
        assert "Library/" in result
        assert "Binaries/" in result
