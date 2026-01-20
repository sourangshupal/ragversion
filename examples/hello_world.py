"""Absolute minimal RAGVersion example - tracks one file in 10 lines."""

import asyncio
from ragversion import AsyncVersionTracker


async def main():
    # Create tracker (auto-initializes, uses SQLite)
    async with await AsyncVersionTracker.create() as tracker:
        # Track a file
        result = await tracker.track("README.md")
        if result.changed:
            print(f"Tracked! Change: {result.change_type.value}, Version: {result.version_number}")
        else:
            print(f"No changes (current version: {result.version_number})")


if __name__ == "__main__":
    asyncio.run(main())
