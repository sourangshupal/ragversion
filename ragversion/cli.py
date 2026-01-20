"""Command-line interface for RAGVersion."""

import asyncio
import functools
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ragversion import AsyncVersionTracker, __version__
from ragversion.config import RAGVersionConfig
from ragversion.storage import SupabaseStorage

console = Console()


def async_command(f):
    """Decorator to run async Click commands."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group()
@click.version_option(version=__version__)
def main():
    """RAGVersion - Async version tracking for RAG applications."""
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    default="ragversion.yaml",
    help="Path to config file",
)
def init(config: str):
    """Initialize a new RAGVersion project."""
    try:
        # Create example config
        example_config = Path(__file__).parent.parent / "ragversion.yaml.example"

        if Path(config).exists():
            rprint(f"[yellow]Config file already exists: {config}[/yellow]")
            if not click.confirm("Overwrite?"):
                return

        # Copy example config
        with open(example_config, "r") as src:
            with open(config, "w") as dst:
                dst.write(src.read())

        rprint(f"[green]✓[/green] Created config file: {config}")
        rprint("\n[bold]Next steps:[/bold]")
        rprint("1. Edit ragversion.yaml with your Supabase credentials")
        rprint("2. Run migrations: ragversion migrate")
        rprint("3. Start tracking: ragversion track ./documents")

    except Exception as e:
        rprint(f"[red]✗[/red] Failed to initialize: {e}")
        sys.exit(1)


@main.command()
@click.option("--config", "-c", help="Path to config file")
@async_command
async def migrate(config: Optional[str]):
    """Run database migrations."""
    try:
        # Load config
        cfg = RAGVersionConfig.load(config)

        if not cfg.supabase:
            rprint("[red]✗[/red] Supabase configuration not found")
            sys.exit(1)

        # Initialize storage
        storage = SupabaseStorage(
            url=cfg.supabase.url,
            key=cfg.supabase.key,
        )

        await storage.initialize()

        # Show migration SQL
        migration_file = Path(__file__).parent / "storage" / "migrations" / "001_initial_schema.sql"

        rprint("[bold]Database Migration[/bold]\n")
        rprint("Run the following SQL in your Supabase SQL Editor:\n")
        rprint(f"File: {migration_file}\n")

        with open(migration_file, "r") as f:
            sql = f.read()
            rprint("[dim]" + sql[:500] + "...[/dim]\n")

        rprint("[yellow]Note:[/yellow] Migrations should be run manually in Supabase SQL Editor")
        rprint("Visit: https://supabase.com/dashboard/project/_/sql")

        await storage.close()

    except Exception as e:
        rprint(f"[red]✗[/red] Migration failed: {e}")
        sys.exit(1)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--config", "-c", help="Path to config file")
@click.option("--patterns", "-p", multiple=True, help="File patterns (e.g., *.pdf)")
@click.option("--recursive/--no-recursive", default=True, help="Recursive search")
@click.option("--workers", "-w", default=4, help="Number of parallel workers")
@async_command
async def track(
    path: str,
    config: Optional[str],
    patterns: tuple,
    recursive: bool,
    workers: int,
):
    """Track files for changes."""
    try:
        # Load config
        cfg = RAGVersionConfig.load(config)

        if not cfg.supabase:
            rprint("[red]✗[/red] Supabase configuration not found")
            sys.exit(1)

        # Initialize tracker
        storage = SupabaseStorage(
            url=cfg.supabase.url,
            key=cfg.supabase.key,
        )

        tracker = AsyncVersionTracker(
            storage=storage,
            store_content=cfg.tracking.store_content,
            max_file_size_mb=cfg.tracking.max_file_size_mb,
        )

        await tracker.initialize()

        # Check if path is file or directory
        p = Path(path)

        if p.is_file():
            # Track single file
            with console.status("[bold blue]Tracking file..."):
                event = await tracker.track(path)

            if event:
                rprint(f"[green]✓[/green] {event.change_type.value.upper()}: {event.file_name}")
            else:
                rprint(f"[dim]No changes detected: {p.name}[/dim]")

        else:
            # Track directory
            pattern_list = list(patterns) if patterns else ["*"]

            with console.status(f"[bold blue]Scanning {path}..."):
                result = await tracker.track_directory(
                    path,
                    patterns=pattern_list,
                    recursive=recursive,
                    max_workers=workers,
                )

            # Display results
            rprint(f"\n[bold]Results:[/bold]")
            rprint(f"  Total files: {result.total_files}")
            rprint(f"  Changes: {result.success_count}")
            rprint(f"  Errors: {result.failure_count}")
            rprint(f"  Duration: {result.duration_seconds:.2f}s")
            rprint(f"  Success rate: {result.success_rate:.1f}%")

            if result.successful:
                rprint("\n[bold]Changes:[/bold]")
                for event in result.successful[:10]:  # Show first 10
                    icon = "+" if event.change_type.value == "created" else "~"
                    rprint(f"  {icon} {event.file_name}")

                if len(result.successful) > 10:
                    rprint(f"  ... and {len(result.successful) - 10} more")

            if result.failed:
                rprint("\n[bold red]Errors:[/bold red]")
                for error in result.failed[:5]:  # Show first 5
                    rprint(f"  [red]✗[/red] {error.file_path}: {error.error_type}")

                if len(result.failed) > 5:
                    rprint(f"  ... and {len(result.failed) - 5} more")

        await tracker.close()

    except Exception as e:
        rprint(f"[red]✗[/red] Tracking failed: {e}")
        sys.exit(1)


@main.command()
@click.option("--config", "-c", help="Path to config file")
@click.option("--limit", "-l", default=20, help="Number of documents to list")
@async_command
async def list(config: Optional[str], limit: int):
    """List tracked documents."""
    try:
        # Load config
        cfg = RAGVersionConfig.load(config)

        if not cfg.supabase:
            rprint("[red]✗[/red] Supabase configuration not found")
            sys.exit(1)

        # Initialize tracker
        storage = SupabaseStorage(
            url=cfg.supabase.url,
            key=cfg.supabase.key,
        )

        tracker = AsyncVersionTracker(storage=storage)
        await tracker.initialize()

        # Get documents
        documents = await tracker.list_documents(limit=limit)

        if not documents:
            rprint("[dim]No documents tracked yet[/dim]")
            await tracker.close()
            return

        # Create table
        table = Table(title="Tracked Documents")
        table.add_column("File", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Versions", justify="right", style="green")
        table.add_column("Size", justify="right")
        table.add_column("Updated", style="yellow")

        for doc in documents:
            size_kb = doc.file_size / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"

            table.add_row(
                doc.file_name,
                doc.file_type,
                str(doc.version_count),
                size_str,
                doc.updated_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)

        await tracker.close()

    except Exception as e:
        rprint(f"[red]✗[/red] Failed to list documents: {e}")
        sys.exit(1)


@main.command()
@click.argument("document_id")
@click.option("--config", "-c", help="Path to config file")
@async_command
async def history(document_id: str, config: Optional[str]):
    """View version history for a document."""
    try:
        from uuid import UUID

        # Load config
        cfg = RAGVersionConfig.load(config)

        if not cfg.supabase:
            rprint("[red]✗[/red] Supabase configuration not found")
            sys.exit(1)

        # Initialize tracker
        storage = SupabaseStorage(
            url=cfg.supabase.url,
            key=cfg.supabase.key,
        )

        tracker = AsyncVersionTracker(storage=storage)
        await tracker.initialize()

        # Get versions
        doc_uuid = UUID(document_id)
        versions = await tracker.list_versions(doc_uuid)

        if not versions:
            rprint("[dim]No versions found[/dim]")
            await tracker.close()
            return

        # Create table
        table = Table(title=f"Version History: {document_id}")
        table.add_column("Version", justify="right", style="cyan")
        table.add_column("Change", style="magenta")
        table.add_column("Hash", style="dim")
        table.add_column("Size", justify="right")
        table.add_column("Created", style="yellow")

        for version in versions:
            size_kb = version.file_size / 1024
            size_str = f"{size_kb:.1f} KB"

            table.add_row(
                str(version.version_number),
                version.change_type.value,
                version.content_hash[:8],
                size_str,
                version.created_at.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)

        await tracker.close()

    except Exception as e:
        rprint(f"[red]✗[/red] Failed to get history: {e}")
        sys.exit(1)


@main.command()
@click.argument("document_id")
@click.option("--from-version", "-f", type=int, required=True, help="From version")
@click.option("--to-version", "-t", type=int, required=True, help="To version")
@click.option("--config", "-c", help="Path to config file")
@async_command
async def diff(document_id: str, from_version: int, to_version: int, config: Optional[str]):
    """Show diff between two versions."""
    try:
        from uuid import UUID

        # Load config
        cfg = RAGVersionConfig.load(config)

        if not cfg.supabase:
            rprint("[red]✗[/red] Supabase configuration not found")
            sys.exit(1)

        # Initialize tracker
        storage = SupabaseStorage(
            url=cfg.supabase.url,
            key=cfg.supabase.key,
        )

        tracker = AsyncVersionTracker(storage=storage)
        await tracker.initialize()

        # Get diff
        doc_uuid = UUID(document_id)
        diff_result = await tracker.get_diff(doc_uuid, from_version, to_version)

        if not diff_result:
            rprint("[dim]No diff available[/dim]")
            await tracker.close()
            return

        rprint(f"\n[bold]Diff: v{from_version} → v{to_version}[/bold]")
        rprint(f"[green]+ Additions: {diff_result.additions}[/green]")
        rprint(f"[red]- Deletions: {diff_result.deletions}[/red]")
        rprint("\n" + diff_result.diff_text)

        await tracker.close()

    except Exception as e:
        rprint(f"[red]✗[/red] Failed to get diff: {e}")
        sys.exit(1)


@main.command()
@click.option("--config", "-c", help="Path to config file")
@async_command
async def health(config: Optional[str]):
    """Check health of storage backend."""
    try:
        # Load config
        cfg = RAGVersionConfig.load(config)

        if not cfg.supabase:
            rprint("[red]✗[/red] Supabase configuration not found")
            sys.exit(1)

        # Initialize storage
        storage = SupabaseStorage(
            url=cfg.supabase.url,
            key=cfg.supabase.key,
        )

        await storage.initialize()

        # Health check
        is_healthy = await storage.health_check()

        if is_healthy:
            rprint("[green]✓[/green] Storage backend is healthy")
        else:
            rprint("[red]✗[/red] Storage backend is unhealthy")
            sys.exit(1)

        await storage.close()

    except Exception as e:
        rprint(f"[red]✗[/red] Health check failed: {e}")
        sys.exit(1)


@main.command()
@click.argument("document_id", required=False)
@click.option("--config", "-c", help="Path to config file")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@async_command
async def stats(document_id: Optional[str], config: Optional[str], format: str):
    """Display statistics and analytics.

    Examples:
        ragversion stats                    # Overall statistics
        ragversion stats <document-id>      # Document-specific stats
        ragversion stats --format json      # JSON output
    """
    try:
        # Load config
        cfg = RAGVersionConfig.load(config)

        if not cfg.supabase:
            rprint("[red]✗[/red] Supabase configuration not found")
            sys.exit(1)

        # Initialize tracker
        storage = SupabaseStorage(
            url=cfg.supabase.url,
            key=cfg.supabase.key,
        )

        tracker = AsyncVersionTracker(storage=storage)
        await tracker.initialize()

        if document_id:
            # Document-specific statistics
            from uuid import UUID

            doc_uuid = UUID(document_id)
            doc_stats = await tracker.get_document_statistics(doc_uuid)

            if format == "json":
                # JSON output
                output = {
                    "document_id": str(doc_stats.document_id),
                    "file_name": doc_stats.file_name,
                    "file_path": doc_stats.file_path,
                    "total_versions": doc_stats.total_versions,
                    "versions_by_change_type": doc_stats.versions_by_change_type,
                    "total_size_bytes": doc_stats.total_size_bytes,
                    "first_tracked": doc_stats.first_tracked.isoformat(),
                    "last_updated": doc_stats.last_updated.isoformat(),
                    "average_days_between_changes": doc_stats.average_days_between_changes,
                    "change_frequency": doc_stats.change_frequency,
                }
                print(json.dumps(output, indent=2))
            else:
                # Rich table output
                size_mb = doc_stats.total_size_bytes / (1024 * 1024)
                size_str = (
                    f"{size_mb:.2f} MB"
                    if size_mb >= 1
                    else f"{doc_stats.total_size_bytes / 1024:.2f} KB"
                )

                # Overview panel
                overview_text = f"""[bold]File:[/bold] {doc_stats.file_name}
[bold]Path:[/bold] {doc_stats.file_path}
[bold]Versions:[/bold] {doc_stats.total_versions}
[bold]First tracked:[/bold] {doc_stats.first_tracked.strftime("%Y-%m-%d %H:%M")}
[bold]Last updated:[/bold] {doc_stats.last_updated.strftime("%Y-%m-%d %H:%M")}
[bold]Total size:[/bold] {size_str}
[bold]Change frequency:[/bold] {doc_stats.change_frequency.upper()} (avg {doc_stats.average_days_between_changes:.1f} days)"""

                panel = Panel(overview_text, title="Document Statistics", border_style="cyan")
                console.print(panel)

                # Version breakdown table
                if doc_stats.versions_by_change_type:
                    rprint("\n[bold]Version Breakdown:[/bold]")
                    table = Table()
                    table.add_column("Change Type", style="magenta")
                    table.add_column("Count", justify="right", style="green")

                    for change_type, count in sorted(doc_stats.versions_by_change_type.items()):
                        table.add_row(change_type.title(), str(count))

                    console.print(table)

        else:
            # Overall statistics
            overall_stats = await tracker.get_statistics()

            if format == "json":
                # JSON output
                output = {
                    "total_documents": overall_stats.total_documents,
                    "total_versions": overall_stats.total_versions,
                    "total_storage_bytes": overall_stats.total_storage_bytes,
                    "average_versions_per_document": overall_stats.average_versions_per_document,
                    "documents_by_file_type": overall_stats.documents_by_file_type,
                    "recent_activity_count": overall_stats.recent_activity_count,
                    "oldest_document_date": (
                        overall_stats.oldest_document_date.isoformat()
                        if overall_stats.oldest_document_date
                        else None
                    ),
                    "newest_document_date": (
                        overall_stats.newest_document_date.isoformat()
                        if overall_stats.newest_document_date
                        else None
                    ),
                }
                print(json.dumps(output, indent=2))
            else:
                # Rich table output
                storage_mb = overall_stats.total_storage_bytes / (1024 * 1024)
                storage_str = (
                    f"{storage_mb:.2f} MB"
                    if storage_mb >= 1
                    else f"{overall_stats.total_storage_bytes / 1024:.2f} KB"
                )

                # Overview panel
                overview_text = f"""[bold]Total Documents:[/bold] {overall_stats.total_documents:,}
[bold]Total Versions:[/bold] {overall_stats.total_versions:,}
[bold]Storage Used:[/bold] {storage_str}
[bold]Avg Versions/Doc:[/bold] {overall_stats.average_versions_per_document:.2f}
[bold]Recent Activity:[/bold] {overall_stats.recent_activity_count} changes (last 7 days)"""

                if overall_stats.oldest_document_date:
                    overview_text += f"\n[bold]Oldest Document:[/bold] {overall_stats.oldest_document_date.strftime('%Y-%m-%d')}"
                if overall_stats.newest_document_date:
                    overview_text += f"\n[bold]Newest Document:[/bold] {overall_stats.newest_document_date.strftime('%Y-%m-%d')}"

                panel = Panel(overview_text, title="RAGVersion Statistics", border_style="cyan")
                console.print(panel)

                # Top documents table
                rprint("\n[bold]Top Documents by Version Count:[/bold]")
                top_docs = await tracker.get_top_documents(limit=10, order_by="version_count")

                if top_docs:
                    table = Table()
                    table.add_column("File Name", style="cyan")
                    table.add_column("Type", style="magenta")
                    table.add_column("Versions", justify="right", style="green")
                    table.add_column("Size", justify="right")

                    for doc in top_docs:
                        size_kb = doc.file_size / 1024
                        size_str = (
                            f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                        )

                        table.add_row(
                            doc.file_name,
                            doc.file_type,
                            str(doc.version_count),
                            size_str,
                        )

                    console.print(table)
                else:
                    rprint("[dim]No documents found[/dim]")

                # File type distribution table
                if overall_stats.documents_by_file_type:
                    rprint("\n[bold]File Type Distribution:[/bold]")
                    table = Table()
                    table.add_column("Type", style="magenta")
                    table.add_column("Count", justify="right", style="green")
                    table.add_column("Percent", justify="right", style="yellow")

                    total_docs = overall_stats.total_documents
                    for file_type, count in sorted(
                        overall_stats.documents_by_file_type.items(),
                        key=lambda x: x[1],
                        reverse=True,
                    ):
                        percent = (count / total_docs * 100) if total_docs > 0 else 0
                        table.add_row(file_type, str(count), f"{percent:.1f}%")

                    console.print(table)

        await tracker.close()

    except ValueError as e:
        rprint(f"[red]✗[/red] Invalid document ID: {e}")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]✗[/red] Failed to get statistics: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
