module puby_types
    implicit none
    private

    public :: publication_t, zotero_config_t, curl_config_t

    ! Core publication data structure
    type :: publication_t
        character(len=:), allocatable :: title
        character(len=:), allocatable :: authors
        character(len=:), allocatable :: journal
        character(len=:), allocatable :: year
        character(len=:), allocatable :: doi
        character(len=:), allocatable :: url
        character(len=:), allocatable :: source
    end type

    ! Zotero API configuration
    type :: zotero_config_t
        character(len=:), allocatable :: api_key
        character(len=:), allocatable :: group_id
        character(len=:), allocatable :: library_type
    end type

    ! Curl configuration (legacy - kept for compatibility with DESIGN.md)
    type :: curl_config_t
        character(len=:), allocatable :: user_agent
        integer :: timeout_seconds
        logical :: follow_redirects
        logical :: verify_ssl
    end type

end module puby_types