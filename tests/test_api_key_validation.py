"""Test API key format validation for Zotero."""

import pytest
from puby.models import ZoteroConfig


class TestZoteroAPIKeyFormatValidation:
    """Test format validation for Zotero API keys."""

    def test_valid_api_key_formats(self):
        """Test various valid API key formats."""
        valid_keys = [
            "P9NiFoyLeZu2bZNvvuQPDWsd",  # From Zotero docs
            "Io1bwAiOjB1jPgUNegjJhJxF",  # Example format
            "7lhgvcwVq60CDi7E68FyE3br",  # Another example
            "ABCDEFGHIJKLMNPQRSTUVWXYZ"[:24],  # All caps, 24 chars
            "abcdefghijklmnpqrstuvwxyz"[:24],  # All lowercase, 24 chars
            "123456789012345678901234",  # All numbers
            "A1b2C3d4E5f6G7h8I9j0K1l2",  # Mixed case and numbers
        ]
        
        for key in valid_keys:
            config = ZoteroConfig(api_key=key, library_type="user")
            assert config.is_valid(), f"Key {key} should be valid"
            assert len(config.validation_errors()) == 0

    def test_invalid_api_key_formats(self):
        """Test various invalid API key formats."""
        invalid_cases = [
            ("", "empty string"),
            ("   ", "whitespace only"),
            ("\t\n  ", "whitespace characters"),
            ("short", "too short"),
            ("P9NiFoyLeZu2bZNvvuQPDWs", "23 characters - too short"),
            ("P9NiFoyLeZu2bZNvvuQPDWsdX", "25 characters - too long"),
            ("P9NiFoyLeZu2bZNvvuQPDWsd\n", "24 chars with newline"),
            ("P9NiFoyLeZu2bZNvvuQPDWsd ", "24 chars with space"),
            ("P9Ni!oyLeZu2bZNvvuQPDWsd", "contains exclamation mark"),
            ("P9Ni@oyLeZu2bZNvvuQPDWsd", "contains at symbol"),
            ("P9Ni#oyLeZu2bZNvvuQPDWsd", "contains hash"),
            ("P9Ni$oyLeZu2bZNvvuQPDWsd", "contains dollar sign"),
            ("P9Ni%oyLeZu2bZNvvuQPDWsd", "contains percent"),
            ("P9Ni^oyLeZu2bZNvvuQPDWsd", "contains caret"),
            ("P9Ni&oyLeZu2bZNvvuQPDWsd", "contains ampersand"),
            ("P9Ni*oyLeZu2bZNvvuQPDWsd", "contains asterisk"),
            ("P9Ni(oyLeZu2bZNvvuQPDWsd", "contains parenthesis"),
            ("P9Ni)oyLeZu2bZNvvuQPDWsd", "contains parenthesis"),
            ("P9Ni-oyLeZu2bZNvvuQPDWsd", "contains dash"),
            ("P9Ni_oyLeZu2bZNvvuQPDWsd", "contains underscore"),
            ("P9Ni=oyLeZu2bZNvvuQPDWsd", "contains equals"),
            ("P9Ni+oyLeZu2bZNvvuQPDWsd", "contains plus"),
            ("P9Ni[oyLeZu2bZNvvuQPDWsd", "contains bracket"),
            ("P9Ni]oyLeZu2bZNvvuQPDWsd", "contains bracket"),
            ("P9Ni{oyLeZu2bZNvvuQPDWsd", "contains brace"),
            ("P9Ni}oyLeZu2bZNvvuQPDWsd", "contains brace"),
            ("P9Ni\\oyLeZu2bZNvvuQPDWsd", "contains backslash"),
            ("P9Ni|oyLeZu2bZNvvuQPDWsd", "contains pipe"),
            ("P9Ni;oyLeZu2bZNvvuQPDWsd", "contains semicolon"),
            ("P9Ni:oyLeZu2bZNvvuQPDWsd", "contains colon"),
            ("P9Ni'oyLeZu2bZNvvuQPDWsd", "contains quote"),
            ('P9Ni"oyLeZu2bZNvvuQPDWsd', "contains double quote"),
            ("P9Ni,oyLeZu2bZNvvuQPDWsd", "contains comma"),
            ("P9Ni.oyLeZu2bZNvvuQPDWsd", "contains dot"),
            ("P9Ni<oyLeZu2bZNvvuQPDWsd", "contains less than"),
            ("P9Ni>oyLeZu2bZNvvuQPDWsd", "contains greater than"),
            ("P9Ni?oyLeZu2bZNvvuQPDWsd", "contains question mark"),
            ("P9Ni/oyLeZu2bZNvvuQPDWsd", "contains slash"),
            ("P9NiFoyLeZu2bZNvvuQPDWs🔑", "contains emoji"),
            ("P9NiFoyLeZu2bZNvvuQPDWsâ", "contains unicode"),
        ]
        
        for key, description in invalid_cases:
            config = ZoteroConfig(api_key=key, library_type="user")
            assert not config.is_valid(), f"Key should be invalid: {description}"
            errors = config.validation_errors()
            assert len(errors) > 0, f"Should have validation errors: {description}"
            # Should have specific format error, not just "required" error
            format_error_found = any(
                "format" in error.lower() or "invalid" in error.lower() 
                for error in errors
            )
            if key.strip():  # Not empty/whitespace - should have format error
                assert format_error_found, f"Should have format error for: {description}"

    def test_api_key_format_error_message_clarity(self):
        """Test that format validation provides clear error messages."""
        # Test various invalid formats
        config = ZoteroConfig(api_key="invalid_key", library_type="user")
        assert not config.is_valid()
        errors = config.validation_errors()
        
        # Should have specific format validation message
        assert any("format" in error.lower() for error in errors), \
            "Should mention format in error message"
        assert any("24" in error for error in errors), \
            "Should mention expected length"
        assert any("alphanumeric" in error.lower() for error in errors), \
            "Should mention character requirements"

    def test_edge_case_api_keys(self):
        """Test edge cases that might appear valid but aren't."""
        edge_cases = [
            "000000000000000000000000",  # All zeros - technically valid format
            "111111111111111111111111",  # All ones - technically valid format
            "P9NiFoyLeZu2bZNvvuQPDWs\0",  # Null terminator
            "P9NiFoyLeZu2bZNvvuQPDWs\r",  # Carriage return
            "\0P9NiFoyLeZu2bZNvvuQPDWs",  # Leading null
            "P9NiFoyLeZu2bZNvvuQPDW💖d",  # Unicode heart in middle
        ]
        
        for key in edge_cases:
            config = ZoteroConfig(api_key=key, library_type="user")
            # These should all be invalid due to format requirements
            if len(key) == 24 and key.isalnum():
                # If it's exactly 24 alphanumeric chars, it should be valid
                assert config.is_valid(), f"Valid 24-char alphanumeric key rejected: {repr(key)}"
            else:
                assert not config.is_valid(), f"Invalid key accepted: {repr(key)}"

    def test_api_key_validation_with_other_config_errors(self):
        """Test API key validation doesn't interfere with other validation."""
        # Invalid API key AND missing group ID for group library
        config = ZoteroConfig(api_key="short", library_type="group")
        assert not config.is_valid()
        errors = config.validation_errors()
        
        # Should have both API key format error and group ID error
        api_key_error = any("format" in error.lower() for error in errors)
        group_id_error = any("group id" in error.lower() for error in errors)
        
        assert api_key_error, "Should have API key format error"
        assert group_id_error, "Should have group ID error"

    def test_none_api_key_handling(self):
        """Test that None API key is handled appropriately."""
        # With dataclass, None is actually allowed as a value for str fields
        # So we test that our validation catches it properly
        config = ZoteroConfig(api_key=None, library_type="user")  # type: ignore
        assert not config.is_valid()
        errors = config.validation_errors()
        assert any("API key is required" in error for error in errors)

    def test_api_key_strip_behavior(self):
        """Test that API keys are validated as-is, not stripped."""
        # Key with leading/trailing spaces - should be invalid
        config = ZoteroConfig(api_key=" P9NiFoyLeZu2bZNvvuQPDWsd ", library_type="user")
        assert not config.is_valid()
        errors = config.validation_errors()
        assert any("format" in error.lower() for error in errors)
        
        # The validation should not strip - users should provide exact key
        # This ensures we don't accidentally accept malformed keys