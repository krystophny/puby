"""Tests for publication reporting utilities."""

import csv
import json
from io import StringIO
from unittest.mock import patch

from puby.matcher import PotentialMatch
from puby.models import Author, Publication
from puby.reporter import (
    AnalysisReporter,
    AnalysisResult,
    ConsoleReporter,
    SyncRecommendation,
)


class TestConsoleReporter:
    """Test ConsoleReporter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ConsoleReporter("table")
        self.test_publications = [
            Publication(
                title="Test Publication 1",
                authors=[Author(name="John Doe", family_name="Doe")],
                year=2023,
                doi="10.1234/test1",
                journal="Test Journal",
                source="ORCID",
            ),
            Publication(
                title="Very Long Publication Title That Should Be Truncated",
                authors=[
                    Author(name="Jane Smith", family_name="Smith"),
                    Author(name="Bob Johnson", family_name="Johnson"),
                    Author(name="Alice Brown", family_name="Brown"),
                ],
                year=2022,
                journal="Another Journal",
                source="Zotero",
            ),
        ]

    def test_format_initialization(self):
        """Test reporter format initialization."""
        table_reporter = ConsoleReporter("table")
        assert table_reporter.format == "table"

        json_reporter = ConsoleReporter("json")
        assert json_reporter.format == "json"

    @patch("click.echo")
    def test_report_missing_empty(self, mock_echo):
        """Test reporting empty missing publications."""
        self.reporter.report_missing([])
        mock_echo.assert_called_with("\n✓ No missing publications found.")

    @patch("click.echo")
    def test_report_missing_with_publications(self, mock_echo):
        """Test reporting missing publications."""
        self.reporter.report_missing(self.test_publications)

        # Check header was printed
        calls = mock_echo.call_args_list
        assert any("Found 2 missing publication(s)" in str(call) for call in calls)

    @patch("click.echo")
    def test_report_duplicates_empty(self, mock_echo):
        """Test reporting empty duplicates."""
        self.reporter.report_duplicates([])
        mock_echo.assert_called_with("\n✓ No duplicates found in Zotero.")

    @patch("click.echo")
    def test_report_duplicates_with_groups(self, mock_echo):
        """Test reporting duplicate groups."""
        duplicate_groups = [self.test_publications]
        self.reporter.report_duplicates(duplicate_groups)

        calls = mock_echo.call_args_list
        assert any("Found 1 group(s) of duplicates" in str(call) for call in calls)

    @patch("click.echo")
    def test_report_potential_matches_empty(self, mock_echo):
        """Test reporting empty potential matches."""
        self.reporter.report_potential_matches([])
        mock_echo.assert_called_with("\n✓ No ambiguous matches found.")

    @patch("click.echo")
    def test_report_potential_matches_with_data(self, mock_echo):
        """Test reporting potential matches."""
        matches = [(self.test_publications[0], self.test_publications[1], 0.75)]
        self.reporter.report_potential_matches(matches)

        calls = mock_echo.call_args_list
        assert any("Found 1 potential match(es)" in str(call) for call in calls)
        assert any("75.00%" in str(call) for call in calls)

    def test_json_format_output(self):
        """Test JSON format output."""
        json_reporter = ConsoleReporter("json")

        with patch("click.echo") as mock_echo:
            json_reporter.report_missing([self.test_publications[0]])

            # Extract the JSON output from the call
            calls = mock_echo.call_args_list
            json_call = next(call for call in calls if "{" in str(call.args[0]))
            json_output = json_call.args[0]

            # Verify it's valid JSON
            data = json.loads(json_output)
            assert len(data) == 1
            assert data[0]["title"] == "Test Publication 1"
            assert data[0]["year"] == 2023

    def test_csv_format_output(self):
        """Test CSV format output."""
        csv_reporter = ConsoleReporter("csv")

        with patch("click.echo") as mock_echo:
            csv_reporter.report_missing([self.test_publications[0]])

            # Extract CSV output
            calls = mock_echo.call_args_list
            csv_call = next(call for call in calls if "Title" in str(call.args[0]))
            csv_output = csv_call.args[0]

            # Parse CSV
            reader = csv.DictReader(StringIO(csv_output))
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["Title"] == "Test Publication 1"

    def test_bibtex_format_output(self):
        """Test BibTeX format output."""
        bibtex_reporter = ConsoleReporter("bibtex")

        with patch("click.echo") as mock_echo:
            bibtex_reporter.report_missing([self.test_publications[0]])

            calls = mock_echo.call_args_list
            bibtex_calls = [call for call in calls if "@article" in str(call.args)]
            assert len(bibtex_calls) > 0


class TestAnalysisResult:
    """Test AnalysisResult data structure."""

    def test_analysis_result_creation(self):
        """Test creating an analysis result."""
        missing = [Publication("Test", [])]
        duplicates = [[Publication("Dup1", []), Publication("Dup2", [])]]
        potential = [
            PotentialMatch(Publication("Src", []), Publication("Ref", []), 0.7)
        ]

        result = AnalysisResult(
            missing_publications=missing,
            duplicate_groups=duplicates,
            potential_matches=potential,
            total_source_publications=10,
            total_reference_publications=8,
        )

        assert len(result.missing_publications) == 1
        assert len(result.duplicate_groups) == 1
        assert len(result.potential_matches) == 1
        assert result.total_source_publications == 10
        assert result.total_reference_publications == 8


class TestSyncRecommendation:
    """Test sync recommendation generation."""

    def test_sync_recommendation_creation(self):
        """Test creating sync recommendations."""
        rec = SyncRecommendation(
            action_type="add",
            publication=Publication("Test", []),
            reason="Missing in Zotero",
            confidence=0.9,
        )

        assert rec.action_type == "add"
        assert rec.reason == "Missing in Zotero"
        assert rec.confidence == 0.9


class TestAnalysisReporter:
    """Test AnalysisReporter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = AnalysisReporter("table", verbose=False)
        self.test_result = AnalysisResult(
            missing_publications=[Publication("Missing Pub", [Author("Test Author")])],
            duplicate_groups=[
                [
                    Publication("Dup1", [Author("Author 1")]),
                    Publication("Dup2", [Author("Author 2")]),
                ]
            ],
            potential_matches=[
                PotentialMatch(
                    Publication("Source", []), Publication("Reference", []), 0.75
                )
            ],
            total_source_publications=10,
            total_reference_publications=8,
        )

    def test_analysis_reporter_creation(self):
        """Test creating analysis reporter."""
        reporter = AnalysisReporter("json", verbose=True)
        assert reporter.format == "json"
        assert reporter.verbose is True

    @patch("click.echo")
    def test_generate_full_report(self, mock_echo):
        """Test generating a complete analysis report."""
        self.reporter.generate_full_report(self.test_result)

        calls = mock_echo.call_args_list
        call_text = " ".join(str(call) for call in calls)

        # Check that all sections are included
        assert "PUBLICATION ANALYSIS REPORT" in call_text
        assert "Missing Publications" in call_text
        assert "Duplicate Publications" in call_text
        assert "Potential Matches" in call_text
        assert "SUMMARY STATISTICS" in call_text

    @patch("click.echo")
    def test_generate_summary_statistics(self, mock_echo):
        """Test summary statistics generation."""
        self.reporter._print_summary_statistics(self.test_result)

        calls = mock_echo.call_args_list
        call_text = " ".join(str(call) for call in calls)

        assert "Source Publications: 10" in call_text
        assert "Missing Publications: 1" in call_text
        assert "Duplicate Publications: 2" in call_text

    def test_generate_sync_recommendations(self):
        """Test sync recommendation generation."""
        recommendations = self.reporter.generate_sync_recommendations(self.test_result)

        # Should have at least recommendations for missing pubs
        assert len(recommendations) >= 1

        # Check for add recommendation
        add_recs = [r for r in recommendations if r.action_type == "add"]
        assert len(add_recs) >= 1
        assert add_recs[0].reason == "Missing in reference library"

    @patch("click.echo")
    def test_print_sync_recommendations(self, mock_echo):
        """Test printing sync recommendations."""
        recommendations = [
            SyncRecommendation(
                "add", Publication("Test", []), "Missing publication", 0.9
            )
        ]

        self.reporter.print_sync_recommendations(recommendations)

        calls = mock_echo.call_args_list
        call_text = " ".join(str(call) for call in calls)

        assert "SYNC RECOMMENDATIONS" in call_text
        assert "ADD" in call_text
        assert "90% confidence" in call_text

    def test_verbose_mode_differences(self):
        """Test differences in verbose vs non-verbose output."""
        verbose_reporter = AnalysisReporter("table", verbose=True)
        regular_reporter = AnalysisReporter("table", verbose=False)

        assert verbose_reporter.verbose is True
        assert regular_reporter.verbose is False

        # Both should handle the same result without error
        with patch("click.echo"):
            verbose_reporter.generate_full_report(self.test_result)
            regular_reporter.generate_full_report(self.test_result)
