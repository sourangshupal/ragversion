"""Markdown document parser."""

import aiofiles

try:
    import markdown
except ImportError:
    markdown = None

from ragversion.exceptions import ParsingError
from ragversion.parsers.base import BaseParser


class MarkdownParser(BaseParser):
    """Parser for Markdown documents."""

    def __init__(self):
        # Markdown is optional - we can still parse as plain text
        self.has_markdown = markdown is not None

    async def parse(self, file_path: str) -> str:
        """
        Parse a Markdown document and extract text content.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Extracted text content (plain text or HTML)

        Raises:
            ParsingError: If parsing fails
        """
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # If markdown library is available, convert to HTML
            # Otherwise, return raw markdown
            if self.has_markdown:
                # Convert markdown to plain text (strip HTML tags)
                import re

                html = markdown.markdown(content)
                # Remove HTML tags for plain text
                text = re.sub(r"<[^>]+>", "", html)
                return text
            else:
                return content

        except Exception as e:
            raise ParsingError(file_path, e)

    def supports(self, file_extension: str) -> bool:
        """Check if this parser supports the given file extension."""
        return file_extension.lower() in [".md", ".markdown"]
