"""Exception hierarchy for Amygdala."""


class AmygdalaError(Exception):
    """Base exception for all Amygdala errors."""


class ConfigError(AmygdalaError):
    """Configuration-related error."""


class ConfigNotFoundError(ConfigError):
    """Raised when .amygdala/config.toml is missing."""


class IndexOperationError(AmygdalaError):
    """Index-related error."""


class IndexCorruptedError(IndexOperationError):
    """Raised when index.json is corrupted or invalid."""


class StorageError(AmygdalaError):
    """Storage-related error."""


class MemoryFileNotFoundError(StorageError):
    """Raised when a memory .md file is not found."""


class GitError(AmygdalaError):
    """Git operation error."""


class NotAGitRepoError(GitError):
    """Raised when a path is not inside a git repository."""


class ProviderError(AmygdalaError):
    """LLM provider error."""


class ProviderNotFoundError(ProviderError):
    """Raised when a requested provider is not installed."""


class ProviderAuthError(ProviderError):
    """Raised when provider authentication fails."""


class ProviderAPIError(ProviderError):
    """Raised when an API call to the provider fails."""


class CaptureError(AmygdalaError):
    """Capture pipeline error."""


class FileTooLargeError(CaptureError):
    """Raised when a file exceeds the configured size limit."""


class UnsupportedFileError(CaptureError):
    """Raised when a file type is not supported for capture."""


class AdapterError(AmygdalaError):
    """Adapter-related error."""


class AdapterNotFoundError(AdapterError):
    """Raised when a requested adapter is not available."""
