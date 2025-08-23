module puby
    use puby_types
    use puby_http
    use puby_curl
    implicit none
    private

    ! Re-export types
    public :: publication_t, zotero_config_t, curl_config_t
    public :: http_client_t, http_response_t, http_config_t, http_headers_t
    public :: curl_handle_t, curl_error_t

    ! Re-export HTTP client functionality
    public :: http_client_init, http_client_cleanup
    public :: http_get, http_post, http_get_with_options
    public :: http_config_init, http_config_cleanup
    public :: http_headers_init, http_headers_cleanup, http_headers_add

    ! Re-export low-level curl bindings for advanced users
    public :: curl_init, curl_cleanup, curl_perform
    public :: curl_setopt_url, curl_setopt_writefunction, curl_setopt_writedata
    public :: curl_setopt_useragent, curl_setopt_timeout
    public :: curl_setopt_followlocation, curl_setopt_ssl_verifypeer
    public :: curl_getinfo_response_code
    public :: writefunction_callback

    ! Legacy functionality
    public :: say_hello

contains
    subroutine say_hello
        print *, "Hello, puby!"
    end subroutine say_hello
end module puby
