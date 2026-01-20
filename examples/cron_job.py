#!/usr/bin/env python3
"""
Cron job example for RAGVersion.

This script is designed to be run periodically (e.g., via cron)
to sync documents to your RAG system.

Add to crontab:
0 * * * * /path/to/venv/bin/python /path/to/cron_job.py >> /var/log/ragversion.log 2>&1
"""

import asyncio
import logging
import sys
from datetime import datetime

from ragversion import AsyncVersionTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def sync_documents():
    """Sync documents to RAG system."""
    logger.info("Starting document sync...")

    try:
        # Initialize tracker with factory method (best practice)
        tracker = await AsyncVersionTracker.create(
            storage="supabase",  # Uses environment variables
            store_content=True,
            max_file_size_mb=50,
        )

        # Track directory
        result = await tracker.track_directory(
            "./documents",
            patterns=["*.pdf", "*.docx", "*.md", "*.txt"],
            recursive=True,
            max_workers=4,
        )

        logger.info(f"Sync completed:")
        logger.info(f"  Total files: {result.total_files}")
        logger.info(f"  Changes: {result.success_count}")
        logger.info(f"  Errors: {result.failure_count}")
        logger.info(f"  Duration: {result.duration_seconds:.2f}s")
        logger.info(f"  Success rate: {result.success_rate:.1f}%")

        # Log changes
        for event in result.successful:
            logger.info(f"  {event.change_type.value.upper()}: {event.file_name}")

        # Log errors
        for error in result.failed:
            logger.error(f"  FAILED: {error.file_path} - {error.error}")

        await tracker.close()

        # Exit with success
        return 0

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        return 1


def main():
    """Main entry point."""
    logger.info(f"RAGVersion cron job started at {datetime.now()}")

    exit_code = asyncio.run(sync_documents())

    logger.info(f"RAGVersion cron job finished at {datetime.now()}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
