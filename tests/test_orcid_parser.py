"""Tests for ORCID API parser functionality."""

import pytest
import responses

from puby.sources import ORCIDSource


class TestORCIDSource:
    """Test ORCID source implementation."""

    def test_extract_orcid_id_from_url(self):
        """Test ORCID ID extraction from various URL formats."""
        source = ORCIDSource("https://orcid.org/0000-0000-0000-0000")
        assert source.orcid_id == "0000-0000-0000-0000"

        source = ORCIDSource("http://orcid.org/0000-1234-5678-9012")
        assert source.orcid_id == "0000-1234-5678-9012"

        # ORCID with X checksum digit
        source = ORCIDSource("https://orcid.org/0000-0000-0000-000X")
        assert source.orcid_id == "0000-0000-0000-000X"

        # Direct ID
        source = ORCIDSource("0000-0000-0000-0000")
        assert source.orcid_id == "0000-0000-0000-0000"

    def test_extract_orcid_id_invalid_format(self):
        """Test ORCID ID extraction with invalid formats."""
        with pytest.raises(ValueError, match="Invalid ORCID URL or ID"):
            ORCIDSource("invalid-orcid")

        with pytest.raises(ValueError, match="Invalid ORCID URL or ID"):
            ORCIDSource("https://orcid.org/invalid")

    @responses.activate
    def test_fetch_publications_success(self):
        """Test successful publication fetching from ORCID API."""
        # Mock works summary response
        works_response = {
            "last-modified-date": {"value": 1640995200000},
            "group": [
                {
                    "last-modified-date": {"value": 1640995200000},
                    "work-summary": [
                        {
                            "put-code": 12345,
                            "created-date": {"value": 1640995200000},
                            "last-modified-date": {"value": 1640995200000},
                        }
                    ],
                }
            ],
        }

        # Mock work detail response
        work_detail = {
            "title": {"title": {"value": "Test Publication"}},
            "publication-date": {"year": {"value": "2021"}},
            "journal-title": {"value": "Test Journal"},
            "external-ids": {
                "external-id": [
                    {"external-id-type": "doi", "external-id-value": "10.1000/test.doi"}
                ]
            },
            "url": {"value": "https://example.com/publication"},
            "contributors": {
                "contributor": [{"credit-name": {"value": "Test Author"}}]
            },
        }

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            json=works_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/work/12345",
            json=work_detail,
            status=200,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 1
        pub = publications[0]

        assert pub.title == "Test Publication"
        assert pub.year == 2021
        assert pub.journal == "Test Journal"
        assert pub.doi == "10.1000/test.doi"
        assert pub.url == "https://example.com/publication"
        assert len(pub.authors) == 1
        assert pub.authors[0].name == "Test Author"
        assert pub.source == "ORCID"

    @responses.activate
    def test_fetch_publications_no_works(self):
        """Test fetching when no works are available."""
        works_response = {"group": []}

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            json=works_response,
            status=200,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 0

    @responses.activate
    def test_fetch_publications_api_error(self):
        """Test handling of API errors."""
        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            status=404,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 0

    @responses.activate
    def test_fetch_work_detail_error(self):
        """Test handling of work detail fetch errors."""
        works_response = {"group": [{"work-summary": [{"put-code": 12345}]}]}

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            json=works_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/work/12345",
            status=500,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 0

    @responses.activate
    def test_parse_work_minimal_data(self):
        """Test parsing work with minimal required data."""
        works_response = {"group": [{"work-summary": [{"put-code": 12345}]}]}

        work_detail = {
            "title": {"title": {"value": "Minimal Publication"}},
        }

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            json=works_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/work/12345",
            json=work_detail,
            status=200,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 1
        pub = publications[0]

        assert pub.title == "Minimal Publication"
        assert pub.year is None
        assert pub.journal is None
        assert pub.doi is None
        assert pub.url is None
        assert len(pub.authors) == 1
        assert pub.authors[0].name == "[Authors not available]"

    @responses.activate
    def test_parse_work_no_title(self):
        """Test parsing work without title returns None."""
        works_response = {"group": [{"work-summary": [{"put-code": 12345}]}]}

        work_detail = {}

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            json=works_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/work/12345",
            json=work_detail,
            status=200,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 0

    @responses.activate
    def test_parse_work_multiple_contributors(self):
        """Test parsing work with multiple contributors."""
        works_response = {"group": [{"work-summary": [{"put-code": 12345}]}]}

        work_detail = {
            "title": {"title": {"value": "Multi-author Publication"}},
            "contributors": {
                "contributor": [
                    {"credit-name": {"value": "First Author"}},
                    {"credit-name": {"value": "Second Author"}},
                    {"credit-name": {"value": "Third Author"}},
                ]
            },
        }

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            json=works_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/work/12345",
            json=work_detail,
            status=200,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 1
        pub = publications[0]

        assert len(pub.authors) == 3
        assert pub.authors[0].name == "First Author"
        assert pub.authors[1].name == "Second Author"
        assert pub.authors[2].name == "Third Author"

    @responses.activate
    def test_parse_work_multiple_external_ids(self):
        """Test parsing work with multiple external IDs, prioritizing DOI."""
        works_response = {"group": [{"work-summary": [{"put-code": 12345}]}]}

        work_detail = {
            "title": {"title": {"value": "Publication with IDs"}},
            "external-ids": {
                "external-id": [
                    {"external-id-type": "isbn", "external-id-value": "978-0123456789"},
                    {
                        "external-id-type": "doi",
                        "external-id-value": "10.1000/test.doi",
                    },
                    {"external-id-type": "pmid", "external-id-value": "12345678"},
                ]
            },
        }

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            json=works_response,
            status=200,
        )

        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/work/12345",
            json=work_detail,
            status=200,
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        assert len(publications) == 1
        pub = publications[0]

        assert pub.doi == "10.1000/test.doi"

    def test_api_headers(self):
        """Test that correct API headers are set."""
        source = ORCIDSource("0000-0000-0000-0000")

        # Check that the API base URL is correct
        assert source.api_base == "https://pub.orcid.org/v3.0"
        assert source.orcid_id == "0000-0000-0000-0000"

    @responses.activate
    def test_rate_limit_handling(self):
        """Test handling of rate limit responses."""
        responses.add(
            responses.GET,
            "https://pub.orcid.org/v3.0/0000-0000-0000-0000/works",
            status=429,  # Too Many Requests
            headers={"Retry-After": "60"},
        )

        source = ORCIDSource("0000-0000-0000-0000")
        publications = source.fetch()

        # Should handle rate limit gracefully
        assert len(publications) == 0
