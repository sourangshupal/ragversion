"""Chunk-level versioning for RAGVersion (v0.10.0).

This module provides chunk-level change tracking for cost-optimized RAG operations.
By tracking changes at the chunk level, RAGVersion can achieve 80-95% embedding cost
reduction by only re-embedding changed chunks instead of entire documents.
"""

from ragversion.chunking.detector import ChunkChangeDetector
from ragversion.chunking.splitters import (
    BaseChunker,
    ChunkerRegistry,
    RecursiveTextChunker,
)

__all__ = [
    "ChunkChangeDetector",
    "BaseChunker",
    "ChunkerRegistry",
    "RecursiveTextChunker",
]
