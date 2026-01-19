"""Document parsers for RAGVersion."""

from ragversion.parsers.base import BaseParser, ParserRegistry
from ragversion.parsers.pdf import PDFParser
from ragversion.parsers.docx import DOCXParser
from ragversion.parsers.text import TextParser
from ragversion.parsers.markdown import MarkdownParser

# Register all parsers
ParserRegistry.register(".pdf", PDFParser)
ParserRegistry.register(".docx", DOCXParser)
ParserRegistry.register(".doc", DOCXParser)
ParserRegistry.register(".txt", TextParser)
ParserRegistry.register(".md", MarkdownParser)
ParserRegistry.register(".markdown", MarkdownParser)

__all__ = [
    "BaseParser",
    "ParserRegistry",
    "PDFParser",
    "DOCXParser",
    "TextParser",
    "MarkdownParser",
]
