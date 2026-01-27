#!/usr/bin/env python3
"""
Batch Operations Examples

Demonstrates how to use BatchNotionClient for efficient bulk operations:
1. Batch block appending
2. Batch page updates
3. Batch page creation
4. Error handling with partial failures
5. Performance comparison
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.notion.batch_client import BatchNotionClient, BatchResult
from src.core.notion.client import NotionConfig


# ============================================================================
# Example 1: Batch Block Appending
# ============================================================================

def example_batch_append_blocks():
    """Demonstrate batch block appending"""
    print("\n" + "="*60)
    print("Example 1: Batch Block Appending")
    print("="*60)

    print("\nScenario: Adding 250 paragraph blocks to a page")
    print("  Without batching: 250 API calls (~85 seconds)")
    print("  With batching: 3 API calls (~1 second)")
    print("  Improvement: 98% fewer API calls, 85x faster")

    # Create sample blocks
    blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": f"Paragraph {i}"}}]
            }
        }
        for i in range(250)
    ]

    print(f"\nCreated {len(blocks)} blocks to append")
    print("\nUsage:")
    print("""
    config = NotionConfig(api_key="...", candidates_db_id="...")
    client = BatchNotionClient(config)

    result = client.batch_append_blocks("page-id", blocks)

    print(f"Added {result.total_blocks} blocks")
    print(f"API calls: {result.chunks_processed}")
    print(f"Success rate: {result.success_rate:.1f}%")
    """)

    # Note: Actual execution requires valid Notion credentials
    print("\nNote: This example requires valid Notion API credentials to execute.")


# ============================================================================
# Example 2: Batch Page Updates
# ============================================================================

def example_batch_update_pages():
    """Demonstrate batch page updates"""
    print("\n" + "="*60)
    print("Example 2: Batch Page Updates")
    print("="*60)

    print("\nScenario: Updating hiring stage for 50 candidates")
    print("  Updates all pages with rate limiting")
    print("  Handles partial failures gracefully")

    # Prepare updates
    updates = [
        {
            "page_id": f"page-{i}",
            "properties": {
                "Hiring Stage": {"status": {"name": "1次選考"}},
                "Last Updated": {"date": {"start": "2024-01-20"}}
            }
        }
        for i in range(50)
    ]

    print(f"\nPrepared {len(updates)} page updates")
    print("\nUsage:")
    print("""
    result = client.batch_update_pages(updates, respect_rate_limit=True)

    print(f"Updated: {result.successful}/{result.total_items}")
    print(f"Failed: {result.failed}")
    print(f"Success rate: {result.success_rate:.1f}%")

    # Check errors
    if result.errors:
        for error in result.errors:
            print(f"Failed page {error['page_id']}: {error['error']}")
    """)


# ============================================================================
# Example 3: Batch Page Creation
# ============================================================================

def example_batch_create_pages():
    """Demonstrate batch page creation"""
    print("\n" + "="*60)
    print("Example 3: Batch Page Creation")
    print("="*60)

    print("\nScenario: Creating 20 new candidate pages")
    print("  Creates all pages with rate limiting")
    print("  Returns created page IDs for further processing")

    # Prepare pages
    pages = [
        {
            "parent": {"database_id": "database-id-here"},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": f"Candidate {i}"}}]
                },
                "Email": {
                    "email": f"candidate{i}@example.com"
                },
                "Hiring Stage": {
                    "status": {"name": "Not started"}
                },
                "Applied Date": {
                    "date": {"start": "2024-01-20"}
                }
            }
        }
        for i in range(20)
    ]

    print(f"\nPrepared {len(pages)} pages to create")
    print("\nUsage:")
    print("""
    result = client.batch_create_pages(pages)

    print(f"Created: {result.successful}/{result.total_items}")

    # Get created page IDs
    for response in result.responses:
        page_id = response['id']
        print(f"Created page: {page_id}")
    """)


# ============================================================================
# Example 4: Error Handling with Partial Failures
# ============================================================================

def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "="*60)
    print("Example 4: Error Handling with Partial Failures")
    print("="*60)

    print("\nScenario: Some updates succeed, some fail")
    print("  BatchNotionClient handles partial failures gracefully")
    print("  Returns detailed error information")

    print("\nExample error handling pattern:")
    print("""
    result = client.batch_update_pages(updates)

    # Check overall success
    if result.success_rate < 100:
        print(f"Warning: {result.failed} updates failed")

        # Log detailed errors
        for error in result.errors:
            logger.error(
                f"Failed to update page at index {error['index']}",
                page_id=error.get('page_id'),
                error_type=error['error_type'],
                error_message=error['error']
            )

        # Decide what to do
        if result.success_rate < 50:
            # Too many failures - abort and retry
            raise Exception("Batch operation mostly failed")
        else:
            # Some failures acceptable - continue with successful items
            for response in result.responses:
                process_successful_update(response)

    # All succeeded
    else:
        print(f"All {result.total_items} updates succeeded!")
    """)


# ============================================================================
# Example 5: Performance Comparison
# ============================================================================

def example_performance_comparison():
    """Demonstrate performance improvements"""
    print("\n" + "="*60)
    print("Example 5: Performance Comparison")
    print("="*60)

    scenarios = [
        {
            "operation": "Append 100 blocks",
            "without_batch": "100 API calls, ~34s",
            "with_batch": "1 API call, ~0.4s",
            "improvement": "100x faster"
        },
        {
            "operation": "Append 250 blocks",
            "without_batch": "250 API calls, ~85s",
            "with_batch": "3 API calls, ~1.2s",
            "improvement": "71x faster"
        },
        {
            "operation": "Update 50 pages",
            "without_batch": "50 API calls, ~17s",
            "with_batch": "50 API calls, ~17s",
            "improvement": "Same (rate limiting applied)"
        },
        {
            "operation": "Create 20 pages",
            "without_batch": "20 API calls, ~7s",
            "with_batch": "20 API calls, ~7s",
            "improvement": "Same (rate limiting applied)"
        }
    ]

    print("\nPerformance Comparison:")
    print("-" * 60)
    print(f"{'Operation':<20} {'Without Batch':<20} {'With Batch':<15} {'Improvement':<15}")
    print("-" * 60)

    for scenario in scenarios:
        print(
            f"{scenario['operation']:<20} "
            f"{scenario['without_batch']:<20} "
            f"{scenario['with_batch']:<15} "
            f"{scenario['improvement']:<15}"
        )

    print("\nKey Takeaway:")
    print("  - Block appending benefits most from batching (up to 100x faster)")
    print("  - Page updates/creation still benefit from unified error handling")
    print("  - Rate limiting is automatically applied across all operations")


# ============================================================================
# Example 6: Real-World Sync Pattern
# ============================================================================

def example_real_world_sync():
    """Demonstrate real-world sync pattern"""
    print("\n" + "="*60)
    print("Example 6: Real-World Sync Pattern")
    print("="*60)

    print("\nComplete sync workflow using batch operations:")
    print("""
    def sync_candidates(herp_candidates, notion_client):
        # Prepare batch operations
        pages_to_create = []
        pages_to_update = []

        for candidate in herp_candidates:
            notion_page = find_notion_page(candidate['id'])

            if notion_page:
                # Existing page - prepare update
                pages_to_update.append({
                    'page_id': notion_page['id'],
                    'properties': build_properties(candidate)
                })
            else:
                # New candidate - prepare creation
                pages_to_create.append({
                    'parent': {'database_id': DB_ID},
                    'properties': build_properties(candidate)
                })

        # Execute batch operations
        metrics = {
            'created': 0,
            'updated': 0,
            'failed': 0
        }

        # Batch create
        if pages_to_create:
            result = notion_client.batch_create_pages(pages_to_create)
            metrics['created'] = result.successful
            metrics['failed'] += result.failed

            # Cache created pages
            for response in result.responses:
                cache.set(f"page:{response['id']}", response)

        # Batch update
        if pages_to_update:
            result = notion_client.batch_update_pages(pages_to_update)
            metrics['updated'] = result.successful
            metrics['failed'] += result.failed

        return metrics

    # Run sync
    metrics = sync_candidates(candidates, notion_client)
    print(f"Synced {metrics['created']} new, {metrics['updated']} updated")
    print(f"Failures: {metrics['failed']}")
    """)


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*13 + "BATCH OPERATIONS EXAMPLES" + " "*20 + "║")
    print("╚" + "="*58 + "╝")

    example_batch_append_blocks()
    example_batch_update_pages()
    example_batch_create_pages()
    example_error_handling()
    example_performance_comparison()
    example_real_world_sync()

    print("\n" + "="*60)
    print("All examples complete!")
    print("="*60 + "\n")
