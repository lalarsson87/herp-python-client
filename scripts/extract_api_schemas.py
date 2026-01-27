#!/usr/bin/env python3
"""
Extract actual API response schemas from VCR cassettes

This script analyzes recorded VCR cassettes to extract the actual field
structures returned by the HERP API, helping verify TypedDict schemas.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, Set
from collections import defaultdict


def extract_fields(obj: Any, prefix: str = "") -> Set[str]:
    """Recursively extract all field paths from an object"""
    fields = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            field_path = f"{prefix}.{key}" if prefix else key
            fields.add(field_path)

            # Recurse into nested objects
            if isinstance(value, dict):
                fields.update(extract_fields(value, field_path))
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Sample first item in list
                fields.update(extract_fields(value[0], field_path))

    return fields


def analyze_cassette(cassette_path: Path) -> Dict[str, Any]:
    """Analyze a single cassette file"""
    with open(cassette_path, 'r', encoding='utf-8') as f:
        cassette = yaml.safe_load(f)

    results = {
        'file': cassette_path.name,
        'interactions': [],
        'schemas': defaultdict(lambda: {'fields': set(), 'samples': []})
    }

    if 'interactions' not in cassette:
        return results

    for interaction in cassette['interactions']:
        if 'response' not in interaction or 'body' not in interaction['response']:
            continue

        body = interaction['response']['body']
        if not isinstance(body, dict) or 'string' not in body:
            continue

        try:
            data = json.loads(body['string'])

            # Extract endpoint from request
            uri = interaction['request']['uri']
            endpoint = uri.split('/v1/')[-1].split('?')[0]

            # Analyze different response types
            if 'candidacies' in data:
                schema_name = 'HerpCandidacyResponse'
                for candidacy in data['candidacies']:
                    fields = extract_fields(candidacy)
                    results['schemas'][schema_name]['fields'].update(fields)
                    if len(results['schemas'][schema_name]['samples']) < 2:
                        results['schemas'][schema_name]['samples'].append(candidacy)

            elif 'contacts' in data:
                schema_name = 'HerpContactResponse'
                for contact in data['contacts']:
                    fields = extract_fields(contact)
                    results['schemas'][schema_name]['fields'].update(fields)
                    if len(results['schemas'][schema_name]['samples']) < 2:
                        results['schemas'][schema_name]['samples'].append(contact)

            elif 'evaluations' in data:
                schema_name = 'HerpEvaluationResponse'
                for evaluation in data['evaluations']:
                    fields = extract_fields(evaluation)
                    results['schemas'][schema_name]['fields'].update(fields)
                    if len(results['schemas'][schema_name]['samples']) < 2:
                        results['schemas'][schema_name]['samples'].append(evaluation)

            elif 'files' in data:
                schema_name = 'HerpFileResponse'
                for file in data['files']:
                    fields = extract_fields(file)
                    results['schemas'][schema_name]['fields'].update(fields)
                    if len(results['schemas'][schema_name]['samples']) < 2:
                        results['schemas'][schema_name]['samples'].append(file)

            elif 'requisitions' in data:
                schema_name = 'HerpRequisitionResponse'
                for requisition in data['requisitions']:
                    fields = extract_fields(requisition)
                    results['schemas'][schema_name]['fields'].update(fields)
                    if len(results['schemas'][schema_name]['samples']) < 2:
                        results['schemas'][schema_name]['samples'].append(requisition)

            elif 'users' in data:
                schema_name = 'HerpUserResponse'
                for user in data['users']:
                    fields = extract_fields(user)
                    results['schemas'][schema_name]['fields'].update(fields)
                    if len(results['schemas'][schema_name]['samples']) < 2:
                        results['schemas'][schema_name]['samples'].append(user)

            elif 'id' in data:
                # Single object response - determine type from endpoint
                if 'candidacies' in endpoint:
                    schema_name = 'HerpCandidacyResponse'
                elif 'contacts' in endpoint:
                    schema_name = 'HerpContactResponse'
                elif 'evaluations' in endpoint:
                    schema_name = 'HerpEvaluationResponse'
                else:
                    schema_name = 'UnknownResponse'

                fields = extract_fields(data)
                results['schemas'][schema_name]['fields'].update(fields)
                if len(results['schemas'][schema_name]['samples']) < 2:
                    results['schemas'][schema_name]['samples'].append(data)

        except json.JSONDecodeError:
            continue

    return results


def main():
    """Main entry point"""
    cassettes_dir = Path(__file__).parent.parent / 'tests' / 'integration' / 'fixtures' / 'cassettes'

    if not cassettes_dir.exists():
        print(f"❌ Cassettes directory not found: {cassettes_dir}")
        return 1

    print("Analyzing VCR cassettes for API response schemas...\n")

    # Aggregate results across all cassettes
    all_schemas = defaultdict(lambda: {'fields': set(), 'samples': []})

    cassette_files = sorted(cassettes_dir.glob('*.yaml'))
    for cassette_path in cassette_files:
        print(f"📂 {cassette_path.name}")
        results = analyze_cassette(cassette_path)

        for schema_name, schema_data in results['schemas'].items():
            all_schemas[schema_name]['fields'].update(schema_data['fields'])

            # Keep diverse samples
            for sample in schema_data['samples']:
                if len(all_schemas[schema_name]['samples']) < 3:
                    all_schemas[schema_name]['samples'].append(sample)

    print("\n" + "="*80)
    print("EXTRACTED API SCHEMAS")
    print("="*80 + "\n")

    for schema_name in sorted(all_schemas.keys()):
        schema_data = all_schemas[schema_name]
        fields = sorted(schema_data['fields'])

        print(f"\n{schema_name}")
        print("-" * len(schema_name))
        print(f"Fields ({len(fields)}):")

        # Group by top-level vs nested
        top_level = [f for f in fields if '.' not in f]
        nested = [f for f in fields if '.' in f]

        if top_level:
            print("\nTop-level fields:")
            for field in top_level:
                print(f"  - {field}")

        if nested:
            print("\nNested fields:")
            for field in nested:
                print(f"  - {field}")

        # Show sample data for understanding types
        if schema_data['samples']:
            print(f"\nSample data (first occurrence):")
            sample = schema_data['samples'][0]
            # Only show top-level structure
            print("  {")
            for key, value in sorted(sample.items()):
                if isinstance(value, (dict, list)):
                    if isinstance(value, list):
                        type_info = f"List[{type(value[0]).__name__}]" if value else "List[]"
                    else:
                        type_info = "Dict"
                    print(f"    {key!r}: {type_info}")
                else:
                    print(f"    {key!r}: {value!r}")
            print("  }")

        print()

    return 0


if __name__ == '__main__':
    exit(main())
