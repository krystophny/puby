"""Tests for Google Scholar source implementation."""

from unittest.mock import patch

import pytest
import responses

from puby.sources import ScholarSource


class TestScholarSource:
    """Test Google Scholar source implementation."""

    def test_extract_scholar_id_from_url(self):
        """Test Scholar ID extraction from various URL formats."""
        # Standard profile URL
        source = ScholarSource("https://scholar.google.com/citations?user=ABC123&hl=en")
        assert source.user_id == "ABC123"

        # Profile URL with different parameters
        source = ScholarSource("https://scholar.google.com/citations?hl=en&user=XYZ789")
        assert source.user_id == "XYZ789"

        # Minimal profile URL
        source = ScholarSource("https://scholar.google.com/citations?user=TEST456")
        assert source.user_id == "TEST456"

        # Direct user ID
        source = ScholarSource("DEF789")
        assert source.user_id == "DEF789"

    def test_extract_scholar_id_invalid_format(self):
        """Test Scholar ID extraction with invalid formats."""
        with pytest.raises(ValueError, match="Invalid Google Scholar URL or ID"):
            ScholarSource("https://google.com/invalid")

        with pytest.raises(ValueError, match="Invalid Google Scholar URL or ID"):
            ScholarSource("invalid-scholar-url")

        with pytest.raises(ValueError, match="Invalid Google Scholar URL or ID"):
            ScholarSource("")

    @responses.activate
    def test_fetch_publications_success(self):
        """Test successful publication fetching from Google Scholar."""
        mock_html = """
        <html>
        <body>
            <div id="gs_ccl">
                <tr class="gsc_a_tr">
                    <td class="gsc_a_t">
                        <a class="gsc_a_at" href="/citations?view_op=view_citation&hl=en&user=ABC123&citation_for_view=ABC123:u5HHmVD_uO8C">
                            Machine Learning Applications in Physics
                        </a>
                        <div class="gs_gray">
                            J Smith, A Johnson, B Williams
                        </div>
                        <div class="gs_gray">
                            Nature Physics 15 (4), 123-130, 2021
                        </div>
                    </td>
                    <td class="gsc_a_c">
                        <a href="/citations?view_op=view_citation&hl=en&user=ABC123&citation_for_view=ABC123:u5HHmVD_uO8C">45</a>
                    </td>
                    <td class="gsc_a_y">
                        <span class="gsc_a_h">2021</span>
                    </td>
                </tr>
                <tr class="gsc_a_tr">
                    <td class="gsc_a_t">
                        <a class="gsc_a_at" href="/citations?view_op=view_citation&hl=en&user=ABC123&citation_for_view=ABC123:d1gkVwhDpl0C">
                            Deep Learning for Scientific Computing
                        </a>
                        <div class="gs_gray">
                            B Williams, J Smith
                        </div>
                        <div class="gs_gray">
                            Journal of Computational Physics 400, 109001, 2020
                        </div>
                    </td>
                    <td class="gsc_a_c">
                        <a href="/citations?view_op=view_citation&hl=en&user=ABC123&citation_for_view=ABC123:d1gkVwhDpl0C">23</a>
                    </td>
                    <td class="gsc_a_y">
                        <span class="gsc_a_h">2020</span>
                    </td>
                </tr>
            </div>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=0&pagesize=100",
            body=mock_html,
            status=200,
        )

        source = ScholarSource("ABC123")
        publications = source.fetch()

        assert len(publications) == 2

        # Check first publication
        pub1 = publications[0]
        assert pub1.title == "Machine Learning Applications in Physics"
        assert pub1.year == 2021
        assert pub1.journal == "Nature Physics"
        assert len(pub1.authors) == 3
        assert pub1.authors[0].name == "J Smith"
        assert pub1.authors[1].name == "A Johnson"
        assert pub1.authors[2].name == "B Williams"
        assert pub1.source == "Google Scholar"

        # Check second publication
        pub2 = publications[1]
        assert pub2.title == "Deep Learning for Scientific Computing"
        assert pub2.year == 2020
        assert pub2.journal == "Journal of Computational Physics"
        assert len(pub2.authors) == 2
        assert pub2.authors[0].name == "B Williams"
        assert pub2.authors[1].name == "J Smith"

    @responses.activate
    def test_fetch_publications_with_pagination(self):
        """Test fetching publications across multiple pages."""
        # First page with more results indicator
        page1_html = """
        <html>
        <body>
            <div id="gs_ccl">
                <tr class="gsc_a_tr">
                    <td class="gsc_a_t">
                        <a class="gsc_a_at">Publication 1</a>
                        <div class="gs_gray">Author One</div>
                        <div class="gs_gray">Journal One, 2021</div>
                    </td>
                    <td class="gsc_a_c"><a>10</a></td>
                    <td class="gsc_a_y"><span class="gsc_a_h">2021</span></td>
                </tr>
            </div>
            <button id="gsc_bpf_next" onclick="window.location='?user=ABC123&cstart=100'">Show more</button>
        </body>
        </html>
        """

        # Second page without more results indicator
        page2_html = """
        <html>
        <body>
            <div id="gs_ccl">
                <tr class="gsc_a_tr">
                    <td class="gsc_a_t">
                        <a class="gsc_a_at">Publication 2</a>
                        <div class="gs_gray">Author Two</div>
                        <div class="gs_gray">Journal Two, 2020</div>
                    </td>
                    <td class="gsc_a_c"><a>5</a></td>
                    <td class="gsc_a_y"><span class="gsc_a_h">2020</span></td>
                </tr>
            </div>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=0&pagesize=100",
            body=page1_html,
            status=200,
        )

        responses.add(
            responses.GET,
            "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=100&pagesize=100",
            body=page2_html,
            status=200,
        )

        # Mock time.sleep to speed up tests
        with patch("time.sleep"):
            source = ScholarSource("ABC123")
            publications = source.fetch()

        assert len(publications) == 2
        assert publications[0].title == "Publication 1"
        assert publications[1].title == "Publication 2"

    @responses.activate
    def test_fetch_publications_empty_profile(self):
        """Test fetching from profile with no publications."""
        empty_html = """
        <html>
        <body>
            <div id="gs_ccl">
                <!-- No publications -->
            </div>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=0&pagesize=100",
            body=empty_html,
            status=200,
        )

        source = ScholarSource("ABC123")
        publications = source.fetch()

        assert len(publications) == 0

    @responses.activate
    def test_fetch_publications_network_error(self):
        """Test handling of network errors."""
        responses.add(
            responses.GET,
            "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=0&pagesize=100",
            status=500,
        )

        source = ScholarSource("ABC123")
        publications = source.fetch()

        assert len(publications) == 0

    @responses.activate
    def test_fetch_publications_blocked_request(self):
        """Test handling of blocked requests (429 Too Many Requests)."""
        responses.add(
            responses.GET,
            "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=0&pagesize=100",
            status=429,
            headers={"Retry-After": "300"},
        )

        source = ScholarSource("ABC123")
        publications = source.fetch()

        assert len(publications) == 0

    def test_parse_publication_minimal_data(self):
        """Test parsing publication with minimal data."""
        source = ScholarSource("ABC123")

        # Create a minimal publication row (just title)
        minimal_html = """
        <tr class="gsc_a_tr">
            <td class="gsc_a_t">
                <a class="gsc_a_at">Test Publication</a>
            </td>
            <td class="gsc_a_c"></td>
            <td class="gsc_a_y"></td>
        </tr>
        """

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(minimal_html, "html.parser")
        row = soup.find("tr", class_="gsc_a_tr")

        publication = source._parse_publication_row(row)

        assert publication is not None
        assert publication.title == "Test Publication"
        assert publication.year is None
        assert publication.journal is None
        assert len(publication.authors) == 1
        assert publication.authors[0].name == "[Authors not available]"

    def test_parse_publication_no_title(self):
        """Test parsing publication without title returns None."""
        source = ScholarSource("ABC123")

        # Create a publication row without title
        no_title_html = """
        <tr class="gsc_a_tr">
            <td class="gsc_a_t">
                <div class="gs_gray">Some Author</div>
            </td>
            <td class="gsc_a_c"></td>
            <td class="gsc_a_y"></td>
        </tr>
        """

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(no_title_html, "html.parser")
        row = soup.find("tr", class_="gsc_a_tr")

        publication = source._parse_publication_row(row)

        assert publication is None

    def test_parse_authors_from_gray_text(self):
        """Test parsing authors from gray text."""
        source = ScholarSource("ABC123")

        # Test various author formats
        test_cases = [
            ("J Smith, A Johnson, B Williams", ["J Smith", "A Johnson", "B Williams"]),
            ("Single Author", ["Single Author"]),
            ("A, B, C, D, E", ["A", "B", "C", "D", "E"]),
            ("", ["[Authors not available]"]),
        ]

        for author_text, expected in test_cases:
            authors = source._parse_authors(author_text)
            assert len(authors) == len(expected)
            for i, expected_name in enumerate(expected):
                assert authors[i].name == expected_name

    def test_parse_journal_and_year_from_gray_text(self):
        """Test parsing journal and year from publication info."""
        source = ScholarSource("ABC123")

        # Test various publication info formats
        test_cases = [
            ("Nature Physics 15 (4), 123-130, 2021", ("Nature Physics", 2021)),
            ("Journal of Science, 2020", ("Journal of Science", 2020)),
            ("Proceedings of Conference 2019", ("Proceedings of Conference", 2019)),
            ("arXiv preprint arXiv:2021.12345", ("arXiv preprint", 2021)),
            ("Book Title, 2022", ("Book Title", 2022)),
            ("Just a title with no year", ("Just a title with no year", None)),
            ("", (None, None)),
        ]

        for pub_info, (expected_journal, expected_year) in test_cases:
            journal, year = source._parse_journal_and_year(pub_info)
            assert journal == expected_journal
            assert year == expected_year

    @patch("time.sleep")
    def test_rate_limiting_delay(self, mock_sleep):
        """Test that rate limiting delays are implemented."""
        source = ScholarSource("ABC123")

        # Call the rate limiting method
        source._apply_rate_limit()

        # Verify sleep was called with appropriate delay
        mock_sleep.assert_called_once()
        call_args = mock_sleep.call_args[0][0]
        assert 1.0 <= call_args <= 3.0  # Should be between 1-3 seconds

    def test_build_url_with_pagination(self):
        """Test URL building with pagination parameters."""
        source = ScholarSource("ABC123")

        # Test first page
        url = source._build_url(0)
        expected = "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=0&pagesize=100"
        assert url == expected

        # Test subsequent page
        url = source._build_url(100)
        expected = "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=100&pagesize=100"
        assert url == expected

    def test_user_agent_header(self):
        """Test that proper User-Agent header is set."""
        source = ScholarSource("ABC123")

        headers = source._get_headers()
        assert "User-Agent" in headers
        assert "Mozilla" in headers["User-Agent"]  # Should look like a real browser

    @responses.activate
    def test_parse_publication_with_complex_journal_info(self):
        """Test parsing publication with complex journal information."""
        complex_html = """
        <html>
        <body>
            <div id="gs_ccl">
                <tr class="gsc_a_tr">
                    <td class="gsc_a_t">
                        <a class="gsc_a_at">Complex Publication Title</a>
                        <div class="gs_gray">First Author, Second Author, Third Author</div>
                        <div class="gs_gray">Nature Communications 12 (1), 1-15, 2021</div>
                    </td>
                    <td class="gsc_a_c"><a>100</a></td>
                    <td class="gsc_a_y"><span class="gsc_a_h">2021</span></td>
                </tr>
            </div>
        </body>
        </html>
        """

        responses.add(
            responses.GET,
            "https://scholar.google.com/citations?user=ABC123&hl=en&cstart=0&pagesize=100",
            body=complex_html,
            status=200,
        )

        source = ScholarSource("ABC123")
        publications = source.fetch()

        assert len(publications) == 1
        pub = publications[0]
        assert pub.title == "Complex Publication Title"
        assert pub.journal == "Nature Communications"
        assert pub.year == 2021
        assert len(pub.authors) == 3
        assert pub.authors[0].name == "First Author"
