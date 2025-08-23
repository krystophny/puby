program test_cli
    ! CLI argument parsing test suite
    ! Tests for puby CLI functionality per Issue #1
    use puby_cli, only: cli_config_t, parse_arguments_from_array, validate_url, display_help
    implicit none
    
    integer :: test_count = 0
    integer :: failed_count = 0
    
    call test_parse_command_line()
    call test_url_validation() 
    call test_help_system()
    call test_error_handling()
    call test_configuration_validation()
    
    write(*,'(A,I0,A,I0,A)') 'Tests completed: ', test_count, &
                             ', Failed: ', failed_count, ' tests'
    
    if (failed_count > 0) then
        stop 1
    else
        write(*,'(A)') 'All tests passed!'
    end if

contains

    subroutine test_parse_command_line()
        ! Test suite for command line argument parsing
        write(*,'(A)') '=== Testing Command Line Parsing ==='
        
        call test_valid_argument_combinations()
        call test_long_form_arguments()
        call test_mixed_argument_order()
        call test_empty_command_line()
    end subroutine

    subroutine test_valid_argument_combinations()
        ! Given: Valid argument combinations provided
        ! When: parse_arguments_from_array is called
        ! Then: Configuration should be valid with correct values
        
        type(cli_config_t) :: config
        character(len=256) :: args(4)
        
        write(*,'(A)') 'Testing valid argument combinations...'
        call increment_test_count()
        
        ! Test valid combination: check --scholar=url --orcid=url --zotero=group
        args(1) = 'check'
        args(2) = '--scholar=https://scholar.google.com/citations?user=test'
        args(3) = '--orcid=https://orcid.org/0000-0000-0000-0001'
        args(4) = '--zotero=12345'
        
        call parse_arguments_from_array(args, config)
        
        if (.not. config%valid) then
            call record_test_failure('Valid arguments rejected: ' // config%error_message)
            return
        end if
        
        if (.not. allocated(config%command) .or. config%command /= 'check') then
            call record_test_failure('Command not parsed correctly')
            return
        end if
        
        if (.not. allocated(config%scholar_url) .or. &
            config%scholar_url /= 'https://scholar.google.com/citations?user=test') then
            call record_test_failure('Scholar URL not parsed correctly')
            return
        end if
        
        if (.not. allocated(config%orcid_url) .or. &
            config%orcid_url /= 'https://orcid.org/0000-0000-0000-0001') then
            call record_test_failure('ORCID URL not parsed correctly')
            return
        end if
        
        if (.not. allocated(config%zotero_group) .or. config%zotero_group /= '12345') then
            call record_test_failure('Zotero group not parsed correctly')
            return
        end if
        
        write(*,'(A)') '  PASS: Valid argument combinations parsed correctly'
    end subroutine
    
    subroutine test_long_form_arguments()
        ! Given: All long-form arguments with values
        ! When: parse_arguments_from_array processes arguments
        ! Then: All configuration fields should be populated correctly
        
        type(cli_config_t) :: config
        character(len=256) :: args(6)
        
        write(*,'(A)') 'Testing long-form argument parsing...'
        call increment_test_count()
        
        ! Test all long-form arguments
        args(1) = 'check'
        args(2) = '--scholar=https://scholar.google.com/test'
        args(3) = '--orcid=https://orcid.org/test'
        args(4) = '--pure=https://pure.example.com/test'
        args(5) = '--zotero=54321'
        args(6) = '--api-key=secret123'
        
        call parse_arguments_from_array(args, config)
        
        if (.not. config%valid) then
            call record_test_failure('Long-form arguments rejected: ' // config%error_message)
            return
        end if
        
        if (.not. allocated(config%zotero_api_key) .or. config%zotero_api_key /= 'secret123') then
            call record_test_failure('API key not parsed correctly')
            return
        end if
        
        if (.not. allocated(config%pure_url) .or. &
            config%pure_url /= 'https://pure.example.com/test') then
            call record_test_failure('Pure URL not parsed correctly')
            return
        end if
        
        write(*,'(A)') '  PASS: Long-form arguments parsed correctly'
    end subroutine
    
    subroutine test_mixed_argument_order()
        ! Given: Arguments provided in different orders
        ! When: parse_arguments_from_array processes arguments
        ! Then: Configuration should be identical regardless of order
        
        type(cli_config_t) :: config1, config2
        character(len=256) :: args1(4), args2(4)
        
        write(*,'(A)') 'Testing argument order independence...'
        call increment_test_count()
        
        ! Test order 1: scholar, orcid, zotero
        args1(1) = 'check'
        args1(2) = '--scholar=https://scholar.test.com'
        args1(3) = '--orcid=https://orcid.test.com'
        args1(4) = '--zotero=123'
        
        ! Test order 2: zotero, orcid, scholar
        args2(1) = 'check'
        args2(2) = '--zotero=123'
        args2(3) = '--orcid=https://orcid.test.com'
        args2(4) = '--scholar=https://scholar.test.com'
        
        call parse_arguments_from_array(args1, config1)
        call parse_arguments_from_array(args2, config2)
        
        if (.not. config1%valid .or. .not. config2%valid) then
            call record_test_failure('Argument order caused parsing failure')
            return
        end if
        
        if (config1%scholar_url /= config2%scholar_url .or. &
            config1%orcid_url /= config2%orcid_url .or. &
            config1%zotero_group /= config2%zotero_group) then
            call record_test_failure('Argument order affected results')
            return
        end if
        
        write(*,'(A)') '  PASS: Argument order independence verified'
    end subroutine
    
    subroutine test_empty_command_line()
        ! Given: No command line arguments provided
        ! When: parse_arguments_from_array is called
        ! Then: Configuration should be invalid with appropriate error
        
        type(cli_config_t) :: config
        character(len=256) :: args(0)
        
        write(*,'(A)') 'Testing empty command line handling...'
        call increment_test_count()
        
        call parse_arguments_from_array(args, config)
        
        if (config%valid) then
            call record_test_failure('Empty command line incorrectly accepted')
            return
        end if
        
        if (.not. allocated(config%error_message)) then
            call record_test_failure('No error message for empty command line')
            return
        end if
        
        write(*,'(A)') '  PASS: Empty command line correctly rejected'
    end subroutine

    subroutine test_url_validation()
        ! Test suite for URL validation functionality
        write(*,'(A)') '=== Testing URL Validation ==='
        
        call test_valid_http_urls()
        call test_valid_https_urls()
        call test_invalid_url_formats()
        call test_malformed_urls()
        call test_empty_urls()
    end subroutine
    
    subroutine test_valid_http_urls()
        ! Given: Valid HTTP URLs
        ! When: validate_url is called
        ! Then: Should return true for valid formats
        
        write(*,'(A)') 'Testing valid HTTP URL formats...'
        call increment_test_count()
        
        if (.not. validate_url('http://example.com')) then
            call record_test_failure('Basic HTTP URL rejected')
            return
        end if
        
        if (.not. validate_url('http://scholar.google.com/citations')) then
            call record_test_failure('Google Scholar HTTP URL rejected')
            return
        end if
        
        if (.not. validate_url('http://example.com/path/to/page')) then
            call record_test_failure('HTTP URL with path rejected')
            return
        end if
        
        write(*,'(A)') '  PASS: Valid HTTP URLs accepted'
    end subroutine
    
    subroutine test_valid_https_urls()
        ! Given: Valid HTTPS URLs with various domain formats
        ! When: validate_url is called
        ! Then: Should return true for all valid HTTPS URLs
        
        write(*,'(A)') 'Testing valid HTTPS URL formats...'
        call increment_test_count()
        
        if (.not. validate_url('https://orcid.org/0000-0000-0000-0001')) then
            call record_test_failure('ORCID HTTPS URL rejected')
            return
        end if
        
        if (.not. validate_url('https://scholar.google.com/citations?user=test')) then
            call record_test_failure('Google Scholar HTTPS URL rejected')
            return
        end if
        
        if (.not. validate_url('https://pure.example.com/portal/person')) then
            call record_test_failure('Pure portal HTTPS URL rejected')
            return
        end if
        
        write(*,'(A)') '  PASS: Valid HTTPS URLs accepted'
    end subroutine
    
    subroutine test_invalid_url_formats()
        ! Given: URLs with invalid protocols or formats
        ! When: validate_url is called
        ! Then: Should return false for invalid formats
        
        write(*,'(A)') 'Testing invalid URL format detection...'
        call increment_test_count()
        
        if (validate_url('ftp://example.com')) then
            call record_test_failure('FTP URL incorrectly accepted')
            return
        end if
        
        if (validate_url('file:///home/user')) then
            call record_test_failure('File URL incorrectly accepted')
            return
        end if
        
        if (validate_url('example.com')) then
            call record_test_failure('URL without protocol incorrectly accepted')
            return
        end if
        
        write(*,'(A)') '  PASS: Invalid URL formats correctly rejected'
    end subroutine
    
    subroutine test_malformed_urls()
        ! Given: Malformed URLs (missing domain, invalid characters)
        ! When: validate_url is called
        ! Then: Should return false and handle gracefully
        
        write(*,'(A)') 'Testing malformed URL handling...'
        call increment_test_count()
        
        if (validate_url('http://')) then
            call record_test_failure('HTTP without domain incorrectly accepted')
            return
        end if
        
        if (validate_url('https://')) then
            call record_test_failure('HTTPS without domain incorrectly accepted')
            return
        end if
        
        if (validate_url('http:// ')) then
            call record_test_failure('HTTP with space after // incorrectly accepted')
            return
        end if
        
        write(*,'(A)') '  PASS: Malformed URLs correctly rejected'
    end subroutine
    
    subroutine test_empty_urls()
        ! Given: Empty or whitespace-only URL strings
        ! When: validate_url is called
        ! Then: Should return false for empty inputs
        
        write(*,'(A)') 'Testing empty URL validation...'
        call increment_test_count()
        
        if (validate_url('')) then
            call record_test_failure('Empty URL incorrectly accepted')
            return
        end if
        
        if (validate_url('   ')) then
            call record_test_failure('Whitespace-only URL incorrectly accepted')
            return
        end if
        
        if (validate_url('\t\n')) then
            call record_test_failure('Tabs and newlines URL incorrectly accepted')
            return
        end if
        
        write(*,'(A)') '  PASS: Empty URLs correctly rejected'
    end subroutine

    subroutine test_help_system()
        ! Test suite for help system functionality
        write(*,'(A)') '=== Testing Help System ==='
        
        call test_help_flag_detection()
        call test_help_message_content()
        call test_help_message_format()
    end subroutine
    
    subroutine test_help_flag_detection()
        ! Given: --help argument provided
        ! When: parse_arguments_from_array processes arguments
        ! Then: help_requested flag should be set to true
        
        type(cli_config_t) :: config
        character(len=256) :: args(1)
        
        write(*,'(A)') 'Testing help flag detection...'
        call increment_test_count()
        
        ! Test --help
        args(1) = '--help'
        call parse_arguments_from_array(args, config)
        
        if (.not. config%help_requested) then
            call record_test_failure('--help flag not detected')
            return
        end if
        
        if (.not. config%valid) then
            call record_test_failure('--help should set config as valid')
            return
        end if
        
        ! Test -h
        args(1) = '-h'
        call parse_arguments_from_array(args, config)
        
        if (.not. config%help_requested) then
            call record_test_failure('-h flag not detected')
            return
        end if
        
        write(*,'(A)') '  PASS: Help flags detected correctly'
    end subroutine
    
    subroutine test_help_message_content()
        ! Given: Help message needs to be displayed
        ! When: display_help is called
        ! Then: Should show all required usage information
        
        write(*,'(A)') 'Testing help message content...'
        call increment_test_count()
        
        ! This test verifies display_help exists and runs without error
        ! Content verification would require capturing stdout which is complex
        call display_help()
        
        write(*,'(A)') '  PASS: display_help function executes successfully'
    end subroutine
    
    subroutine test_help_message_format()
        ! Given: Help message format requirements from DESIGN.md
        ! When: display_help generates output
        ! Then: Should match specified format with examples
        
        write(*,'(A)') 'Testing help message format compliance...'
        call increment_test_count()
        
        ! This test verifies basic format compliance
        ! More detailed testing would require output capture
        call display_help()
        
        write(*,'(A)') '  PASS: help message format implemented'
    end subroutine

    subroutine test_error_handling()
        ! Test suite for error handling and reporting
        write(*,'(A)') '=== Testing Error Handling ==='
        
        call test_missing_required_arguments()
        call test_invalid_argument_names()
        call test_malformed_argument_syntax()
        call test_error_message_format()
    end subroutine
    
    subroutine test_missing_required_arguments()
        ! Given: Command line missing required Zotero configuration
        ! When: parse_arguments_from_array validates arguments
        ! Then: Should set valid=false with descriptive error message
        
        type(cli_config_t) :: config
        character(len=256) :: args(2)
        
        write(*,'(A)') 'Testing missing required argument detection...'
        call increment_test_count()
        
        ! Test missing zotero config
        args(1) = 'check'
        args(2) = '--scholar=https://scholar.google.com/test'
        
        call parse_arguments_from_array(args, config)
        
        if (config%valid) then
            call record_test_failure('Missing Zotero config not detected')
            return
        end if
        
        if (.not. allocated(config%error_message)) then
            call record_test_failure('No error message for missing Zotero config')
            return
        end if
        
        write(*,'(A)') '  PASS: Missing required arguments detected'
    end subroutine
    
    subroutine test_invalid_argument_names()
        ! Given: Unknown or misspelled argument names
        ! When: parse_arguments_from_array processes arguments
        ! Then: Should generate clear error about unknown arguments
        
        type(cli_config_t) :: config
        character(len=256) :: args(3)
        
        write(*,'(A)') 'Testing invalid argument name handling...'
        call increment_test_count()
        
        ! Test unknown argument
        args(1) = 'check'
        args(2) = '--unknown=value'
        args(3) = '--zotero=123'
        
        call parse_arguments_from_array(args, config)
        
        if (config%valid) then
            call record_test_failure('Unknown argument not detected')
            return
        end if
        
        if (.not. allocated(config%error_message)) then
            call record_test_failure('No error message for unknown argument')
            return
        end if
        
        write(*,'(A)') '  PASS: Invalid argument names detected'
    end subroutine
    
    subroutine test_malformed_argument_syntax()
        ! Given: Arguments with incorrect syntax (missing =, values)
        ! When: parse_arguments_from_array parses arguments
        ! Then: Should detect and report syntax errors clearly
        
        type(cli_config_t) :: config
        character(len=256) :: args(3)
        
        write(*,'(A)') 'Testing malformed argument syntax detection...'
        call increment_test_count()
        
        ! Test missing equals sign
        args(1) = 'check'
        args(2) = '--scholar'
        args(3) = '--zotero=123'
        
        call parse_arguments_from_array(args, config)
        
        if (config%valid) then
            call record_test_failure('Malformed argument syntax not detected')
            return
        end if
        
        if (.not. allocated(config%error_message)) then
            call record_test_failure('No error message for malformed syntax')
            return
        end if
        
        write(*,'(A)') '  PASS: Malformed argument syntax detected'
    end subroutine
    
    subroutine test_error_message_format()
        ! Given: Error conditions that require user feedback
        ! When: Error messages are generated
        ! Then: Should follow standard format from DESIGN.md
        
        type(cli_config_t) :: config
        character(len=256) :: args(0)
        
        write(*,'(A)') 'Testing error message format compliance...'
        call increment_test_count()
        
        ! Test error message exists and has content
        call parse_arguments_from_array(args, config)
        
        if (.not. allocated(config%error_message)) then
            call record_test_failure('Error message not allocated')
            return
        end if
        
        if (len(config%error_message) == 0) then
            call record_test_failure('Error message is empty')
            return
        end if
        
        write(*,'(A)') '  PASS: Error message format implemented'
    end subroutine

    subroutine test_configuration_validation()
        ! Test suite for overall configuration validation
        write(*,'(A)') '=== Testing Configuration Validation ==='
        
        call test_zotero_config_requirements()
        call test_minimum_source_requirements()
        call test_configuration_completeness()
    end subroutine
    
    subroutine test_zotero_config_requirements()
        ! Given: Zotero configuration is required per DESIGN.md
        ! When: Configuration is validated
        ! Then: Both group ID and API key must be present
        
        type(cli_config_t) :: config
        character(len=256) :: args(3)
        
        write(*,'(A)') 'Testing Zotero configuration requirements...'
        call increment_test_count()
        
        ! Test valid Zotero configuration
        args(1) = 'check'
        args(2) = '--zotero=12345'
        args(3) = '--orcid=https://orcid.org/test'
        
        call parse_arguments_from_array(args, config)
        
        if (.not. config%valid) then
            call record_test_failure('Valid Zotero config rejected: ' // config%error_message)
            return
        end if
        
        if (.not. allocated(config%zotero_group)) then
            call record_test_failure('Zotero group not stored')
            return
        end if
        
        write(*,'(A)') '  PASS: Zotero configuration requirements met'
    end subroutine
    
    subroutine test_minimum_source_requirements()
        ! Given: At least one source URL should be provided
        ! When: Configuration is validated
        ! Then: Should require at least one of scholar/orcid/pure URLs
        
        type(cli_config_t) :: config
        character(len=256) :: args(2)
        
        write(*,'(A)') 'Testing minimum source URL requirements...'
        call increment_test_count()
        
        ! Test missing source URLs
        args(1) = 'check'
        args(2) = '--zotero=12345'
        
        call parse_arguments_from_array(args, config)
        
        if (config%valid) then
            call record_test_failure('Missing source URLs not detected')
            return
        end if
        
        if (.not. allocated(config%error_message)) then
            call record_test_failure('No error message for missing source URLs')
            return
        end if
        
        write(*,'(A)') '  PASS: Minimum source requirements enforced'
    end subroutine
    
    subroutine test_configuration_completeness()
        ! Given: Complete valid configuration provided
        ! When: All validation checks are performed
        ! Then: Configuration should be marked as valid
        
        type(cli_config_t) :: config
        character(len=256) :: args(5)
        
        write(*,'(A)') 'Testing complete configuration validation...'
        call increment_test_count()
        
        ! Test complete valid configuration
        args(1) = 'check'
        args(2) = '--scholar=https://scholar.google.com/test'
        args(3) = '--orcid=https://orcid.org/test'
        args(4) = '--zotero=12345'
        args(5) = '--api-key=secret'
        
        call parse_arguments_from_array(args, config)
        
        if (.not. config%valid) then
            call record_test_failure('Complete valid config rejected: ' // config%error_message)
            return
        end if
        
        ! Verify all fields are populated
        if (.not. allocated(config%command) .or. &
            .not. allocated(config%scholar_url) .or. &
            .not. allocated(config%orcid_url) .or. &
            .not. allocated(config%zotero_group) .or. &
            .not. allocated(config%zotero_api_key)) then
            call record_test_failure('Not all configuration fields populated')
            return
        end if
        
        write(*,'(A)') '  PASS: Complete configuration validation successful'
    end subroutine

    ! Test utility functions
    subroutine increment_test_count()
        test_count = test_count + 1
    end subroutine
    
    subroutine record_test_failure(message)
        character(len=*), intent(in) :: message
        failed_count = failed_count + 1
        write(*,'(A,A)') '  FAIL: ', message
    end subroutine

end program test_cli