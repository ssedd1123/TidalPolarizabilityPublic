C     -*- fortran -*-
C     This file is autogenerated with f2py (version:2)
C     It contains Fortran 77 wrappers to fortran functions.

      subroutine f2pywrapCSEVAL (CSEVALf2pywrap, N, U, IDERIV, X, 
     &Y, B, C, D)
      external CSEVAL
      integer N
      double precision U
      integer IDERIV
      double precision X(N)
      double precision Y(N)
      double precision B(N)
      double precision C(N)
      double precision D(N)
      double precision CSEVALf2pywrap, CSEVAL
      CSEVALf2pywrap = CSEVAL(N, U, IDERIV, X, Y, B, C, D)
      end
