"""Text splitting strategies for chunk-level versioning."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)


class BaseChunker(ABC):
    """Abstract base class for text chunking strategies."""

    @abstractmethod
    async def split_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: The text to split into chunks

        Returns:
            List of text chunks
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens
        """
        pass


class RecursiveTextChunker(BaseChunker):
    """Recursive text chunking strategy.

    This chunker uses LangChain's RecursiveCharacterTextSplitter when available,
    falling back to a simple paragraph-based splitter otherwise.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize the recursive text chunker.

        Args:
            chunk_size: Target size per chunk (in tokens or characters)
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer: Optional[object] = None

        # Try to initialize tiktoken for token counting
        try:
            import tiktoken

            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.debug("Initialized tiktoken tokenizer for token counting")
        except ImportError:
            logger.debug("tiktoken not available, falling back to character-based counting")
        except Exception as e:
            logger.warning(f"Failed to initialize tiktoken: {e}, using fallback")

    async def split_text(self, text: str) -> List[str]:
        """Split text using LangChain if available, else simple fallback.

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,  # Use character length, not token length
            )
            chunks = splitter.split_text(text)
            logger.debug(f"Split text into {len(chunks)} chunks using LangChain")
            return chunks
        except ImportError:
            logger.debug("LangChain not available, using simple paragraph-based splitting")
            return self._simple_split(text)
        except Exception as e:
            logger.warning(f"LangChain splitting failed: {e}, falling back to simple split")
            return self._simple_split(text)

    def _simple_split(self, text: str) -> List[str]:
        """Fallback: split on paragraphs.

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for para in paragraphs:
            # Check if adding this paragraph would exceed chunk_size
            if len(current) + len(para) + 2 <= self.chunk_size:  # +2 for \n\n
                current += para + "\n\n"
            else:
                # Save current chunk if not empty
                if current.strip():
                    chunks.append(current.strip())

                # Start new chunk with overlap if possible
                if chunks and self.chunk_overlap > 0:
                    # Take last chunk_overlap characters from previous chunk
                    overlap_text = chunks[-1][-self.chunk_overlap :]
                    current = overlap_text + "\n\n" + para + "\n\n"
                else:
                    current = para + "\n\n"

        # Add final chunk
        if current.strip():
            chunks.append(current.strip())

        logger.debug(f"Split text into {len(chunks)} chunks using simple splitter")
        return chunks if chunks else [text]  # Return original text if splitting failed

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or character-based estimate.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens (or estimated tokens if tiktoken unavailable)
        """
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token counting failed: {e}, using character estimate")

        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4


class CharacterChunker(BaseChunker):
    """Simple character-based chunking strategy.

    Splits text at fixed character boundaries without regard to semantic boundaries.
    Useful for testing or when speed is more important than quality.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """Initialize the character chunker.

        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def split_text(self, text: str) -> List[str]:
        """Split text at fixed character boundaries.

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if self.chunk_overlap > 0 else end

        return chunks

    def count_tokens(self, text: str) -> int:
        """Estimate token count based on character length.

        Args:
            text: The text to count tokens for

        Returns:
            Estimated number of tokens
        """
        return len(text) // 4


class ChunkerRegistry:
    """Registry for chunking strategies.

    Allows registration and retrieval of different chunking strategies by name.
    """

    _chunkers = {
        "recursive": RecursiveTextChunker,
        "character": CharacterChunker,
    }

    @classmethod
    def get_chunker(cls, name: str = "recursive", **kwargs) -> BaseChunker:
        """Get a chunker instance by name.

        Args:
            name: Name of the chunker strategy (default: "recursive")
            **kwargs: Arguments to pass to the chunker constructor

        Returns:
            Initialized chunker instance

        Raises:
            ValueError: If chunker name is not registered
        """
        chunker_class = cls._chunkers.get(name)
        if not chunker_class:
            logger.warning(
                f"Unknown chunker '{name}', falling back to recursive. "
                f"Available: {list(cls._chunkers.keys())}"
            )
            chunker_class = RecursiveTextChunker

        return chunker_class(**kwargs)

    @classmethod
    def register_chunker(cls, name: str, chunker_class: type) -> None:
        """Register a new chunker strategy.

        Args:
            name: Name to register the chunker under
            chunker_class: The chunker class to register

        Raises:
            ValueError: If chunker_class is not a subclass of BaseChunker
        """
        if not issubclass(chunker_class, BaseChunker):
            raise ValueError(f"{chunker_class} must be a subclass of BaseChunker")

        cls._chunkers[name] = chunker_class
        logger.info(f"Registered chunker: {name}")

    @classmethod
    def list_chunkers(cls) -> List[str]:
        """Get list of registered chunker names.

        Returns:
            List of chunker names
        """
        return list(cls._chunkers.keys())
