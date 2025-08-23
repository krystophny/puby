module puby_cli
    implicit none
    private

    public :: cli_config_t
    public :: parse_cli_arguments
    public :: parse_arguments_from_array
    public :: display_help
    public :: validate_url

    ! CLI configuration type
    type :: cli_config_t
        character(len=:), allocatable :: scholar_url
        character(len=:), allocatable :: orcid_url
        character(len=:), allocatable :: pure_url
        character(len=:), allocatable :: zotero_group
        character(len=:), allocatable :: zotero_api_key
        character(len=:), allocatable :: command
        character(len=:), allocatable :: error_message
        logical :: help_requested = .false.
        logical :: valid = .false.
    end type cli_config_t

contains

    subroutine parse_cli_arguments(config)
        type(cli_config_t), intent(out) :: config
        character(len=256) :: arg
        character(len=256), allocatable :: args(:)
        integer :: i, nargs

        ! Get system command line arguments
        nargs = command_argument_count()
        
        if (nargs == 0) then
            allocate(args(0))
            call parse_arguments_from_array(args, config)
            return
        end if
        
        allocate(args(nargs))
        do i = 1, nargs
            call get_command_argument(i, args(i))
        end do
        
        call parse_arguments_from_array(args, config)
    end subroutine parse_cli_arguments

    subroutine parse_arguments_from_array(args, config)
        character(len=*), intent(in) :: args(:)
        type(cli_config_t), intent(out) :: config
        integer :: i, nargs
        character(len=:), allocatable :: key, value
        logical :: has_required_config, has_source_url

        ! Initialize configuration
        config = cli_config_t()
        has_required_config = .false.
        has_source_url = .false.
        
        nargs = size(args)
        
        ! Handle empty command line
        if (nargs == 0) then
            config%error_message = 'No arguments provided. Use --help for usage information.'
            config%valid = .false.
            return
        end if
        
        ! Process arguments
        do i = 1, nargs
            ! Handle help flag
            if (trim(args(i)) == '--help' .or. trim(args(i)) == '-h') then
                config%help_requested = .true.
                config%valid = .true.
                return
            end if
            
            ! Handle command (first positional argument)
            if (i == 1 .and. args(i)(1:2) /= '--') then
                config%command = trim(args(i))
                cycle
            end if
            
            ! Handle key=value arguments
            if (args(i)(1:2) == '--') then
                call parse_key_value_argument(args(i), key, value)
                
                if (.not. allocated(key) .or. .not. allocated(value)) then
                    config%error_message = 'Malformed argument: ' // trim(args(i))
                    config%valid = .false.
                    return
                end if
                
                select case (key)
                case ('scholar')
                    if (.not. validate_url(value)) then
                        config%error_message = 'Invalid Scholar URL: ' // value
                        config%valid = .false.
                        return
                    end if
                    config%scholar_url = value
                    has_source_url = .true.
                    
                case ('orcid')
                    if (.not. validate_url(value)) then
                        config%error_message = 'Invalid ORCID URL: ' // value
                        config%valid = .false.
                        return
                    end if
                    config%orcid_url = value
                    has_source_url = .true.
                    
                case ('pure')
                    if (.not. validate_url(value)) then
                        config%error_message = 'Invalid Pure URL: ' // value
                        config%valid = .false.
                        return
                    end if
                    config%pure_url = value
                    has_source_url = .true.
                    
                case ('zotero')
                    config%zotero_group = value
                    has_required_config = .true.
                    
                case ('api-key')
                    config%zotero_api_key = value
                    
                case default
                    config%error_message = 'Unknown argument: --' // key
                    config%valid = .false.
                    return
                end select
            else
                config%error_message = 'Invalid argument format: ' // trim(args(i))
                config%valid = .false.
                return
            end if
        end do
        
        ! Validate required configuration
        
        ! Validate required configuration
        if (.not. has_required_config) then
            config%error_message = &
                'Missing required Zotero configuration. Use --zotero=GROUP_ID'
            config%valid = .false.
            return
        end if
        
        if (.not. has_source_url) then
            config%error_message = 'At least one source URL must be provided ' // &
                '(--scholar, --orcid, or --pure)'
            config%valid = .false.
            return
        end if
        
        config%valid = .true.
    end subroutine parse_arguments_from_array

    subroutine parse_key_value_argument(arg, key, value)
        character(len=*), intent(in) :: arg
        character(len=:), allocatable, intent(out) :: key, value
        integer :: equals_pos
        
        ! Find equals sign
        equals_pos = index(arg, '=')
        
        if (equals_pos == 0 .or. equals_pos <= 3) then
            ! No equals sign or immediately after --
            return
        end if
        
        if (equals_pos == len_trim(arg)) then
            ! Equals at end, no value
            return
        end if
        
        ! Extract key (remove -- prefix)
        key = arg(3:equals_pos-1)
        
        ! Extract value
        value = arg(equals_pos+1:len_trim(arg))
        
        ! Validate non-empty
        if (len(key) == 0 .or. len(value) == 0) then
            if (allocated(key)) deallocate(key)
            if (allocated(value)) deallocate(value)
        end if
    end subroutine parse_key_value_argument

    logical function validate_url(url_string)
        character(len=*), intent(in) :: url_string
        character(len=:), allocatable :: trimmed_url
        integer :: len_url
        
        validate_url = .false.
        
        ! Handle empty or whitespace-only URLs
        trimmed_url = trim(adjustl(url_string))
        len_url = len(trimmed_url)
        
        if (len_url == 0) then
            return
        end if
        
        ! Check minimum length for any valid URL
        if (len_url < 7) then ! Minimum: http://x
            return
        end if
        
        ! Check for HTTP protocol
        if (len_url >= 7 .and. trimmed_url(1:7) == 'http://') then
            ! Must have content after http://
            if (len_url > 7) then
                validate_url = .true.
            end if
            return
        end if
        
        ! Check for HTTPS protocol
        if (len_url >= 8 .and. trimmed_url(1:8) == 'https://') then
            ! Must have content after https://
            if (len_url > 8) then
                validate_url = .true.
            end if
            return
        end if
        
        ! If we get here, no valid protocol was found
        validate_url = .false.
    end function validate_url

    subroutine display_help()
        write(*,'(A)') 'Puby - Publication List Management Tool'
        write(*,'(A)') ''
        write(*,'(A)') 'USAGE:'
        write(*,'(A)') '    puby check [OPTIONS]'
        write(*,'(A)') ''
        write(*,'(A)') 'COMMANDS:'
        write(*,'(A)') '    check         Compare publications across sources'
        write(*,'(A)') ''
        write(*,'(A)') 'OPTIONS:'
        write(*,'(A)') '    --scholar=URL     Google Scholar profile URL'
        write(*,'(A)') '    --orcid=URL       ORCID profile URL'
        write(*,'(A)') '    --pure=URL        Pure research portal URL'
        write(*,'(A)') '    --zotero=GROUP    Zotero group ID (required)'
        write(*,'(A)') '    --api-key=KEY     Zotero API key'
        write(*,'(A)') '    --help, -h        Show this help message'
        write(*,'(A)') ''
        write(*,'(A)') 'EXAMPLES:'
        write(*,'(A)') '    # Compare Scholar and ORCID with Zotero group'
        write(*,'(A)') '    puby check --scholar=https://scholar.google.com/... \'
        write(*,'(A)') '               --orcid=https://orcid.org/0000-... \'
        write(*,'(A)') '               --zotero=12345'
        write(*,'(A)') ''
        write(*,'(A)') '    # Check only ORCID against Zotero'
        write(*,'(A)') '    puby check --orcid=https://orcid.org/0000-... \'
        write(*,'(A)') '               --zotero=12345 --api-key=YOUR_KEY'
        write(*,'(A)') ''
        write(*,'(A)') 'REQUIREMENTS:'
        write(*,'(A)') '    - At least one source URL (--scholar, --orcid, or --pure)'
        write(*,'(A)') '    - Zotero group ID (--zotero=GROUP_ID)'
        write(*,'(A)') ''
    end subroutine display_help

end module puby_cli