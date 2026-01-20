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

        # Build helpful message
        msg = f"Failed to parse {file_path}: {original_error}"

        # Add specific suggestions based on error type
        error_str = str(original_error).lower()
        if "pdf" in error_str or file_path.lower().endswith(".pdf"):
            msg += "\n\nTroubleshooting:"
            msg += "\n  • Install PDF parser: pip install pypdf"
            msg += "\n  • Check if file is corrupted: try opening it in a PDF viewer"
            msg += "\n  • Verify file format: ensure it's a valid PDF file"
        elif "docx" in error_str or "word" in error_str or file_path.lower().endswith((".docx", ".doc")):
            msg += "\n\nTroubleshooting:"
            msg += "\n  • Install DOCX parser: pip install python-docx"
            msg += "\n  • Verify file is valid .docx format (not .doc)"
            msg += "\n  • Try opening file in Microsoft Word or LibreOffice"
        elif "pptx" in error_str or file_path.lower().endswith((".pptx", ".ppt")):
            msg += "\n\nTroubleshooting:"
            msg += "\n  • Install PPTX parser: pip install python-pptx"
            msg += "\n  • Verify file is valid .pptx format"
        elif "xlsx" in error_str or file_path.lower().endswith((".xlsx", ".xls")):
            msg += "\n\nTroubleshooting:"
            msg += "\n  • Install Excel parser: pip install openpyxl"
            msg += "\n  • Verify file is valid Excel format"
        else:
            msg += "\n\nTroubleshooting:"
            msg += "\n  • Install all parsers: pip install ragversion[parsers]"
            msg += "\n  • Check file format and encoding"
            msg += "\n  • Verify file is not corrupted"

        super().__init__(msg)


class StorageError(RAGVersionError):
    """Raised when storage operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error

        # Enhance message with suggestions
        enhanced_msg = f"Storage error: {message}"

        if original_error:
            enhanced_msg += f"\nOriginal error: {original_error}"

            error_str = str(original_error).lower()

            # Connection errors
            if "connection" in error_str or "connect" in error_str:
                enhanced_msg += "\n\nTroubleshooting:"
                enhanced_msg += "\n  • Check database connection and credentials"
                enhanced_msg += "\n  • For Supabase: verify SUPABASE_URL and SUPABASE_SERVICE_KEY"
                enhanced_msg += "\n  • For SQLite: check file path and permissions"
                enhanced_msg += "\n  • Verify network connectivity (if using cloud storage)"

            # Permission errors
            elif "permission" in error_str or "denied" in error_str:
                enhanced_msg += "\n\nTroubleshooting:"
                enhanced_msg += "\n  • Check file/directory permissions"
                enhanced_msg += "\n  • Ensure write access to database file and directory"
                enhanced_msg += "\n  • Run with appropriate user privileges"

            # Database/table not found
            elif "not found" in error_str or "does not exist" in error_str:
                enhanced_msg += "\n\nTroubleshooting:"
                enhanced_msg += "\n  • For Supabase: run database migrations"
                enhanced_msg += "\n  • Verify tables exist: documents, versions, version_content"
                enhanced_msg += "\n  • Check database initialization: await tracker.initialize()"

            # Generic database error
            else:
                enhanced_msg += "\n\nTroubleshooting:"
                enhanced_msg += "\n  • Verify database is accessible"
                enhanced_msg += "\n  • Check database logs for more details"
                enhanced_msg += "\n  • Ensure storage backend is properly initialized"

        super().__init__(enhanced_msg)


class ConfigurationError(RAGVersionError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, config_file: Optional[str] = None):
        self.config_file = config_file

        msg = f"Configuration error: {message}"

        if config_file:
            msg += f"\nConfig file: {config_file}"

        msg += "\n\nTroubleshooting:"
        msg += "\n  • Run: ragversion init  (to create default config)"
        msg += "\n  • Verify YAML syntax is correct"
        msg += "\n  • Check environment variables are set (for Supabase: SUPABASE_URL, SUPABASE_SERVICE_KEY)"
        msg += "\n  • Use factory method for zero config: await AsyncVersionTracker.create()"

        super().__init__(msg)


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
