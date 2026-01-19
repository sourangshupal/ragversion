"""Base parser interface for document parsing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Type


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    async def parse(self, file_path: str) -> str:
        """
        Parse a document and extract text content.

        Args:
            file_path: Path to the file to parse

        Returns:
            Extracted text content

        Raises:
            ParsingError: If parsing fails
        """
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """
        Check if this parser supports the given file extension.

        Args:
            file_extension: File extension (e.g., '.pdf', '.docx')

        Returns:
            True if supported, False otherwise
        """
        pass


class ParserRegistry:
    """Registry for document parsers."""

    _parsers: Dict[str, Type[BaseParser]] = {}

    @classmethod
    def register(cls, extension: str, parser_class: Type[BaseParser]) -> None:
        """
        Register a parser for a file extension.

        Args:
            extension: File extension (e.g., '.pdf')
            parser_class: Parser class to use
        """
        cls._parsers[extension.lower()] = parser_class

    @classmethod
    def get_parser(cls, file_path: str) -> Optional[BaseParser]:
        """
        Get a parser for the given file.

        Args:
            file_path: Path to the file

        Returns:
            Parser instance or None if no parser found
        """
        extension = Path(file_path).suffix.lower()
        parser_class = cls._parsers.get(extension)

        if parser_class:
            return parser_class()

        return None

    @classmethod
    def supports(cls, file_path: str) -> bool:
        """
        Check if any parser supports this file.

        Args:
            file_path: Path to the file

        Returns:
            True if supported, False otherwise
        """
        extension = Path(file_path).suffix.lower()
        return extension in cls._parsers
