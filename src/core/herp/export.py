#!/usr/bin/env python3
"""
HERP Data Export Utilities

Provides utilities for exporting HERP data to various formats (CSV, JSONL, JSON).
Supports streaming for memory-efficient processing of large datasets.
"""

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Literal, Optional

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .client import HerpClient

logger = get_logger(__name__)

ExportFormat = Literal["csv", "jsonl", "json"]


class CandidacyExporter:
    """
    Export candidacies to various formats

    Supports CSV, JSONL (JSON Lines), and JSON formats.
    Uses streaming for memory-efficient processing of large datasets.

    Example:
        >>> from src.core.herp import HerpClient
        >>> from src.core.herp.export import CandidacyExporter
        >>>
        >>> client = HerpClient(config)
        >>> exporter = CandidacyExporter(client)
        >>>
        >>> # Export to CSV
        >>> exporter.export_to_csv("candidacies_2026.csv")
        >>>
        >>> # Export with filters
        >>> exporter.export_to_csv(
        ...     "recent_candidacies.csv",
        ...     updated_since="2026-01-20T00:00:00Z",
        ...     fields=["id", "name", "email", "status"]
        ... )
        >>>
        >>> # Export to JSONL for data pipelines
        >>> exporter.export_to_jsonl("candidacies.jsonl")
    """

    def __init__(self, client: "HerpClient"):
        """
        Initialize candidacy exporter

        Args:
            client: HERP client instance
        """
        self.client = client

    def export_to_csv(
        self,
        output_file: str,
        updated_since: Optional[str] = None,
        fields: Optional[List[str]] = None,
        chunk_size: int = 100,
    ) -> int:
        """
        Export candidacies to CSV file

        Streams candidacies to CSV for memory efficiency.
        Automatically handles field extraction and CSV formatting.

        Args:
            output_file: Output CSV file path
            updated_since: ISO 8601 datetime to filter by update time
            fields: List of fields to export (None = all fields)
            chunk_size: Number of records per page (default: 100)

        Returns:
            Number of candidacies exported

        Example:
            >>> exporter.export_to_csv(
            ...     "candidacies.csv",
            ...     updated_since="2026-01-01T00:00:00Z",
            ...     fields=["id", "name", "email", "appliedAt", "status"]
            ... )
            Exported 1,523 candidacies to candidacies.csv
            1523
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0
        writer = None
        fieldnames = None

        logger.info(f"Starting CSV export to {output_file}")

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            # Stream candidacies (memory efficient)
            for candidacy in self.client.candidacies.stream(
                updated_since=updated_since, chunk_size=chunk_size
            ):
                # Initialize writer with headers from first row
                if writer is None:
                    # Determine fields to export
                    if fields:
                        fieldnames = fields
                    else:
                        fieldnames = list(candidacy.keys())

                    writer = csv.DictWriter(
                        csvfile, fieldnames=fieldnames, extrasaction="ignore"
                    )
                    writer.writeheader()

                # Filter fields if specified
                if fields:
                    row = {k: candidacy.get(k) for k in fields}
                else:
                    row = candidacy

                writer.writerow(row)
                count += 1

                if count % 1000 == 0:
                    logger.info(f"Exported {count:,} candidacies...")

        logger.info(f"Exported {count:,} candidacies to {output_file}")
        return count

    def export_to_jsonl(
        self,
        output_file: str,
        updated_since: Optional[str] = None,
        fields: Optional[List[str]] = None,
        chunk_size: int = 100,
    ) -> int:
        """
        Export candidacies to JSON Lines format

        JSON Lines format (one JSON object per line) is ideal for:
        - Data pipelines and streaming processing
        - Large datasets that don't fit in memory
        - Line-by-line processing tools

        Args:
            output_file: Output JSONL file path
            updated_since: ISO 8601 datetime to filter by update time
            fields: List of fields to export (None = all fields)
            chunk_size: Number of records per page (default: 100)

        Returns:
            Number of candidacies exported

        Example:
            >>> exporter.export_to_jsonl("candidacies.jsonl")
            Exported 5,234 candidacies to candidacies.jsonl
            5234
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0

        logger.info(f"Starting JSONL export to {output_file}")

        with open(output_path, "w", encoding="utf-8") as f:
            for candidacy in self.client.candidacies.stream(
                updated_since=updated_since, chunk_size=chunk_size
            ):
                # Filter fields if specified
                if fields:
                    record = {k: candidacy.get(k) for k in fields}
                else:
                    record = candidacy

                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

                if count % 1000 == 0:
                    logger.info(f"Exported {count:,} candidacies...")

        logger.info(f"Exported {count:,} candidacies to {output_file}")
        return count

    def export_to_json(
        self,
        output_file: str,
        updated_since: Optional[str] = None,
        fields: Optional[List[str]] = None,
        max_records: Optional[int] = None,
    ) -> int:
        """
        Export candidacies to standard JSON format

        Warning:
            This loads all records into memory. Use export_to_jsonl()
            for large datasets (10,000+ records).

        Args:
            output_file: Output JSON file path
            updated_since: ISO 8601 datetime to filter by update time
            fields: List of fields to export (None = all fields)
            max_records: Maximum number of records to export (None = all)

        Returns:
            Number of candidacies exported

        Example:
            >>> exporter.export_to_json(
            ...     "candidacies.json",
            ...     max_records=5000,
            ...     fields=["id", "name", "email"]
            ... )
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting JSON export to {output_file}")

        # Collect all candidacies
        candidacies = []
        for candidacy in self.client.candidacies.stream(updated_since=updated_since):
            # Filter fields if specified
            if fields:
                record = {k: candidacy.get(k) for k in fields}
            else:
                record = candidacy

            candidacies.append(record)

            if max_records and len(candidacies) >= max_records:
                logger.info(f"Reached max_records limit: {max_records}")
                break

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(candidacies, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(candidacies):,} candidacies to {output_file}")
        return len(candidacies)

    def export(
        self,
        output_file: str,
        format: ExportFormat = "csv",
        **kwargs,
    ) -> int:
        """
        Export candidacies to specified format

        Convenience method that delegates to format-specific methods.

        Args:
            output_file: Output file path
            format: Export format ("csv", "jsonl", or "json")
            **kwargs: Additional arguments passed to format-specific method

        Returns:
            Number of candidacies exported

        Example:
            >>> exporter.export("candidacies.csv", format="csv")
            >>> exporter.export("candidacies.jsonl", format="jsonl")
            >>> exporter.export("candidacies.json", format="json")
        """
        if format == "csv":
            return self.export_to_csv(output_file, **kwargs)
        elif format == "jsonl":
            return self.export_to_jsonl(output_file, **kwargs)
        elif format == "json":
            return self.export_to_json(output_file, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")


class DataExporter:
    """
    Generic data exporter for any HERP resource

    Provides flexible export capabilities for candidacies, contacts,
    requisitions, and other HERP resources.

    Example:
        >>> exporter = DataExporter(client)
        >>>
        >>> # Export candidacies
        >>> exporter.export_resource(
        ...     resource_iter=client.candidacies.stream(),
        ...     output_file="candidacies.csv",
        ...     format="csv"
        ... )
        >>>
        >>> # Export requisitions
        >>> exporter.export_resource(
        ...     resource_iter=iter(client.master_data.list_requisitions()),
        ...     output_file="requisitions.json",
        ...     format="json"
        ... )
    """

    def __init__(self, client: "HerpClient"):
        """
        Initialize data exporter

        Args:
            client: HERP client instance
        """
        self.client = client

    def export_resource(
        self,
        resource_iter: Iterator[Dict[str, Any]],
        output_file: str,
        format: ExportFormat = "csv",
        fields: Optional[List[str]] = None,
    ) -> int:
        """
        Export any resource to file

        Generic export method that works with any iterable of dictionaries.

        Args:
            resource_iter: Iterator of resource dictionaries
            output_file: Output file path
            format: Export format ("csv", "jsonl", or "json")
            fields: List of fields to export (None = all fields)

        Returns:
            Number of resources exported

        Example:
            >>> # Export contacts for multiple candidacies
            >>> contacts = []
            >>> for cand_id in candidacy_ids:
            ...     contacts.extend(client.contacts.list(cand_id))
            >>>
            >>> exporter.export_resource(
            ...     resource_iter=iter(contacts),
            ...     output_file="all_contacts.csv",
            ...     format="csv"
            ... )
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "csv":
            return self._export_csv(resource_iter, output_path, fields)
        elif format == "jsonl":
            return self._export_jsonl(resource_iter, output_path, fields)
        elif format == "json":
            return self._export_json(resource_iter, output_path, fields)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_csv(
        self,
        resource_iter: Iterator[Dict[str, Any]],
        output_path: Path,
        fields: Optional[List[str]],
    ) -> int:
        """Export to CSV format"""
        count = 0
        writer = None
        fieldnames = None

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            for resource in resource_iter:
                if writer is None:
                    fieldnames = fields if fields else list(resource.keys())
                    writer = csv.DictWriter(
                        csvfile, fieldnames=fieldnames, extrasaction="ignore"
                    )
                    writer.writeheader()

                row = {k: resource.get(k) for k in fieldnames}
                writer.writerow(row)
                count += 1

        logger.info(f"Exported {count:,} resources to {output_path}")
        return count

    def _export_jsonl(
        self,
        resource_iter: Iterator[Dict[str, Any]],
        output_path: Path,
        fields: Optional[List[str]],
    ) -> int:
        """Export to JSONL format"""
        count = 0

        with open(output_path, "w", encoding="utf-8") as f:
            for resource in resource_iter:
                record = {k: resource.get(k) for k in fields} if fields else resource
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                count += 1

        logger.info(f"Exported {count:,} resources to {output_path}")
        return count

    def _export_json(
        self,
        resource_iter: Iterator[Dict[str, Any]],
        output_path: Path,
        fields: Optional[List[str]],
    ) -> int:
        """Export to JSON format"""
        resources = []

        for resource in resource_iter:
            record = {k: resource.get(k) for k in fields} if fields else resource
            resources.append(record)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resources, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(resources):,} resources to {output_path}")
        return len(resources)
