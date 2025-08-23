# puby

Publication List Management Tool - Compare publications across Google Scholar, ORCID, Pure, and Zotero.

## Installation

Build from source using Fortran Package Manager:

```bash
fpm build
```

Install system-wide:

```bash
fpm install --prefix ~/.local
```

Add `~/.local/bin` to your PATH if not already present.

## Basic Usage

```bash
# Compare Scholar and ORCID with Zotero group
puby check --scholar=https://scholar.google.com/citations?user=abc123 \
           --orcid=https://orcid.org/0000-1234-5678-9012 \
           --zotero=12345

# Check only ORCID against Zotero with API key
puby check --orcid=https://orcid.org/0000-1234-5678-9012 \
           --zotero=12345 --api-key=YOUR_ZOTERO_API_KEY

# Display help
puby --help
```

## Command Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--scholar=URL` | No* | Google Scholar profile URL |
| `--orcid=URL` | No* | ORCID profile URL |
| `--pure=URL` | No* | Pure research portal URL |
| `--zotero=GROUP` | Yes | Zotero group ID |
| `--api-key=KEY` | No | Zotero API key for private groups |
| `--help`, `-h` | No | Show help message |

*At least one source URL must be provided.

## Examples

### Compare Multiple Sources

```bash
puby check \
  --scholar=https://scholar.google.com/citations?user=abc123 \
  --orcid=https://orcid.org/0000-1234-5678-9012 \
  --pure=https://pure.example.edu/en/persons/researcher \
  --zotero=12345 \
  --api-key=YOUR_API_KEY
```

### Scholar Only Comparison

```bash
puby check \
  --scholar=https://scholar.google.com/citations?user=abc123 \
  --zotero=12345
```

### ORCID Only with Private Group

```bash
puby check \
  --orcid=https://orcid.org/0000-1234-5678-9012 \
  --zotero=12345 \
  --api-key=YOUR_PRIVATE_API_KEY
```

## Requirements

- Fortran compiler (gfortran recommended)
- Fortran Package Manager (fpm)
- curl library for HTTP requests
- At least one publication source URL
- Zotero group ID

## URL Formats

Valid URL formats for each source:

- **Google Scholar**: `https://scholar.google.com/citations?user=USER_ID`
- **ORCID**: `https://orcid.org/0000-XXXX-XXXX-XXXX`
- **Pure**: Any HTTPS URL pointing to a Pure research portal profile

All URLs must start with `http://` or `https://` and contain content after the protocol.
