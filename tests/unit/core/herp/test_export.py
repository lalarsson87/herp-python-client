"""
Tests for HERP Export Functionality
"""

import csv
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.core.herp.export import CandidacyExporter, DataExporter


class TestCandidacyExporter:
    """Test CandidacyExporter class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HerpClient"""
        client = Mock()
        client.candidacies = Mock()
        return client

    @pytest.fixture
    def exporter(self, mock_client):
        """Create CandidacyExporter instance"""
        return CandidacyExporter(mock_client)

    def test_initialization(self, mock_client):
        """Test exporter initialization"""
        exporter = CandidacyExporter(mock_client)

        assert exporter.client == mock_client

    def test_export_to_csv_creates_file(self, exporter, mock_client, tmp_path):
        """Test export_to_csv creates CSV file"""
        # Mock streaming candidacies
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe", "email": "john@example.com"},
                    {"id": "cand_2", "name": "Jane Smith", "email": "jane@example.com"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.csv"

        count = exporter.export_to_csv(str(output_file))

        assert count == 2
        assert output_file.exists()

    def test_export_to_csv_correct_content(self, exporter, mock_client, tmp_path):
        """Test export_to_csv writes correct CSV content"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe"},
                    {"id": "cand_2", "name": "Jane Smith"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.csv"
        exporter.export_to_csv(str(output_file))

        # Read and verify CSV
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 2
            assert rows[0]["id"] == "cand_1"
            assert rows[0]["name"] == "John Doe"
            assert rows[1]["name"] == "Jane Smith"

    def test_export_to_csv_with_fields_filter(self, exporter, mock_client, tmp_path):
        """Test export_to_csv with specific fields"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {
                        "id": "cand_1",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "status": "active",
                    },
                ]
            )
        )

        output_file = tmp_path / "candidacies.csv"
        exporter.export_to_csv(str(output_file), fields=["id", "name"])

        # Read and verify only specified fields
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 1
            assert rows[0]["id"] == "cand_1"
            assert rows[0]["name"] == "John Doe"
            # email and status should not be in output
            assert "email" not in rows[0] or rows[0]["email"] == ""
            assert "status" not in rows[0] or rows[0]["status"] == ""

    def test_export_to_csv_creates_nested_directories(
        self, exporter, mock_client, tmp_path
    ):
        """Test export_to_csv creates parent directories"""
        mock_client.candidacies.stream = Mock(return_value=iter([{"id": "cand_1"}]))

        output_file = tmp_path / "exports" / "2026" / "candidacies.csv"

        exporter.export_to_csv(str(output_file))

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_export_to_csv_passes_updated_since(self, exporter, mock_client, tmp_path):
        """Test export_to_csv passes updated_since parameter"""
        mock_client.candidacies.stream = Mock(return_value=iter([]))

        output_file = tmp_path / "candidacies.csv"
        exporter.export_to_csv(
            str(output_file), updated_since="2026-01-20T00:00:00Z", chunk_size=50
        )

        # Verify stream was called with correct parameters
        mock_client.candidacies.stream.assert_called_once_with(
            updated_since="2026-01-20T00:00:00Z", chunk_size=50
        )

    def test_export_to_csv_empty_dataset(self, exporter, mock_client, tmp_path):
        """Test export_to_csv with no records"""
        mock_client.candidacies.stream = Mock(return_value=iter([]))

        output_file = tmp_path / "candidacies.csv"
        count = exporter.export_to_csv(str(output_file))

        assert count == 0
        assert output_file.exists()
        # File should be empty (no header if no records)
        assert output_file.stat().st_size == 0

    def test_export_to_jsonl_creates_file(self, exporter, mock_client, tmp_path):
        """Test export_to_jsonl creates JSONL file"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe"},
                    {"id": "cand_2", "name": "Jane Smith"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.jsonl"

        count = exporter.export_to_jsonl(str(output_file))

        assert count == 2
        assert output_file.exists()

    def test_export_to_jsonl_correct_format(self, exporter, mock_client, tmp_path):
        """Test export_to_jsonl writes correct JSONL format (one JSON per line)"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe"},
                    {"id": "cand_2", "name": "Jane Smith"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.jsonl"
        exporter.export_to_jsonl(str(output_file))

        # Read and verify JSONL
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

            assert len(lines) == 2
            obj1 = json.loads(lines[0])
            obj2 = json.loads(lines[1])

            assert obj1["id"] == "cand_1"
            assert obj2["name"] == "Jane Smith"

    def test_export_to_jsonl_with_fields_filter(self, exporter, mock_client, tmp_path):
        """Test export_to_jsonl with specific fields"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe", "email": "john@example.com"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.jsonl"
        exporter.export_to_jsonl(str(output_file), fields=["id", "name"])

        # Read and verify fields
        with open(output_file, "r", encoding="utf-8") as f:
            obj = json.loads(f.readline())

            assert "id" in obj
            assert "name" in obj
            assert "email" not in obj  # Filtered out

    def test_export_to_jsonl_preserves_unicode(self, exporter, mock_client, tmp_path):
        """Test export_to_jsonl preserves unicode characters"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "José García"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.jsonl"
        exporter.export_to_jsonl(str(output_file))

        # Read and verify unicode
        with open(output_file, "r", encoding="utf-8") as f:
            obj = json.loads(f.readline())

            assert obj["name"] == "José García"

    def test_export_to_json_creates_file(self, exporter, mock_client, tmp_path):
        """Test export_to_json creates JSON file"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe"},
                    {"id": "cand_2", "name": "Jane Smith"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.json"

        count = exporter.export_to_json(str(output_file))

        assert count == 2
        assert output_file.exists()

    def test_export_to_json_correct_format(self, exporter, mock_client, tmp_path):
        """Test export_to_json writes correct JSON array format"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe"},
                    {"id": "cand_2", "name": "Jane Smith"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.json"
        exporter.export_to_json(str(output_file))

        # Read and verify JSON array
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["id"] == "cand_1"
            assert data[1]["name"] == "Jane Smith"

    def test_export_to_json_with_max_records(self, exporter, mock_client, tmp_path):
        """Test export_to_json respects max_records limit"""
        mock_client.candidacies.stream = Mock(
            return_value=iter([{"id": f"cand_{i}"} for i in range(100)])
        )

        output_file = tmp_path / "candidacies.json"
        count = exporter.export_to_json(str(output_file), max_records=10)

        assert count == 10

        # Verify only 10 records in file
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == 10

    def test_export_to_json_with_fields_filter(self, exporter, mock_client, tmp_path):
        """Test export_to_json with specific fields"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "name": "John Doe", "email": "john@example.com"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.json"
        exporter.export_to_json(str(output_file), fields=["id", "name"])

        # Read and verify fields
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

            assert "id" in data[0]
            assert "name" in data[0]
            assert "email" not in data[0]

    def test_export_convenience_method_csv(self, exporter, mock_client, tmp_path):
        """Test export() convenience method for CSV"""
        mock_client.candidacies.stream = Mock(return_value=iter([{"id": "cand_1"}]))

        output_file = tmp_path / "candidacies.csv"
        count = exporter.export(str(output_file), format="csv")

        assert count == 1
        assert output_file.exists()

    def test_export_convenience_method_jsonl(self, exporter, mock_client, tmp_path):
        """Test export() convenience method for JSONL"""
        mock_client.candidacies.stream = Mock(return_value=iter([{"id": "cand_1"}]))

        output_file = tmp_path / "candidacies.jsonl"
        count = exporter.export(str(output_file), format="jsonl")

        assert count == 1
        assert output_file.exists()

    def test_export_convenience_method_json(self, exporter, mock_client, tmp_path):
        """Test export() convenience method for JSON"""
        mock_client.candidacies.stream = Mock(return_value=iter([{"id": "cand_1"}]))

        output_file = tmp_path / "candidacies.json"
        count = exporter.export(str(output_file), format="json")

        assert count == 1
        assert output_file.exists()

    def test_export_unsupported_format_raises_error(self, exporter, tmp_path):
        """Test export() raises error for unsupported format"""
        output_file = tmp_path / "candidacies.xml"

        with pytest.raises(ValueError, match="Unsupported format"):
            exporter.export(str(output_file), format="xml")


class TestDataExporter:
    """Test DataExporter class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HerpClient"""
        return Mock()

    @pytest.fixture
    def exporter(self, mock_client):
        """Create DataExporter instance"""
        return DataExporter(mock_client)

    def test_initialization(self, mock_client):
        """Test exporter initialization"""
        exporter = DataExporter(mock_client)

        assert exporter.client == mock_client

    def test_export_resource_csv(self, exporter, tmp_path):
        """Test export_resource with CSV format"""
        resources = iter(
            [
                {"id": "res_1", "name": "Resource 1"},
                {"id": "res_2", "name": "Resource 2"},
            ]
        )

        output_file = tmp_path / "resources.csv"

        count = exporter.export_resource(
            resource_iter=resources, output_file=str(output_file), format="csv"
        )

        assert count == 2
        assert output_file.exists()

        # Verify CSV content
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 2
            assert rows[0]["id"] == "res_1"

    def test_export_resource_jsonl(self, exporter, tmp_path):
        """Test export_resource with JSONL format"""
        resources = iter(
            [
                {"id": "res_1", "name": "Resource 1"},
                {"id": "res_2", "name": "Resource 2"},
            ]
        )

        output_file = tmp_path / "resources.jsonl"

        count = exporter.export_resource(
            resource_iter=resources, output_file=str(output_file), format="jsonl"
        )

        assert count == 2
        assert output_file.exists()

        # Verify JSONL content
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

            assert len(lines) == 2
            assert json.loads(lines[0])["id"] == "res_1"

    def test_export_resource_json(self, exporter, tmp_path):
        """Test export_resource with JSON format"""
        resources = iter(
            [
                {"id": "res_1", "name": "Resource 1"},
                {"id": "res_2", "name": "Resource 2"},
            ]
        )

        output_file = tmp_path / "resources.json"

        count = exporter.export_resource(
            resource_iter=resources, output_file=str(output_file), format="json"
        )

        assert count == 2
        assert output_file.exists()

        # Verify JSON content
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

            assert len(data) == 2
            assert data[0]["id"] == "res_1"

    def test_export_resource_with_fields_filter(self, exporter, tmp_path):
        """Test export_resource with specific fields"""
        resources = iter(
            [
                {"id": "res_1", "name": "Resource 1", "description": "Desc 1"},
            ]
        )

        output_file = tmp_path / "resources.csv"

        exporter.export_resource(
            resource_iter=resources,
            output_file=str(output_file),
            format="csv",
            fields=["id", "name"],
        )

        # Verify only specified fields
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert "id" in rows[0]
            assert "name" in rows[0]
            assert "description" not in rows[0] or rows[0]["description"] == ""

    def test_export_resource_unsupported_format(self, exporter, tmp_path):
        """Test export_resource raises error for unsupported format"""
        resources = iter([{"id": "res_1"}])
        output_file = tmp_path / "resources.xml"

        with pytest.raises(ValueError, match="Unsupported format"):
            exporter.export_resource(
                resource_iter=resources, output_file=str(output_file), format="xml"
            )

    def test_export_resource_creates_directories(self, exporter, tmp_path):
        """Test export_resource creates parent directories"""
        resources = iter([{"id": "res_1"}])
        output_file = tmp_path / "exports" / "2026" / "resources.csv"

        exporter.export_resource(
            resource_iter=resources, output_file=str(output_file), format="csv"
        )

        assert output_file.exists()


class TestExportEdgeCases:
    """Test edge cases for export functionality"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HerpClient"""
        client = Mock()
        client.candidacies = Mock()
        return client

    @pytest.fixture
    def exporter(self, mock_client):
        """Create CandidacyExporter instance"""
        return CandidacyExporter(mock_client)

    def test_export_csv_with_unicode(self, exporter, mock_client, tmp_path):
        """Test CSV export preserves unicode characters"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"name": "José García", "city": "São Paulo"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.csv"
        exporter.export_to_csv(str(output_file))

        # Verify unicode preservation
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

            assert "José García" in content
            assert "São Paulo" in content

    def test_export_csv_with_special_characters(self, exporter, mock_client, tmp_path):
        """Test CSV export handles special characters (quotes, commas)"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"name": 'John "Johnny" Doe', "skills": "Python, JavaScript, Go"},
                ]
            )
        )

        output_file = tmp_path / "candidacies.csv"
        exporter.export_to_csv(str(output_file))

        # Verify CSV escaping
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert rows[0]["name"] == 'John "Johnny" Doe'
            assert rows[0]["skills"] == "Python, JavaScript, Go"

    def test_export_large_dataset_streaming(self, exporter, mock_client, tmp_path):
        """Test export handles large datasets via streaming"""

        # Simulate large dataset
        def generate_large_dataset():
            for i in range(10000):
                yield {"id": f"cand_{i}", "name": f"Candidate {i}"}

        mock_client.candidacies.stream = Mock(return_value=generate_large_dataset())

        output_file = tmp_path / "candidacies.jsonl"
        count = exporter.export_to_jsonl(str(output_file))

        assert count == 10000
        assert output_file.exists()

    def test_export_json_preserves_data_types(self, exporter, mock_client, tmp_path):
        """Test JSON export preserves data types (int, bool, null)"""
        mock_client.candidacies.stream = Mock(
            return_value=iter(
                [
                    {"id": "cand_1", "age": 30, "active": True, "notes": None},
                ]
            )
        )

        output_file = tmp_path / "candidacies.json"
        exporter.export_to_json(str(output_file))

        # Verify data types
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

            assert data[0]["age"] == 30  # int
            assert data[0]["active"] is True  # bool
            assert data[0]["notes"] is None  # null

    def test_data_exporter_empty_iterator(self, tmp_path):
        """Test DataExporter with empty iterator"""
        exporter = DataExporter(Mock())
        resources = iter([])

        output_file = tmp_path / "empty.csv"

        count = exporter.export_resource(
            resource_iter=resources, output_file=str(output_file), format="csv"
        )

        assert count == 0
