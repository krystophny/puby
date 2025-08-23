module puby
  implicit none
  private

  public :: say_hello
contains
  subroutine say_hello
    print *, "Hello, puby!"
  end subroutine say_hello
end module puby
