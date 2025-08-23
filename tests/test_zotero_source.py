"""Tests for Zotero API client."""

from unittest.mock import Mock, patch

import pytest
import requests

from puby.models import ZoteroConfig
from puby.sources import ZoteroSource


class TestZoteroSource:
    """Test ZoteroSource implementation."""

    @patch("puby.sources.zotero.Zotero")
    def test_zotero_source_creation_with_config(self, mock_zotero):
        """Test creating ZoteroSource with configuration."""
        # Mock successful connection
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        assert source.config == config

    def test_zotero_source_creation_invalid_config(self):
        """Test creating ZoteroSource with invalid configuration."""
        config = ZoteroConfig(api_key="", library_type="group")
        with pytest.raises(ValueError, match="Invalid Zotero configuration"):
            ZoteroSource(config)

    @patch("puby.sources.zotero.Zotero")
    def test_zotero_client_initialization_group(self, mock_zotero):
        """Test Zotero client initialization for group library."""
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef34", group_id="12345", library_type="group"
        )
        ZoteroSource(config)

        mock_zotero.assert_called_once_with(
            "12345", "group", "abcdef1234567890abcdef34"
        )

    @patch("puby.sources.zotero.Zotero")
    def test_zotero_client_initialization_user(self, mock_zotero):
        """Test Zotero client initialization for user library."""
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef34", group_id="67890", library_type="user"
        )
        ZoteroSource(config)

        mock_zotero.assert_called_once_with("67890", "user", "abcdef1234567890abcdef34")

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_zotero_user_id_autodiscovery_success(self, mock_zotero, mock_get):
        """Test successful user ID auto-discovery from API key."""
        # Mock the /keys/current endpoint response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "key": "abcdef1234567890abcdef12",
            "userID": 123456,
            "username": "testuser",
            "access": {"user": {"library": True, "notes": True, "write": True}},
        }
        mock_get.return_value = mock_response

        # Create config without user ID
        config = ZoteroConfig(api_key="abcdef1234567890abcdef12", library_type="user")
        ZoteroSource(config)

        # Verify the auto-discovery was performed
        mock_get.assert_called_once_with(
            "https://api.zotero.org/keys/current",
            headers={
                "Zotero-API-Key": "abcdef1234567890abcdef12",
                "Accept": "application/json",
            },
        )

        # Verify Zotero client was initialized with discovered user ID
        mock_zotero.assert_called_once_with(
            "123456", "user", "abcdef1234567890abcdef12"
        )

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_zotero_user_id_autodiscovery_api_error(self, mock_zotero, mock_get):
        """Test user ID auto-discovery with API error."""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        # Create HTTPError with response attribute
        http_error = requests.HTTPError("403 Forbidden")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_get.return_value = mock_response

        # Create config without user ID
        config = ZoteroConfig(api_key="invalidkey567890123456ab", library_type="user")

        # Should raise error with helpful message
        with pytest.raises(
            ValueError, match="Failed to auto-discover user ID.*Invalid API key"
        ):
            ZoteroSource(config)

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_zotero_user_id_explicit_overrides_autodiscovery(
        self, mock_zotero, mock_get
    ):
        """Test that explicit user ID is used without auto-discovery."""
        # Create config with explicit user ID
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12",
            group_id="999999",  # Explicit user ID
            library_type="user",
        )
        ZoteroSource(config)

        # Verify no auto-discovery was performed
        mock_get.assert_not_called()

        # Verify Zotero client was initialized with explicit user ID
        mock_zotero.assert_called_once_with(
            "999999", "user", "abcdef1234567890abcdef12"
        )

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_zotero_group_library_no_autodiscovery(self, mock_zotero, mock_get):
        """Test that group libraries don't use auto-discovery."""
        # Create config for group library
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12", group_id="12345", library_type="group"
        )
        ZoteroSource(config)

        # Verify no auto-discovery was performed
        mock_get.assert_not_called()

        # Verify Zotero client was initialized with group ID
        mock_zotero.assert_called_once_with(
            "12345", "group", "abcdef1234567890abcdef12"
        )

    @patch("puby.sources.requests.get")
    def test_zotero_user_id_autodiscovery_network_error(self, mock_get):
        """Test user ID auto-discovery with network error."""
        # Mock network error
        mock_get.side_effect = requests.ConnectionError("Network error")

        # Create config without user ID
        config = ZoteroConfig(api_key="abcdef1234567890abcdef12", library_type="user")

        # Should raise error with helpful message
        with pytest.raises(ValueError, match="Failed to auto-discover user ID"):
            ZoteroSource(config)

    @patch("puby.sources.requests.get")
    def test_zotero_user_id_autodiscovery_invalid_response(self, mock_get):
        """Test user ID auto-discovery with invalid response format."""
        # Mock response without userID field
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "key": "abcdef1234567890abcdef12",
            # Missing userID field
            "username": "testuser",
        }
        mock_get.return_value = mock_response

        # Create config without user ID
        config = ZoteroConfig(api_key="abcdef1234567890abcdef12", library_type="user")

        # Should raise error with helpful message
        with pytest.raises(ValueError, match="Invalid response from Zotero API"):
            ZoteroSource(config)

    @patch("puby.sources.zotero.Zotero")
    def test_fetch_publications_success(self, mock_zotero):
        """Test successful publication fetch."""
        # Mock Zotero API response
        mock_items = [
            {
                "data": {
                    "itemType": "journalArticle",
                    "title": "Test Publication 1",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "John",
                            "lastName": "Doe",
                        }
                    ],
                    "date": "2023",
                    "publicationTitle": "Test Journal",
                    "DOI": "10.1234/test1",
                }
            },
            {
                "data": {
                    "itemType": "journalArticle",
                    "title": "Test Publication 2",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "Jane",
                            "lastName": "Smith",
                        }
                    ],
                    "date": "2023-05-15",
                    "publicationTitle": "Another Journal",
                    "DOI": "10.5678/test2",
                }
            },
        ]

        # Configure mock
        mock_client = Mock()
        mock_client.everything.return_value = mock_items
        mock_client.top.return_value = []
        mock_zotero.return_value = mock_client

        # Create source and fetch
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        publications = source.fetch()

        # Verify results
        assert len(publications) == 2

        pub1 = publications[0]
        assert pub1.title == "Test Publication 1"
        assert len(pub1.authors) == 1
        assert pub1.authors[0].name == "John Doe"
        assert pub1.authors[0].given_name == "John"
        assert pub1.authors[0].family_name == "Doe"
        assert pub1.year == 2023
        assert pub1.journal == "Test Journal"
        assert pub1.doi == "10.1234/test1"
        assert pub1.source == "Zotero"

        pub2 = publications[1]
        assert pub2.title == "Test Publication 2"
        assert len(pub2.authors) == 1
        assert pub2.authors[0].name == "Jane Smith"
        assert pub2.year == 2023
        assert pub2.journal == "Another Journal"
        assert pub2.doi == "10.5678/test2"

    @patch("puby.sources.zotero.Zotero")
    def test_fetch_publications_with_pagination(self, mock_zotero):
        """Test fetch with paginated results."""
        # Mock paginated response
        mock_items_page1 = [
            {
                "data": {
                    "itemType": "journalArticle",
                    "title": "Publication 1",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "John",
                            "lastName": "Doe",
                        }
                    ],
                    "date": "2023",
                }
            }
        ]

        mock_items_page2 = [
            {
                "data": {
                    "itemType": "journalArticle",
                    "title": "Publication 2",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "Jane",
                            "lastName": "Smith",
                        }
                    ],
                    "date": "2023",
                }
            }
        ]

        # Configure mock to return paginated results
        mock_client = Mock()
        all_items = mock_items_page1 + mock_items_page2
        mock_client.everything.return_value = all_items
        mock_client.top.return_value = []
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        publications = source.fetch()

        assert len(publications) == 2
        assert mock_client.everything.called

    @patch("puby.sources.zotero.Zotero")
    def test_fetch_publications_error_handling(self, mock_zotero):
        """Test error handling during fetch."""
        # Mock Zotero client that raises exception
        mock_client = Mock()
        mock_client.everything.side_effect = Exception("API Error")
        mock_client.top.return_value = []
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)

        # Should raise ValueError on error instead of silently returning empty list
        with pytest.raises(ValueError, match="Failed to fetch Zotero data"):
            source.fetch()

    @patch("puby.sources.zotero.Zotero")
    def test_parse_zotero_item_book(self, mock_zotero):
        """Test parsing book item type."""
        mock_client = Mock()
        mock_zotero.return_value = mock_client

        book_item = {
            "data": {
                "itemType": "book",
                "title": "Test Book",
                "creators": [
                    {"creatorType": "author", "firstName": "Author", "lastName": "Name"}
                ],
                "date": "2023",
                "publisher": "Test Publisher",
                "ISBN": "978-0-123456-78-9",
            }
        }

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        pub = source._parse_zotero_item(book_item)

        assert pub is not None
        assert pub.title == "Test Book"
        assert pub.publication_type == "book"
        assert pub.source == "Zotero"

    @patch("puby.sources.zotero.Zotero")
    def test_parse_zotero_item_skip_non_publication(self, mock_zotero):
        """Test skipping non-publication item types."""
        mock_client = Mock()
        mock_zotero.return_value = mock_client

        note_item = {
            "data": {"itemType": "note", "note": "This is a note, not a publication"}
        }

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        pub = source._parse_zotero_item(note_item)

        assert pub is None

    @patch("puby.sources.zotero.Zotero")
    def test_parse_zotero_item_no_title(self, mock_zotero):
        """Test parsing item with missing title."""
        mock_client = Mock()
        mock_zotero.return_value = mock_client

        item = {
            "data": {
                "itemType": "journalArticle",
                "title": "",  # Empty title
                "creators": [
                    {"creatorType": "author", "firstName": "John", "lastName": "Doe"}
                ],
            }
        }

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        pub = source._parse_zotero_item(item)

        assert pub is None

    @patch("puby.sources.zotero.Zotero")
    def test_parse_zotero_item_no_authors(self, mock_zotero):
        """Test parsing item with no authors."""
        mock_client = Mock()
        mock_zotero.return_value = mock_client

        item = {
            "data": {
                "itemType": "journalArticle",
                "title": "Publication Without Authors",
                "creators": [],  # No creators
                "date": "2023",
            }
        }

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        pub = source._parse_zotero_item(item)

        assert pub is not None
        assert pub.title == "Publication Without Authors"
        assert len(pub.authors) == 1
        assert pub.authors[0].name == "[No authors]"

    @patch("puby.sources.zotero.Zotero")
    def test_parse_zotero_item_complex_date(self, mock_zotero):
        """Test parsing various date formats."""
        mock_client = Mock()
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)

        # Test different date formats
        date_formats = [
            ("2023", 2023),
            ("2023-05-15", 2023),
            ("May 2023", 2023),
            ("2023-12", 2023),
            ("Published 2023", 2023),
            ("", None),
            ("No year here", None),
        ]

        for date_str, expected_year in date_formats:
            item = {
                "data": {
                    "itemType": "journalArticle",
                    "title": f"Test Publication {date_str}",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "Test",
                            "lastName": "Author",
                        }
                    ],
                    "date": date_str,
                }
            }

            pub = source._parse_zotero_item(item)
            assert pub is not None
            assert pub.year == expected_year, f"Failed for date: '{date_str}'"

    @patch("puby.sources.zotero.Zotero")
    def test_validate_connection_success(self, mock_zotero):
        """Test successful connection validation."""
        # Mock successful connection test
        mock_client = Mock()
        mock_client.collections.return_value = []  # Empty list means success
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)

        # Should not raise any exception
        source.validate_connection()

        # Verify collections was called to test connection
        # (once during init, once during explicit call)
        assert mock_client.collections.call_count == 2

    @patch("puby.sources.zotero.Zotero")
    def test_validate_connection_invalid_api_key(self, mock_zotero):
        """Test connection validation with invalid API key."""
        # Mock authentication failure only on second call
        mock_client = Mock()
        mock_client.collections.side_effect = [
            [],  # First call during init succeeds
            Exception("403 Forbidden"),  # Second explicit call fails
        ]
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="invalidkey567890123456ab", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)

        # Should raise clear error about authentication
        with pytest.raises(ValueError, match="Zotero authentication failed"):
            source.validate_connection()

    @patch("puby.sources.zotero.Zotero")
    def test_validate_connection_network_error(self, mock_zotero):
        """Test connection validation with network error."""
        # Mock network failure only on second call
        mock_client = Mock()
        mock_client.collections.side_effect = [
            [],  # First call during init succeeds
            requests.ConnectionError("Network error"),  # Second explicit call fails
        ]
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)

        # Should raise clear error about network
        with pytest.raises(ValueError, match="Zotero connection failed.*Network"):
            source.validate_connection()

    @patch("puby.sources.zotero.Zotero")
    def test_validate_connection_invalid_library(self, mock_zotero):
        """Test connection validation with invalid library ID."""
        # Mock library not found error only on second call
        mock_client = Mock()
        mock_client.collections.side_effect = [
            [],  # First call during init succeeds
            Exception("404 Not Found"),  # Second explicit call fails
        ]
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="99999", library_type="group"
        )
        source = ZoteroSource(config)

        # Should raise clear error about library not found
        with pytest.raises(ValueError, match="Zotero library.*not found"):
            source.validate_connection()

    @patch("puby.sources.zotero.Zotero")
    def test_validate_connection_on_init(self, mock_zotero):
        """Test that connection is validated on initialization."""
        # Mock successful connection
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )

        # Create source - should validate connection
        ZoteroSource(config)

        # Verify connection was validated during init
        mock_client.collections.assert_called_once()

    @patch("puby.sources.zotero.Zotero")
    def test_init_with_connection_failure(self, mock_zotero):
        """Test initialization with connection failure."""
        # Mock connection failure during init
        mock_client = Mock()
        mock_client.collections.side_effect = Exception("403 Forbidden")
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="invalidkey567890123456ab", group_id="12345", library_type="group"
        )

        # Should raise error during initialization due to authentication failure
        with pytest.raises(
            ValueError, match="Failed to initialize Zotero client.*auth"
        ):
            ZoteroSource(config)

    @patch("puby.sources.zotero.Zotero")
    def test_fetch_with_connection_error_vs_missing(self, mock_zotero):
        """Test distinguishing between connection errors and missing publications."""
        # First test - connection error during fetch
        mock_client = Mock()
        mock_client.collections.return_value = []  # Connection OK for init
        mock_client.everything.side_effect = requests.ConnectionError("Network error")
        mock_client.top.return_value = []
        mock_zotero.return_value = mock_client

        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef56", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)

        # Should raise connection error, not return empty list
        with pytest.raises(ValueError, match="connection failed"):
            source.fetch()

        # Second test - truly empty library
        mock_client2 = Mock()
        mock_client2.collections.return_value = []  # Connection OK for init
        mock_client2.everything.return_value = []  # No items
        mock_client2.top.return_value = []
        mock_zotero.return_value = mock_client2

        source2 = ZoteroSource(config)
        publications = source2.fetch()

        # Should return empty list without error
        assert publications == []

    @patch("puby.sources.zotero.Zotero")
    def test_integration_zotero_api_flow(self, mock_zotero):
        """Test complete Zotero API integration flow."""
        # Mock complete API response with realistic data
        mock_items = [
            {
                "key": "ABC123",
                "version": 123,
                "data": {
                    "key": "ABC123",
                    "itemType": "journalArticle",
                    "title": "A comprehensive study of machine learning applications",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "Alice",
                            "lastName": "Johnson",
                        },
                        {
                            "creatorType": "author",
                            "firstName": "Bob",
                            "lastName": "Smith",
                        },
                        {
                            "creatorType": "editor",  # Should be skipped
                            "firstName": "Carol",
                            "lastName": "Editor",
                        },
                    ],
                    "date": "2023-08-15",
                    "publicationTitle": "Journal of Machine Learning Research",
                    "volume": "24",
                    "issue": "8",
                    "pages": "123-145",
                    "DOI": "10.1234/jmlr.2023.123",
                    "url": "https://doi.org/10.1234/jmlr.2023.123",
                    "abstractNote": "This paper presents a comprehensive analysis...",
                    "tags": [
                        {"tag": "machine learning", "type": 1},
                        {"tag": "data science", "type": 1},
                    ],
                    "collections": ["COLLECTION123"],
                    "relations": {},
                },
            },
            {
                "key": "DEF456",
                "version": 456,
                "data": {
                    "key": "DEF456",
                    "itemType": "book",
                    "title": "Advanced Data Structures",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "Charlie",
                            "lastName": "Brown",
                        }
                    ],
                    "date": "2022",
                    "publisher": "Academic Press",
                    "place": "New York",
                    "ISBN": "978-0-123456-78-9",
                    "numPages": "450",
                },
            },
        ]

        # Configure mock
        mock_client = Mock()
        mock_client.everything.return_value = mock_items
        mock_client.top.return_value = []
        mock_zotero.return_value = mock_client

        # Test with group library
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef90", group_id="987654", library_type="group"
        )
        source = ZoteroSource(config)
        publications = source.fetch()

        # Verify client initialization
        mock_zotero.assert_called_once_with(
            "987654", "group", "abcdef1234567890abcdef90"
        )

        # Verify API calls
        mock_client.everything.assert_called_once()
        mock_client.top.assert_called_once()

        # Verify parsed publications
        assert len(publications) == 2

        # Check journal article
        journal_pub = publications[0]
        assert (
            journal_pub.title
            == "A comprehensive study of machine learning applications"
        )
        assert len(journal_pub.authors) == 2  # Editor should be excluded
        assert journal_pub.authors[0].name == "Alice Johnson"
        assert journal_pub.authors[0].given_name == "Alice"
        assert journal_pub.authors[0].family_name == "Johnson"
        assert journal_pub.authors[1].name == "Bob Smith"
        assert journal_pub.year == 2023
        assert journal_pub.journal == "Journal of Machine Learning Research"
        assert journal_pub.volume == "24"
        assert journal_pub.issue == "8"
        assert journal_pub.pages == "123-145"
        assert journal_pub.doi == "10.1234/jmlr.2023.123"
        assert journal_pub.url == "https://doi.org/10.1234/jmlr.2023.123"
        assert journal_pub.abstract == "This paper presents a comprehensive analysis..."
        assert journal_pub.publication_type == "journalArticle"
        assert journal_pub.source == "Zotero"
        assert journal_pub.raw_data["key"] == "ABC123"

        # Check book
        book_pub = publications[1]
        assert book_pub.title == "Advanced Data Structures"
        assert len(book_pub.authors) == 1
        assert book_pub.authors[0].name == "Charlie Brown"
        assert book_pub.year == 2022
        assert book_pub.journal is None  # Books don't have journals
        assert book_pub.publication_type == "book"
        assert book_pub.source == "Zotero"


class TestZoteroMyPublicationsEndpoint:
    """Test Zotero My Publications endpoint support."""

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_fetch_my_publications_success(self, mock_zotero, mock_requests_get):
        """Test successful fetch from My Publications endpoint."""
        # Mock Zotero client - needed for initialization but won't be used for My Publications
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_zotero.return_value = mock_client

        # Mock API response for My Publications endpoint
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "data": {
                    "itemType": "journalArticle",
                    "title": "My Research Paper",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "John",
                            "lastName": "Author",
                        }
                    ],
                    "date": "2023",
                    "publicationTitle": "Research Journal",
                    "DOI": "10.1234/research.2023.123",
                }
            }
        ]
        mock_requests_get.return_value = mock_response

        # Create source with My Publications enabled
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12",
            group_id="123456",
            library_type="user",
            use_my_publications=True,
        )
        source = ZoteroSource(config)

        publications = source.fetch()

        # Verify API endpoint was called correctly
        mock_requests_get.assert_called_once_with(
            "https://api.zotero.org/users/123456/publications/items",
            headers={
                "Zotero-API-Key": "abcdef1234567890abcdef12",
                "Accept": "application/json",
            },
            params={"format": "json", "limit": 100, "start": 0},
        )

        # Verify publication was parsed correctly
        assert len(publications) == 1
        pub = publications[0]
        assert pub.title == "My Research Paper"
        assert len(pub.authors) == 1
        assert pub.authors[0].name == "John Author"
        assert pub.year == 2023
        assert pub.journal == "Research Journal"
        assert pub.doi == "10.1234/research.2023.123"
        assert pub.source == "Zotero My Publications"

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_fetch_my_publications_with_pagination(
        self, mock_zotero, mock_requests_get
    ):
        """Test My Publications endpoint with pagination."""
        # Mock Zotero client
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_zotero.return_value = mock_client

        # Mock paginated API responses
        # First page returns 100 items (full page), second page returns empty
        first_page_items = []
        for i in range(100):  # Full page of 100 items
            first_page_items.append(
                {
                    "data": {
                        "itemType": "journalArticle",
                        "title": f"Publication {i+1}",
                        "creators": [
                            {
                                "creatorType": "author",
                                "firstName": "A",
                                "lastName": f"Author{i+1}",
                            }
                        ],
                        "date": "2023",
                    }
                }
            )

        responses = [
            # First page - full page to trigger pagination
            Mock(status_code=200, json=lambda: first_page_items),
            # Second page (empty)
            Mock(status_code=200, json=lambda: []),
        ]
        mock_requests_get.side_effect = responses

        # Create source with My Publications enabled
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12",
            group_id="123456",
            library_type="user",
            use_my_publications=True,
        )
        source = ZoteroSource(config)

        publications = source.fetch()

        # Verify both API calls were made
        assert mock_requests_get.call_count == 2

        # First call
        first_call = mock_requests_get.call_args_list[0]
        assert (
            first_call[0][0] == "https://api.zotero.org/users/123456/publications/items"
        )
        assert first_call[1]["params"]["start"] == 0

        # Second call (next page)
        second_call = mock_requests_get.call_args_list[1]
        assert (
            second_call[0][0]
            == "https://api.zotero.org/users/123456/publications/items"
        )
        assert second_call[1]["params"]["start"] == 100

        # Verify publications were parsed
        assert len(publications) == 100
        assert publications[0].title == "Publication 1"
        assert publications[99].title == "Publication 100"

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_fetch_my_publications_endpoint_not_available(
        self, mock_zotero, mock_requests_get
    ):
        """Test fallback to regular library when My Publications endpoint not available."""
        # Mock Zotero client
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_client.everything.return_value = [
            {
                "data": {
                    "itemType": "journalArticle",
                    "title": "Library Publication",
                    "creators": [
                        {
                            "creatorType": "author",
                            "firstName": "Library",
                            "lastName": "Author",
                        }
                    ],
                    "date": "2023",
                }
            }
        ]
        mock_client.top.return_value = []
        mock_zotero.return_value = mock_client

        # Mock My Publications endpoint returning 404
        mock_response = Mock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        # Create source with My Publications enabled
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12",
            group_id="123456",
            library_type="user",
            use_my_publications=True,
        )
        source = ZoteroSource(config)

        publications = source.fetch()

        # Verify My Publications endpoint was tried first
        mock_requests_get.assert_called_once_with(
            "https://api.zotero.org/users/123456/publications/items",
            headers={
                "Zotero-API-Key": "abcdef1234567890abcdef12",
                "Accept": "application/json",
            },
            params={"format": "json", "limit": 100, "start": 0},
        )

        # Verify fallback to regular library
        mock_client.everything.assert_called_once()

        # Verify publication from regular library was returned
        assert len(publications) == 1
        assert publications[0].title == "Library Publication"
        assert publications[0].source == "Zotero"

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_fetch_my_publications_bibtex_format(self, mock_zotero, mock_requests_get):
        """Test My Publications endpoint with BibTeX format."""
        # Mock Zotero client
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_zotero.return_value = mock_client

        # Mock BibTeX response
        bibtex_content = """@article{author2023research,
    title={My Research Paper},
    author={Author, John},
    journal={Research Journal},
    year={2023},
    publisher={Academic Press},
    doi={10.1234/research.2023.123}
}"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = bibtex_content
        mock_requests_get.return_value = mock_response

        # Create source with My Publications in BibTeX format
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12",
            group_id="123456",
            library_type="user",
            use_my_publications=True,
            format="bibtex",
        )
        source = ZoteroSource(config)

        publications = source.fetch()

        # Verify BibTeX endpoint was called
        mock_requests_get.assert_called_once_with(
            "https://api.zotero.org/users/123456/publications/items",
            headers={
                "Zotero-API-Key": "abcdef1234567890abcdef12",
                "Accept": "application/x-bibtex",
            },
            params={"format": "bibtex", "limit": 100, "start": 0},
        )

        # Verify publication was parsed from BibTeX
        assert len(publications) == 1
        pub = publications[0]
        assert pub.title == "My Research Paper"
        assert pub.authors[0].name == "John Author"
        assert pub.journal == "Research Journal"
        assert pub.year == 2023
        assert pub.doi == "10.1234/research.2023.123"
        assert pub.source == "Zotero My Publications"

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_fetch_my_publications_group_library_unsupported(
        self, mock_zotero, mock_requests_get
    ):
        """Test that My Publications is only supported for user libraries."""
        # Mock Zotero client
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_client.everything.return_value = []
        mock_client.top.return_value = []
        mock_zotero.return_value = mock_client

        # Create source with group library and My Publications enabled
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12",
            group_id="123456",
            library_type="group",  # Group library
            use_my_publications=True,
        )
        source = ZoteroSource(config)

        source.fetch()

        # Verify My Publications endpoint was NOT called
        mock_requests_get.assert_not_called()

        # Verify regular library method was used instead
        mock_client.everything.assert_called_once()

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_fetch_my_publications_authentication_error(
        self, mock_zotero, mock_requests_get
    ):
        """Test My Publications endpoint with authentication error."""
        # Mock Zotero client
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_zotero.return_value = mock_client

        # Mock authentication error response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_requests_get.return_value = mock_response

        # Create source with My Publications enabled
        config = ZoteroConfig(
            api_key="invalidkey567890123456ab",
            group_id="123456",
            library_type="user",
            use_my_publications=True,
        )
        source = ZoteroSource(config)

        # Should raise authentication error
        with pytest.raises(ValueError, match="authentication failed.*API key"):
            source.fetch()

    @patch("puby.sources.requests.get")
    @patch("puby.sources.zotero.Zotero")
    def test_fetch_my_publications_network_error(self, mock_zotero, mock_requests_get):
        """Test My Publications endpoint with network error."""
        # Mock Zotero client
        mock_client = Mock()
        mock_client.collections.return_value = []
        mock_zotero.return_value = mock_client

        # Mock network error
        mock_requests_get.side_effect = requests.ConnectionError("Network error")

        # Create source with My Publications enabled
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12",
            group_id="123456",
            library_type="user",
            use_my_publications=True,
        )
        source = ZoteroSource(config)

        # Should raise network error
        with pytest.raises(ValueError, match="Network error"):
            source.fetch()
