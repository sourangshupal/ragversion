"""Plain text document parser."""

import aiofiles

from ragversion.exceptions import ParsingError
from ragversion.parsers.base import BaseParser


class TextParser(BaseParser):
    """Parser for plain text documents."""

    async def parse(self, file_path: str) -> str:
        """
        Parse a text document and extract content.

        Args:
            file_path: Path to the text file

        Returns:
            File content

        Raises:
            ParsingError: If parsing fails
        """
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return content
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                async with aiofiles.open(file_path, "r", encoding="latin-1") as f:
                    content = await f.read()
                    return content
            except Exception as e:
                raise ParsingError(file_path, e)
        except Exception as e:
            raise ParsingError(file_path, e)

    def supports(self, file_extension: str) -> bool:
        """Check if this parser supports the given file extension."""
        return file_extension.lower() == ".txt"
