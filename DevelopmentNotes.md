#Notes about issues met when developing.

# Snow Leopard #

wxPython is used for the UI widgets in Yasso07ui, and it has only support for 32 bit Python. EPD distribution is 32 bit, but the y07 library needs to be compiled as 32 as well. First create a symbolic link for the f2py script in EPD and then::

```
  export CFLAGS="-arch i386"
  export FFLAGS="-m32"
  export LDFLAGS="-Wall -undefined dynamic_lookup -bundle -arch i386"
  f2py -c --fcompiler=gnu95 -m y07 y07_subroutine.f90
```