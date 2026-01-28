"""
HERP CLI Commands

Provides command-line interface for common HERP operations.

Usage:
    herp-client --help
    herp-client sync --full
    herp-client export candidacies --format csv --output data.csv
    herp-client health-check
    herp-client validate-config
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from ..core.herp import HerpClient
from ..core.herp.export import CandidacyExporter
from ..core.utils.config import load_herp_config
from ..core.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="herp-client")
@click.pass_context
def cli(ctx):
    """HERP Python Client - Command-line interface for HERP API operations"""
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    "--full",
    is_flag=True,
    help="Perform full sync (all candidacies)",
)
@click.option(
    "--since",
    type=str,
    help="Sync candidacies updated since (ISO 8601 datetime)",
)
@click.option(
    "--days",
    type=int,
    help="Sync candidacies from last N days",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be synced without syncing",
)
def sync(full: bool, since: Optional[str], days: Optional[int], dry_run: bool):
    """Sync candidacies from HERP API"""
    try:
        config = load_herp_config()
        client = HerpClient(config)

        # Determine sync timeframe
        if days:
            since_dt = datetime.now() - timedelta(days=days)
            since = since_dt.isoformat()
        elif not full and not since:
            # Default: last 7 days
            since_dt = datetime.now() - timedelta(days=7)
            since = since_dt.isoformat()

        if dry_run:
            click.echo("[DRY RUN] Would sync candidacies...")
            if full:
                click.echo("  Scope: All candidacies")
            else:
                click.echo(f"  Scope: Updated since {since}")
            return

        # Perform sync
        click.echo("Syncing candidacies...")
        if full:
            click.echo("  Scope: All candidacies (this may take a while)")
            candidacies = client.candidacies.fetch_all()
        else:
            click.echo(f"  Scope: Updated since {since}")
            candidacies = client.candidacies.fetch_all(updated_since=since)

        click.echo(f"✓ Synced {len(candidacies):,} candidacies")

    except Exception as e:
        click.echo(f"✗ Sync failed: {e}", err=True)
        logger.error(f"Sync failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument("resource", type=click.Choice(["candidacies"]))
@click.option(
    "--format",
    type=click.Choice(["csv", "jsonl", "json"]),
    default="csv",
    help="Export format",
)
@click.option(
    "--output",
    type=click.Path(),
    required=True,
    help="Output file path",
)
@click.option(
    "--since",
    type=str,
    help="Export records updated since (ISO 8601 datetime)",
)
@click.option(
    "--fields",
    type=str,
    help="Comma-separated list of fields to export",
)
@click.option(
    "--max-records",
    type=int,
    help="Maximum number of records to export",
)
def export(
    resource: str,
    format: str,
    output: str,
    since: Optional[str],
    fields: Optional[str],
    max_records: Optional[int],
):
    """Export HERP data to file"""
    try:
        config = load_herp_config()
        client = HerpClient(config)

        # Parse fields
        field_list = fields.split(",") if fields else None

        click.echo(f"Exporting {resource} to {output}...")

        if resource == "candidacies":
            exporter = CandidacyExporter(client)

            if format == "csv":
                count = exporter.export_to_csv(
                    output, updated_since=since, fields=field_list
                )
            elif format == "jsonl":
                count = exporter.export_to_jsonl(
                    output, updated_since=since, fields=field_list
                )
            elif format == "json":
                count = exporter.export_to_json(
                    output,
                    updated_since=since,
                    fields=field_list,
                    max_records=max_records,
                )

            click.echo(f"✓ Exported {count:,} {resource} to {output}")

    except Exception as e:
        click.echo(f"✗ Export failed: {e}", err=True)
        logger.error(f"Export failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command("health-check")
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed health information",
)
def health_check(verbose: bool):
    """Check HERP client health and connectivity"""
    try:
        from ..core.utils.health import perform_health_check

        click.echo("Performing health check...")
        results = perform_health_check()

        # Display results
        all_healthy = True
        for check_name, result in results.items():
            status = "✓" if result["healthy"] else "✗"
            click.echo(f"{status} {check_name}: {result['message']}")

            if verbose and "details" in result:
                for key, value in result["details"].items():
                    click.echo(f"    {key}: {value}")

            if not result["healthy"]:
                all_healthy = False

        if all_healthy:
            click.echo("\n✓ All health checks passed")
            sys.exit(0)
        else:
            click.echo("\n✗ Some health checks failed", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"✗ Health check failed: {e}", err=True)
        logger.error(f"Health check failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command("validate-config")
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Path to config file (.env)",
)
def validate_config(config_file: Optional[str]):
    """Validate HERP configuration"""
    try:
        from ..core.utils.health import validate_configuration

        click.echo("Validating configuration...")

        # Load config
        if config_file:
            import os

            from dotenv import load_dotenv

            load_dotenv(config_file)

        results = validate_configuration()

        # Display results
        all_valid = True
        for check_name, result in results.items():
            status = "✓" if result["valid"] else "✗"
            click.echo(f"{status} {check_name}: {result['message']}")

            if not result["valid"]:
                all_valid = False
                if "suggestion" in result:
                    click.echo(f"    Suggestion: {result['suggestion']}")

        if all_valid:
            click.echo("\n✓ Configuration is valid")
            sys.exit(0)
        else:
            click.echo("\n✗ Configuration has issues", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"✗ Configuration validation failed: {e}", err=True)
        logger.error(f"Configuration validation failed: {e}", exc_info=True)
        sys.exit(1)


@cli.group()
def webhooks():
    """Webhook-related commands"""
    pass


@webhooks.command("test-event")
@click.option(
    "--event-type",
    type=click.Choice(
        [
            "candidacy.created",
            "candidacy.step_changed",
            "candidacy.terminated",
            "contact.created",
        ]
    ),
    default="candidacy.created",
    help="Event type to test",
)
@click.option(
    "--payload-file",
    type=click.Path(exists=True),
    help="JSON file with event payload",
)
def test_event(event_type: str, payload_file: Optional[str]):
    """Test webhook event handling"""
    import json

    try:
        from ..core.herp.webhooks import WebhookHandler

        click.echo(f"Testing webhook event: {event_type}")

        # Load or generate payload
        if payload_file:
            with open(payload_file, "r") as f:
                payload = json.load(f)
        else:
            # Generate sample payload
            payload = {
                "event": event_type,
                "event_id": "test_event_001",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "candidacy_id": "test_cand_123",
                    "name": "Test Candidate",
                },
            }

        # Create handler
        handler = WebhookHandler()

        @handler.on(event_type)
        def test_handler(event):
            click.echo(f"  Event received: {event.event_type}")
            click.echo(f"  Event ID: {event.event_id}")
            click.echo(f"  Data: {event.data}")

        # Process event
        handler.handle(payload)

        click.echo("✓ Event processed successfully")

    except Exception as e:
        click.echo(f"✗ Event processing failed: {e}", err=True)
        logger.error(f"Event processing failed: {e}", exc_info=True)
        sys.exit(1)


@webhooks.command("replay")
@click.option(
    "--event-id",
    type=str,
    help="Specific event ID to replay",
)
@click.option(
    "--event-type",
    type=str,
    help="Event type to replay (all matching events)",
)
@click.option(
    "--since",
    type=str,
    help="Replay events since (ISO 8601 datetime)",
)
@click.option(
    "--failed-only",
    is_flag=True,
    help="Replay only failed events",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be replayed without replaying",
)
def replay_events(
    event_id: Optional[str],
    event_type: Optional[str],
    since: Optional[str],
    failed_only: bool,
    dry_run: bool,
):
    """Replay stored webhook events"""
    try:
        from ..core.herp.webhooks import EventReplayer, EventStore, WebhookRouter

        click.echo("Replaying webhook events...")

        # Setup
        event_store = EventStore()
        router = WebhookRouter()
        replayer = EventReplayer(router, event_store)

        # Determine replay strategy
        since_dt = datetime.fromisoformat(since) if since else None

        if event_id:
            click.echo(f"  Replaying event: {event_id}")
            success = replayer.replay_event_by_id(event_id, dry_run=dry_run)
            if success:
                click.echo("✓ Event replayed successfully")
            else:
                click.echo("✗ Event replay failed", err=True)
                sys.exit(1)

        elif failed_only:
            click.echo("  Replaying failed events...")
            result = replayer.replay_failed_events(since=since_dt, dry_run=dry_run)
            click.echo(f"✓ Replayed {result['successful']}/{result['total']} events")

        else:
            click.echo(f"  Replaying events (type={event_type}, since={since})...")
            result = replayer.replay_events(
                event_type=event_type, since=since_dt, dry_run=dry_run
            )
            click.echo(f"✓ Replayed {result['successful']}/{result['total']} events")

    except Exception as e:
        click.echo(f"✗ Replay failed: {e}", err=True)
        logger.error(f"Replay failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
