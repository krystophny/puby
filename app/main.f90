program main
    use puby_cli, only: cli_config_t, parse_cli_arguments, display_help
    implicit none

    type(cli_config_t) :: config

    ! Parse command line arguments
    call parse_cli_arguments(config)

    ! Handle help request
    if (config%help_requested) then
        call display_help()
        stop 0
    end if

    ! Handle parsing errors
    if (.not. config%valid) then
        write(*,'(A,A)') 'Error: ', config%error_message
        write(*,'(A)') ''
        write(*,'(A)') 'Use --help for usage information.'
        stop 1
    end if

    ! Display parsed configuration for MVP
    write(*,'(A)') 'Puby - Publication List Management Tool'
    write(*,'(A)') 'Configuration parsed successfully:'
    
    if (allocated(config%command)) then
        write(*,'(A,A)') '  Command: ', config%command
    end if
    
    if (allocated(config%scholar_url)) then
        write(*,'(A,A)') '  Scholar URL: ', config%scholar_url
    end if
    
    if (allocated(config%orcid_url)) then
        write(*,'(A,A)') '  ORCID URL: ', config%orcid_url
    end if
    
    if (allocated(config%pure_url)) then
        write(*,'(A,A)') '  Pure URL: ', config%pure_url
    end if
    
    if (allocated(config%zotero_group)) then
        write(*,'(A,A)') '  Zotero Group: ', config%zotero_group
    end if
    
    if (allocated(config%zotero_api_key)) then
        write(*,'(A,A)') '  API Key: [PROVIDED]'
    end if

    write(*,'(A)') ''
    write(*,'(A)') 'CLI implementation complete. Ready for Phase 2 development.'

end program main
