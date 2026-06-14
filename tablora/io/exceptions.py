"""Exceptions raised by file IO adapters."""


class FileManagerError(Exception):
    """Base class for file manager failures."""


class UnsupportedFileTypeError(FileManagerError):
    """Raised when a path has a file extension the editor does not support."""


class FileLoadError(FileManagerError):
    """Raised when a file cannot be loaded as a workbook document."""


class FileSaveError(FileManagerError):
    """Raised when a workbook document cannot be saved."""
