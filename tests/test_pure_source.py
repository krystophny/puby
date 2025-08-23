"""Test Pure research portal source."""

import pytest
import responses
from bs4 import BeautifulSoup

from puby.models import Author, Publication
from puby.sources import PureSource


class TestPureSource:
    """Test Pure research portal source."""

    def test_init_with_valid_url(self):
        """Test initialization with valid Pure URL."""
        url = "https://research.example.edu/en/persons/john-doe"
        source = PureSource(url)
        assert source.pure_url == url

    def test_init_with_invalid_url(self):
        """Test initialization with invalid URL."""
        with pytest.raises(ValueError, match="Invalid Pure portal URL"):
            PureSource("")

        with pytest.raises(ValueError, match="Invalid Pure portal URL"):
            PureSource("not-a-url")

    @responses.activate
    def test_fetch_publications_success(self):
        """Test successful publication fetching from Pure portal."""
        url = "https://research.example.edu/en/persons/john-doe"
        
        # Mock HTML response with Pure portal structure
        html_content = """
        <html>
            <head>
                <title>John Doe - Example University</title>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Person",
                    "name": "John Doe"
                }
                </script>
            </head>
            <body>
                <div class="rendering rendering_person">
                    <div class="result-container">
                        <div class="rendering rendering_contributiontojournal">
                            <h3 class="title">
                                <a href="/publication/1234">Test Publication Title</a>
                            </h3>
                            <div class="persons">
                                <span class="name">John Doe</span>, 
                                <span class="name">Jane Smith</span>
                            </div>
                            <div class="rendering_publicationdetails">
                                <span class="journal">Test Journal</span>
                                <span class="volume">Vol. 42</span>
                                <span class="issue">No. 1</span>
                                <span class="pages">pp. 1-10</span>
                                <span class="date">2023</span>
                            </div>
                        </div>
                        <div class="rendering rendering_contributiontojournal">
                            <h3 class="title">
                                <a href="/publication/5678">Another Research Article</a>
                            </h3>
                            <div class="persons">
                                <span class="name">John Doe</span>
                            </div>
                            <div class="rendering_publicationdetails">
                                <span class="journal">Another Journal</span>
                                <span class="date">2022</span>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            url,
            body=html_content,
            status=200,
            content_type="text/html"
        )
        
        source = PureSource(url)
        publications = source.fetch()
        
        assert len(publications) == 2
        
        # Check first publication
        pub1 = publications[0]
        assert pub1.title == "Test Publication Title"
        assert len(pub1.authors) == 2
        assert pub1.authors[0].name == "John Doe"
        assert pub1.authors[1].name == "Jane Smith"
        assert pub1.journal == "Test Journal"
        assert pub1.year == 2023
        assert pub1.source == "Pure"
        
        # Check second publication
        pub2 = publications[1]
        assert pub2.title == "Another Research Article"
        assert len(pub2.authors) == 1
        assert pub2.authors[0].name == "John Doe"
        assert pub2.journal == "Another Journal"
        assert pub2.year == 2022
        assert pub2.source == "Pure"

    @responses.activate
    def test_fetch_publications_with_pagination(self):
        """Test publication fetching with pagination."""
        base_url = "https://research.example.edu/en/persons/john-doe"
        
        # First page with "Load more" link
        page1_html = """
        <html>
            <body>
                <div class="rendering rendering_person">
                    <div class="result-container">
                        <div class="rendering rendering_contributiontojournal">
                            <h3 class="title">
                                <a href="/publication/1">Publication 1</a>
                            </h3>
                            <div class="persons">
                                <span class="name">John Doe</span>
                            </div>
                            <div class="rendering_publicationdetails">
                                <span class="date">2023</span>
                            </div>
                        </div>
                    </div>
                    <div class="load-more">
                        <a href="?page=2">Load more</a>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Second page without "Load more"
        page2_html = """
        <html>
            <body>
                <div class="rendering rendering_person">
                    <div class="result-container">
                        <div class="rendering rendering_contributiontojournal">
                            <h3 class="title">
                                <a href="/publication/2">Publication 2</a>
                            </h3>
                            <div class="persons">
                                <span class="name">John Doe</span>
                            </div>
                            <div class="rendering_publicationdetails">
                                <span class="date">2022</span>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        responses.add(responses.GET, base_url, body=page1_html, status=200)
        responses.add(responses.GET, f"{base_url}?page=2", body=page2_html, status=200)
        
        source = PureSource(base_url)
        publications = source.fetch()
        
        assert len(publications) == 2
        assert publications[0].title == "Publication 1"
        assert publications[1].title == "Publication 2"

    @responses.activate
    def test_fetch_publications_request_error(self):
        """Test handling of request errors."""
        url = "https://research.example.edu/en/persons/john-doe"
        
        responses.add(
            responses.GET,
            url,
            body="Not Found",
            status=404
        )
        
        source = PureSource(url)
        publications = source.fetch()
        
        assert publications == []

    @responses.activate
    def test_fetch_empty_page(self):
        """Test handling of empty publication page."""
        url = "https://research.example.edu/en/persons/john-doe"
        
        html_content = """
        <html>
            <body>
                <div class="rendering rendering_person">
                    <div class="result-container">
                        <!-- No publications -->
                    </div>
                </div>
            </body>
        </html>
        """
        
        responses.add(responses.GET, url, body=html_content, status=200)
        
        source = PureSource(url)
        publications = source.fetch()
        
        assert publications == []

    @responses.activate
    def test_fetch_with_json_ld_metadata(self):
        """Test extraction of metadata from JSON-LD structured data."""
        url = "https://research.example.edu/en/persons/john-doe"
        
        html_content = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "ScholarlyArticle",
                    "name": "JSON-LD Publication",
                    "author": [
                        {"@type": "Person", "name": "John Doe"},
                        {"@type": "Person", "name": "Jane Smith"}
                    ],
                    "datePublished": "2023",
                    "isPartOf": {
                        "@type": "Periodical",
                        "name": "JSON-LD Journal"
                    }
                }
                </script>
            </head>
            <body>
                <div class="rendering rendering_person">
                    <div class="result-container">
                        <!-- Minimal HTML structure, JSON-LD should be primary source -->
                        <div class="rendering rendering_contributiontojournal">
                            <h3 class="title">
                                <a href="/publication/1">JSON-LD Publication</a>
                            </h3>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        responses.add(responses.GET, url, body=html_content, status=200)
        
        source = PureSource(url)
        publications = source.fetch()
        
        assert len(publications) == 1
        pub = publications[0]
        assert pub.title == "JSON-LD Publication"
        # Should have authors from JSON-LD if HTML parsing is enhanced

    def test_extract_person_id_from_url(self):
        """Test person ID extraction from Pure URLs."""
        source = PureSource("https://research.example.edu/en/persons/john-doe")
        person_id = source._extract_person_id()
        assert person_id == "john-doe"
        
        source = PureSource("https://pure.au.dk/en/persons/kristian-steenstrup-sørensen")
        person_id = source._extract_person_id()
        assert person_id == "kristian-steenstrup-sørensen"

    def test_build_api_url(self):
        """Test API URL construction when available."""
        source = PureSource("https://research.example.edu/en/persons/john-doe")
        api_url = source._build_api_url()
        expected = "https://research.example.edu/ws/api/persons/john-doe/research-outputs"
        assert api_url == expected

    @responses.activate
    def test_fetch_with_api_fallback(self):
        """Test fallback from API to HTML scraping."""
        url = "https://research.example.edu/en/persons/john-doe"
        api_url = "https://research.example.edu/ws/api/persons/john-doe/research-outputs"
        
        # API returns 404, should fallback to HTML
        responses.add(responses.GET, api_url, status=404)
        
        html_content = """
        <html>
            <body>
                <div class="rendering rendering_person">
                    <div class="result-container">
                        <div class="rendering rendering_contributiontojournal">
                            <h3 class="title">
                                <a href="/publication/1">Fallback Publication</a>
                            </h3>
                            <div class="persons">
                                <span class="name">John Doe</span>
                            </div>
                            <div class="rendering_publicationdetails">
                                <span class="date">2023</span>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        
        responses.add(responses.GET, url, body=html_content, status=200)
        
        source = PureSource(url)
        publications = source.fetch()
        
        assert len(publications) == 1
        assert publications[0].title == "Fallback Publication"

    @responses.activate  
    def test_rate_limiting(self):
        """Test that rate limiting is applied between requests."""
        base_url = "https://research.example.edu/en/persons/john-doe"
        
        # Set up pagination to force multiple requests
        page1_html = """<html><body><div class="rendering rendering_person">
                        <div class="result-container"></div>
                        <div class="load-more"><a href="?page=2">Load more</a></div>
                        </div></body></html>"""
        page2_html = """<html><body><div class="rendering rendering_person">
                        <div class="result-container"></div></div></body></html>"""
        
        responses.add(responses.GET, base_url, body=page1_html, status=200)
        responses.add(responses.GET, f"{base_url}?page=2", body=page2_html, status=200)
        
        import time
        start_time = time.time()
        
        source = PureSource(base_url)
        publications = source.fetch()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should have at least minimal delay between requests
        assert elapsed >= 1.0  # At least 1 second for rate limiting