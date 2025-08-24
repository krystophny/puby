"""Constants for puby package."""

# Zotero API constants
ZOTERO_API_KEY_URL = "https://www.zotero.org/settings/keys"

# Common error messages
ZOTERO_API_KEY_REQUIRED_ERROR = (
    f"API key is required for Zotero access. "
    f"Get your API key at: {ZOTERO_API_KEY_URL}"
)

ZOTERO_API_KEY_INVALID_ERROR = (
    f"Please check your API key at: {ZOTERO_API_KEY_URL}"
)

ZOTERO_API_KEY_INVALID_FORMAT_ERROR = (
    f"Invalid API key format. Zotero API keys must be exactly 24 "
    f"alphanumeric characters (letters and numbers only). "
    f"Get your API key at: {ZOTERO_API_KEY_URL}"
)