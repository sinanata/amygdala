"""Tests for exception hierarchy."""

from __future__ import annotations

import pytest

from amygdala.exceptions import (
    AdapterError,
    AdapterNotFoundError,
    AmygdalaError,
    CaptureError,
    ConfigError,
    ConfigNotFoundError,
    FileTooLargeError,
    GitError,
    IndexCorruptedError,
    IndexOperationError,
    MemoryFileNotFoundError,
    NotAGitRepoError,
    ProfileError,
    ProfileNotFoundError,
    ProviderAPIError,
    ProviderAuthError,
    ProviderError,
    ProviderNotFoundError,
    StorageError,
    UnsupportedFileError,
)


class TestExceptionHierarchy:
    """Verify every exception is an AmygdalaError and has correct parentage."""

    @pytest.mark.parametrize(
        "exc_cls,parent_cls",
        [
            (ConfigError, AmygdalaError),
            (ConfigNotFoundError, ConfigError),
            (IndexOperationError, AmygdalaError),
            (IndexCorruptedError, IndexOperationError),
            (StorageError, AmygdalaError),
            (MemoryFileNotFoundError, StorageError),
            (GitError, AmygdalaError),
            (NotAGitRepoError, GitError),
            (ProviderError, AmygdalaError),
            (ProviderNotFoundError, ProviderError),
            (ProviderAuthError, ProviderError),
            (ProviderAPIError, ProviderError),
            (CaptureError, AmygdalaError),
            (FileTooLargeError, CaptureError),
            (UnsupportedFileError, CaptureError),
            (ProfileError, AmygdalaError),
            (ProfileNotFoundError, ProfileError),
            (AdapterError, AmygdalaError),
            (AdapterNotFoundError, AdapterError),
        ],
    )
    def test_inheritance(self, exc_cls: type, parent_cls: type):
        assert issubclass(exc_cls, parent_cls)
        assert issubclass(exc_cls, AmygdalaError)

    @pytest.mark.parametrize(
        "exc_cls",
        [
            AmygdalaError,
            ConfigError,
            ConfigNotFoundError,
            IndexOperationError,
            IndexCorruptedError,
            StorageError,
            MemoryFileNotFoundError,
            GitError,
            NotAGitRepoError,
            ProviderError,
            ProviderNotFoundError,
            ProviderAuthError,
            ProviderAPIError,
            CaptureError,
            FileTooLargeError,
            UnsupportedFileError,
            ProfileError,
            ProfileNotFoundError,
            AdapterError,
            AdapterNotFoundError,
        ],
    )
    def test_can_raise_and_catch(self, exc_cls: type):
        with pytest.raises(exc_cls, match="test message"):
            raise exc_cls("test message")
