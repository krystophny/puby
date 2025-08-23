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

## HTTP Client API

puby includes a Fortran HTTP client built on libcurl for API integration:

```fortran
program example
    use puby_http
    implicit none
    
    type(http_client_t) :: client
    type(http_response_t) :: response
    
    ! Initialize client with default settings
    call http_client_init(client)
    
    ! Make a GET request
    call http_get(client, "https://httpbin.org/get", response)
    if (response%success .and. response%status_code == 200) then
        print *, "Response body: ", response%body
    end if
    
    ! Make a POST request with form data
    call http_post(client, "https://httpbin.org/post", "key=value", response)
    
    ! Cleanup
    call http_client_cleanup(client)
end program
```

### Custom Configuration

```fortran
type(http_config_t) :: config
type(http_client_t) :: client

! Configure client settings
call http_config_init(config, &
    user_agent="MyApp/1.0", &
    timeout=60, &
    follow_redirects=.true., &
    verify_ssl=.true.)

! Initialize client with custom config
call http_client_init(client, config)

! Use client...

call http_client_cleanup(client)
call http_config_cleanup(config)
```

## Requirements

- Fortran compiler (gfortran recommended)
- Fortran Package Manager (fpm)
- libcurl development headers and libraries
- At least one publication source URL
- Zotero group ID

### Installing libcurl

Ubuntu/Debian:
```bash
sudo apt-get install libcurl4-openssl-dev
```

RedHat/CentOS/Fedora:
```bash
sudo yum install libcurl-devel
# or
sudo dnf install libcurl-devel
```

macOS:
```bash
brew install curl
```

## URL Formats

Valid URL formats for each source:

- **Google Scholar**: `https://scholar.google.com/citations?user=USER_ID`
- **ORCID**: `https://orcid.org/0000-XXXX-XXXX-XXXX`
- **Pure**: Any HTTPS URL pointing to a Pure research portal profile

All URLs must start with `http://` or `https://` and contain content after the protocol.
