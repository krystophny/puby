"""Tests for Zotero API client."""

from unittest.mock import Mock, patch

import pytest

from puby.models import ZoteroConfig
from puby.sources import ZoteroSource


class TestZoteroSource:
    """Test ZoteroSource implementation."""

    def test_zotero_source_creation_with_config(self):
        """Test creating ZoteroSource with configuration."""
        config = ZoteroConfig(
            api_key="test_api_key", group_id="12345", library_type="group"
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
            api_key="test_key", group_id="12345", library_type="group"
        )
        ZoteroSource(config)

        mock_zotero.assert_called_once_with("12345", "group", "test_key")

    @patch("puby.sources.zotero.Zotero")
    def test_zotero_client_initialization_user(self, mock_zotero):
        """Test Zotero client initialization for user library."""
        config = ZoteroConfig(api_key="test_key", group_id="67890", library_type="user")
        ZoteroSource(config)

        mock_zotero.assert_called_once_with("67890", "user", "test_key")

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
            api_key="test_key", group_id="12345", library_type="group"
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
            api_key="test_key", group_id="12345", library_type="group"
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
            api_key="test_key", group_id="12345", library_type="group"
        )
        source = ZoteroSource(config)
        publications = source.fetch()

        # Should return empty list on error
        assert publications == []

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
            api_key="test_key", group_id="12345", library_type="group"
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
            api_key="test_key", group_id="12345", library_type="group"
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
            api_key="test_key", group_id="12345", library_type="group"
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
            api_key="test_key", group_id="12345", library_type="group"
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
            api_key="test_key", group_id="12345", library_type="group"
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
            api_key="test_api_key_12345", group_id="987654", library_type="group"
        )
        source = ZoteroSource(config)
        publications = source.fetch()

        # Verify client initialization
        mock_zotero.assert_called_once_with("987654", "group", "test_api_key_12345")

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
