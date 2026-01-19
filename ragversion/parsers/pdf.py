"""PDF document parser."""

import asyncio
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from ragversion.exceptions import ParsingError
from ragversion.parsers.base import BaseParser


class PDFParser(BaseParser):
    """Parser for PDF documents."""

    def __init__(self):
        if PdfReader is None:
            raise ImportError(
                "pypdf is required for PDF parsing. Install with: pip install ragversion[parsers]"
            )

    async def parse(self, file_path: str) -> str:
        """
        Parse a PDF document and extract text content.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text content

        Raises:
            ParsingError: If parsing fails
        """
        try:
            # Run blocking I/O in executor
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, self._parse_sync, file_path)
            return text
        except Exception as e:
            raise ParsingError(file_path, e)

    def _parse_sync(self, file_path: str) -> str:
        """Synchronous PDF parsing."""
        try:
            reader = PdfReader(file_path)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise ParsingError(file_path, e)

    def supports(self, file_extension: str) -> bool:
        """Check if this parser supports the given file extension."""
        return file_extension.lower() == ".pdf"
