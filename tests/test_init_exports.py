"""Tests for public API exports in __init__.py."""

import pytest


class TestPublicAPIExports:
    """Test public API exports from puby package."""

    def test_core_classes_are_exported(self):
        """Test that core classes are available in public API."""
        from puby import Author, Publication, PublicationClient, PublicationMatcher
        
        # These should be importable and be classes
        assert isinstance(Author, type)
        assert isinstance(Publication, type)
        assert isinstance(PublicationClient, type)
        assert isinstance(PublicationMatcher, type)

    def test_source_classes_are_exported(self):
        """Test that source classes are available in public API."""
        from puby import ORCIDSource, PureSource, ScholarSource
        
        # These should be importable and be classes
        assert isinstance(ORCIDSource, type)
        assert isinstance(PureSource, type)
        assert isinstance(ScholarSource, type)

    def test_api_key_function_is_exported(self):
        """Test that get_api_key function is available in public API."""
        from puby import get_api_key
        
        # Should be importable and be a function
        assert callable(get_api_key)

    def test_load_api_keys_function_removed_from_public_api(self):
        """Test that load_api_keys is no longer in public API."""
        import puby
        
        # Should not be available from main package
        assert not hasattr(puby, 'load_api_keys')
        
        # Should raise ImportError when trying to import from main package
        with pytest.raises(ImportError):
            from puby import load_api_keys

    def test_all_exports_are_defined(self):
        """Test that all items in __all__ are actually importable."""
        import puby
        
        # Get the __all__ list
        all_exports = puby.__all__
        
        # Verify each item in __all__ can be imported
        for export_name in all_exports:
            assert hasattr(puby, export_name), f"{export_name} not found in module"
            
        # Verify no extra attributes are exported beyond __all__
        public_attrs = [attr for attr in dir(puby) if not attr.startswith('_')]
        
        # Some attributes like __version__ are not in __all__ but are public
        # Modules that get imported but aren't meant to be public API
        expected_extras = [
            '__version__', 'author_utils', 'base', 'bibtex_parser', 'client', 
            'env', 'http_utils', 'matcher', 'models', 'sources', 'utils',
            'constants', 'orcid_source', 'pure_source', 'scholar_source',
            'zotero_source', 'reporter', 'similarity_utils', 'cli'
        ]
        
        for attr in public_attrs:
            if attr not in all_exports:
                assert attr in expected_extras, f"Unexpected public attribute: {attr}"

    def test_version_is_available(self):
        """Test that version is available."""
        import puby
        
        assert hasattr(puby, '__version__')
        assert isinstance(puby.__version__, str)
        assert len(puby.__version__) > 0


class TestInternalAPINotExported:
    """Test that internal functions are not accidentally exported."""

    def test_internal_functions_not_in_all(self):
        """Test that internal functions are not in __all__."""
        import puby
        
        # These should not be in the public API
        internal_functions = [
            '_initialize_sources',
            '_validate_sources', 
            '_export_missing_publications',
            '_analyze_publications',
        ]
        
        for func_name in internal_functions:
            assert func_name not in puby.__all__, f"Internal function {func_name} should not be in __all__"

    def test_can_still_import_from_modules_directly(self):
        """Test that removing from __init__ doesn't break direct imports."""
        # After removal, tests should still be able to import directly from env.py
        from puby.env import load_api_keys
        
        assert callable(load_api_keys)