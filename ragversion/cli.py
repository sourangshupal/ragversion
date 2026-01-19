"""Command-line interface for RAGVersion."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ragversion import AsyncVersionTracker, __version__
from ragversion.config import RAGVersionConfig
from ragversion.storage import SupabaseStorage

console = Console()


def async_command(f):
    """Decorator to run async Click commands."""

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


if __name__ == "__main__":
    main()
