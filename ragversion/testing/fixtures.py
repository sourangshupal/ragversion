"""Test fixtures and utilities."""

import tempfile
from pathlib import Path
from typing import List, NamedTuple


class TestFile(NamedTuple):
    """Represents a test file."""

    path: str
    content: str
    file_type: str


def create_test_file(
    content: str = "Test content",
    file_type: str = "txt",
    directory: str = None,
    name: str = None,
) -> str:
    """
    Create a temporary test file.

    Args:
        content: File content
        file_type: File extension (without dot)
        directory: Optional directory to create file in
        name: Optional file name (default: temp file)

    Returns:
        Path to created file
    """
    if directory:
        Path(directory).mkdir(parents=True, exist_ok=True)
        if name:
            file_path = Path(directory) / f"{name}.{file_type}"
        else:
            file_path = Path(directory) / f"test_{tempfile.mktemp()}.{file_type}"

        with open(file_path, "w") as f:
            f.write(content)

        return str(file_path)
    else:
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{file_type}", delete=False
        ) as f:
            f.write(content)
            return f.name


def create_sample_documents(
    count: int = 10,
    file_type: str = "txt",
    directory: str = None,
) -> List[TestFile]:
    """
    Create multiple sample test documents.

    Args:
        count: Number of documents to create
        file_type: File extension
        directory: Optional directory to create files in

    Returns:
        List of TestFile objects
    """
    documents = []

    for i in range(count):
        content = f"Sample document {i + 1}\n\n" + "Lorem ipsum " * 20
        path = create_test_file(
            content=content,
            file_type=file_type,
            directory=directory,
            name=f"document_{i + 1}",
        )

        documents.append(
            TestFile(path=path, content=content, file_type=file_type)
        )

    return documents
