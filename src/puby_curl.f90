module puby_curl
    use iso_c_binding, only: c_ptr, c_null_ptr, c_int, c_long, c_char, &
                             c_null_char, c_size_t, c_funptr, c_f_pointer, &
                             c_associated, c_loc
    implicit none
    private

    ! Public types and interfaces
    public :: curl_handle_t, curl_error_t, response_buffer_t
    public :: curl_init, curl_cleanup, curl_perform
    ! Public constants
    public :: CURLE_OK, CURLE_FAILED_INIT, CURLOPT_POSTFIELDS, CURLOPT_POSTFIELDSIZE
    public :: curl_setopt_url, curl_setopt_writefunction, curl_setopt_writedata
    public :: curl_setopt_useragent, curl_setopt_timeout, curl_setopt_followlocation
    public :: curl_setopt_ssl_verifypeer, curl_setopt_httpheader
    public :: curl_getinfo_response_code
    public :: writefunction_callback
    ! Low-level C interface functions (for advanced users)
    public :: c_curl_easy_setopt_ptr, c_curl_easy_setopt_long

    ! libcurl constants
    integer(c_int), parameter :: CURLOPT_URL = 10002
    integer(c_int), parameter :: CURLOPT_WRITEFUNCTION = 20011
    integer(c_int), parameter :: CURLOPT_WRITEDATA = 10001
    integer(c_int), parameter :: CURLOPT_USERAGENT = 10018
    integer(c_int), parameter :: CURLOPT_TIMEOUT = 13
    integer(c_int), parameter :: CURLOPT_FOLLOWLOCATION = 52
    integer(c_int), parameter :: CURLOPT_SSL_VERIFYPEER = 64
    integer(c_int), parameter :: CURLOPT_HTTPHEADER = 10023
    integer(c_int), parameter :: CURLOPT_POSTFIELDS = 10015
    integer(c_int), parameter :: CURLOPT_POSTFIELDSIZE = 60
    integer(c_int), parameter :: CURLINFO_RESPONSE_CODE = 2097154

    ! libcurl error codes
    integer(c_int), parameter :: CURLE_OK = 0
    integer(c_int), parameter :: CURLE_UNSUPPORTED_PROTOCOL = 1
    integer(c_int), parameter :: CURLE_FAILED_INIT = 2
    integer(c_int), parameter :: CURLE_URL_MALFORMAT = 3
    integer(c_int), parameter :: CURLE_COULDNT_RESOLVE_PROXY = 5
    integer(c_int), parameter :: CURLE_COULDNT_RESOLVE_HOST = 6
    integer(c_int), parameter :: CURLE_COULDNT_CONNECT = 7
    integer(c_int), parameter :: CURLE_OPERATION_TIMEDOUT = 28

    ! Response buffer type for C callback
    type :: response_buffer_t
        character(len=:), allocatable :: data
        integer :: size
    end type

    ! Wrapper type for curl handle
    type :: curl_handle_t
        type(c_ptr) :: handle = c_null_ptr
    end type

    ! Error type for curl operations
    type :: curl_error_t
        integer :: code
        character(len=256) :: message
        logical :: success
    end type

    ! ISO C binding interface to libcurl functions
    interface
        function c_curl_easy_init() bind(c, name='curl_easy_init')
            import :: c_ptr
            type(c_ptr) :: c_curl_easy_init
        end function

        subroutine c_curl_easy_cleanup(curl) bind(c, name='curl_easy_cleanup')
            import :: c_ptr
            type(c_ptr), value :: curl
        end subroutine

        function c_curl_easy_setopt_ptr(curl, option, parameter) &
                bind(c, name='curl_easy_setopt')
            import :: c_ptr, c_int
            type(c_ptr), value :: curl
            integer(c_int), value :: option
            type(c_ptr), value :: parameter
            integer(c_int) :: c_curl_easy_setopt_ptr
        end function

        function c_curl_easy_setopt_long(curl, option, parameter) &
                bind(c, name='curl_easy_setopt')
            import :: c_ptr, c_int, c_long
            type(c_ptr), value :: curl
            integer(c_int), value :: option
            integer(c_long), value :: parameter
            integer(c_int) :: c_curl_easy_setopt_long
        end function

        function c_curl_easy_perform(curl) bind(c, name='curl_easy_perform')
            import :: c_ptr, c_int
            type(c_ptr), value :: curl
            integer(c_int) :: c_curl_easy_perform
        end function

        function c_curl_easy_getinfo_long(curl, info, parameter) &
                bind(c, name='curl_easy_getinfo')
            import :: c_ptr, c_int, c_long
            type(c_ptr), value :: curl
            integer(c_int), value :: info
            integer(c_long) :: parameter
            integer(c_int) :: c_curl_easy_getinfo_long
        end function

    end interface

contains

    subroutine curl_init(handle, error)
        type(curl_handle_t), intent(out) :: handle
        type(curl_error_t), intent(out) :: error

        handle%handle = c_curl_easy_init()
        
        if (c_associated(handle%handle)) then
            error%code = CURLE_OK
            error%message = "curl handle initialized successfully"
            error%success = .true.
        else
            error%code = CURLE_FAILED_INIT
            error%message = "failed to initialize curl handle"
            error%success = .false.
        end if
    end subroutine

    subroutine curl_cleanup(handle)
        type(curl_handle_t), intent(inout) :: handle

        if (c_associated(handle%handle)) then
            call c_curl_easy_cleanup(handle%handle)
            handle%handle = c_null_ptr
        end if
    end subroutine

    subroutine curl_perform(handle, error)
        type(curl_handle_t), intent(in) :: handle
        type(curl_error_t), intent(out) :: error
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        res = c_curl_easy_perform(handle%handle)
        error%code = res
        error%success = (res == CURLE_OK)
        
        select case (res)
        case (CURLE_OK)
            error%message = "request completed successfully"
        case (CURLE_URL_MALFORMAT)
            error%message = "malformed URL"
        case (CURLE_COULDNT_RESOLVE_HOST)
            error%message = "could not resolve host"
        case (CURLE_COULDNT_CONNECT)
            error%message = "could not connect to server"
        case (CURLE_OPERATION_TIMEDOUT)
            error%message = "operation timed out"
        case default
            write(error%message, '(A,I0)') "curl error code: ", res
        end select
    end subroutine

    subroutine curl_setopt_url(handle, url, error)
        type(curl_handle_t), intent(in) :: handle
        character(len=*), intent(in) :: url
        type(curl_error_t), intent(out) :: error
        character(len=len(url)+1, kind=c_char), target :: c_url
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        c_url = trim(url) // c_null_char
        res = c_curl_easy_setopt_ptr(handle%handle, CURLOPT_URL, c_loc(c_url))
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "URL set successfully"
        else
            write(error%message, '(A,I0)') "failed to set URL, error: ", res
        end if
    end subroutine

    subroutine curl_setopt_writefunction(handle, callback, error)
        type(curl_handle_t), intent(in) :: handle
        type(c_funptr), intent(in) :: callback
        type(curl_error_t), intent(out) :: error
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        res = c_curl_easy_setopt_ptr(handle%handle, CURLOPT_WRITEFUNCTION, &
                                     callback)
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "write function set successfully"
        else
            write(error%message, '(A,I0)') &
                "failed to set write function, error: ", res
        end if
    end subroutine

    subroutine curl_setopt_writedata(handle, data_ptr, error)
        type(curl_handle_t), intent(in) :: handle
        type(c_ptr), intent(in) :: data_ptr
        type(curl_error_t), intent(out) :: error
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        res = c_curl_easy_setopt_ptr(handle%handle, CURLOPT_WRITEDATA, data_ptr)
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "write data pointer set successfully"
        else
            write(error%message, '(A,I0)') &
                "failed to set write data pointer, error: ", res
        end if
    end subroutine

    subroutine curl_setopt_useragent(handle, user_agent, error)
        type(curl_handle_t), intent(in) :: handle
        character(len=*), intent(in) :: user_agent
        type(curl_error_t), intent(out) :: error
        character(len=len(user_agent)+1, kind=c_char), target :: c_user_agent
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        c_user_agent = trim(user_agent) // c_null_char
        res = c_curl_easy_setopt_ptr(handle%handle, CURLOPT_USERAGENT, &
                                     c_loc(c_user_agent))
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "user agent set successfully"
        else
            write(error%message, '(A,I0)') &
                "failed to set user agent, error: ", res
        end if
    end subroutine

    subroutine curl_setopt_timeout(handle, timeout, error)
        type(curl_handle_t), intent(in) :: handle
        integer, intent(in) :: timeout
        type(curl_error_t), intent(out) :: error
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        res = c_curl_easy_setopt_long(handle%handle, CURLOPT_TIMEOUT, &
                                      int(timeout, c_long))
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "timeout set successfully"
        else
            write(error%message, '(A,I0)') "failed to set timeout, error: ", res
        end if
    end subroutine

    subroutine curl_setopt_followlocation(handle, follow, error)
        type(curl_handle_t), intent(in) :: handle
        logical, intent(in) :: follow
        type(curl_error_t), intent(out) :: error
        integer(c_int) :: res
        integer(c_long) :: follow_val

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        follow_val = 0_c_long
        if (follow) follow_val = 1_c_long

        res = c_curl_easy_setopt_long(handle%handle, CURLOPT_FOLLOWLOCATION, &
                                      follow_val)
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "follow location set successfully"
        else
            write(error%message, '(A,I0)') &
                "failed to set follow location, error: ", res
        end if
    end subroutine

    subroutine curl_setopt_ssl_verifypeer(handle, verify, error)
        type(curl_handle_t), intent(in) :: handle
        logical, intent(in) :: verify
        type(curl_error_t), intent(out) :: error
        integer(c_int) :: res
        integer(c_long) :: verify_val

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        verify_val = 0_c_long
        if (verify) verify_val = 1_c_long

        res = c_curl_easy_setopt_long(handle%handle, CURLOPT_SSL_VERIFYPEER, &
                                      verify_val)
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "SSL verify peer set successfully"
        else
            write(error%message, '(A,I0)') &
                "failed to set SSL verify peer, error: ", res
        end if
    end subroutine

    subroutine curl_setopt_httpheader(handle, headers_ptr, error)
        type(curl_handle_t), intent(in) :: handle
        type(c_ptr), intent(in) :: headers_ptr
        type(curl_error_t), intent(out) :: error
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            return
        end if

        res = c_curl_easy_setopt_ptr(handle%handle, CURLOPT_HTTPHEADER, &
                                     headers_ptr)
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            error%message = "HTTP headers set successfully"
        else
            write(error%message, '(A,I0)') &
                "failed to set HTTP headers, error: ", res
        end if
    end subroutine

    subroutine curl_getinfo_response_code(handle, response_code, error)
        type(curl_handle_t), intent(in) :: handle
        integer, intent(out) :: response_code
        type(curl_error_t), intent(out) :: error
        integer(c_long) :: code_long
        integer(c_int) :: res

        if (.not. c_associated(handle%handle)) then
            error%code = CURLE_FAILED_INIT
            error%message = "curl handle not initialized"
            error%success = .false.
            response_code = 0
            return
        end if

        res = c_curl_easy_getinfo_long(handle%handle, CURLINFO_RESPONSE_CODE, &
                                       code_long)
        
        error%code = res
        error%success = (res == CURLE_OK)
        if (res == CURLE_OK) then
            response_code = int(code_long)
            error%message = "response code retrieved successfully"
        else
            response_code = 0
            write(error%message, '(A,I0)') &
                "failed to get response code, error: ", res
        end if
    end subroutine

    ! C callback function implementation for capturing HTTP response data
    function writefunction_callback(contents, size, nmemb, userdata) &
            result(written) bind(c)
        type(c_ptr), value :: contents
        integer(c_size_t), value :: size, nmemb
        type(c_ptr), value :: userdata
        integer(c_size_t) :: written
        
        type(response_buffer_t), pointer :: buffer
        character(kind=c_char), pointer :: char_data(:)
        character(len=:), allocatable :: new_data
        integer :: realsize, i

        realsize = int(size * nmemb)
        written = int(realsize, c_size_t)

        if (.not. c_associated(userdata)) return

        call c_f_pointer(userdata, buffer)
        call c_f_pointer(contents, char_data, [realsize])

        ! Convert C character array to Fortran string
        allocate(character(realsize) :: new_data)
        do i = 1, realsize
            new_data(i:i) = char_data(i)
        end do

        ! Append to existing buffer
        if (allocated(buffer%data)) then
            buffer%data = buffer%data // new_data
        else
            buffer%data = new_data
        end if

        buffer%size = buffer%size + realsize
    end function

end module puby_curl