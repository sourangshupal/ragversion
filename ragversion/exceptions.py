"""Custom exceptions for RAGVersion."""

from typing import Optional


class RAGVersionError(Exception):
    """Base exception for all RAGVersion errors."""

    pass


class ParsingError(RAGVersionError):
    """Raised when document parsing fails."""

    def __init__(self, file_path: str, original_error: Exception):
        self.file_path = file_path
        self.original_error = original_error
        super().__init__(f"Failed to parse {file_path}: {original_error}")


class StorageError(RAGVersionError):
    """Raised when storage operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        if original_error:
            super().__init__(f"{message}: {original_error}")
        else:
            super().__init__(message)


class ConfigurationError(RAGVersionError):
    """Raised when configuration is invalid."""

    pass


class DocumentNotFoundError(RAGVersionError):
    """Raised when a document is not found."""

    def __init__(self, document_id: str):
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class VersionNotFoundError(RAGVersionError):
    """Raised when a version is not found."""

    def __init__(self, document_id: str, version_number: int):
        self.document_id = document_id
        self.version_number = version_number
        super().__init__(f"Version {version_number} not found for document {document_id}")
