! The Yasso15 core code -- 24.6.2015
! This improved version contains possibility to compute steady state carbon directly
! which is faster, should be numerically more stable and is more elegant
! This code is an improved version of the old Yasso07 code by M. Tuomi
! - Marko Järvenpää
! Compile with -Wconversion -fdefault-real-8

MODULE yasso
IMPLICIT NONE
CONTAINS
SUBROUTINE mod5c(theta,time,climate,init,b,d,leac,xt,steadystate_pred)
IMPLICIT NONE
    !********************************************* &
    ! GENERAL DESCRIPTION FOR ALL THE MEASUREMENTS
    !********************************************* &
    ! returns the model prediction xt for the given parameters
    ! 1-16 matrix A entries: 4*alpha, 12*p
    ! 17-21 Leaching parameters: w1,...,w5 IGNORED IN THIS FUNCTION
    ! 22-23 Temperature-dependence parameters for AWE fractions: beta_1, beta_2
    ! 24-25 Temperature-dependence parameters for N fraction: beta_N1, beta_N2
    ! 26-27 Temperature-dependence parameters for H fraction: beta_H1, beta_H2
    ! 28-30 Precipitation-dependence parameters for AWE, N and H fraction: gamma, gamma_N, gamma_H
    ! 31-32 Humus decomposition parameters: p_H, alpha_H (Note the order!)
    ! 33-35 Woody parameters: theta_1, theta_2, r

    REAL,DIMENSION(35),INTENT(IN) :: theta ! parameters
    REAL,INTENT(IN) :: time,d,leac ! time,size,leaching
    REAL,DIMENSION(3),INTENT(IN) :: climate ! climatic conditions
    REAL,DIMENSION(5),INTENT(IN) :: init ! initial state
    REAL,DIMENSION(5),INTENT(IN) :: b ! infall
    REAL,DIMENSION(5),INTENT(OUT) :: xt ! the result i.e. x(t)
    LOGICAL,OPTIONAL,INTENT(IN) :: steadystate_pred ! set to true if ignore 'time' and compute solution 
    ! in steady-state conditions (which sould give equal solution as if time is set large enough)
    REAL,DIMENSION(5,5) :: A,At,mexpAt
    INTEGER :: i
    REAL,PARAMETER :: pi = 3.141592653589793
    REAL :: tem,temN,temH,size_dep
    REAL,DIMENSION(5) :: te
    REAL,DIMENSION(5) :: z1,z2
    REAL,PARAMETER :: tol = 1E-12
    LOGICAL :: ss_pred = .FALSE.

	IF(PRESENT(steadystate_pred)) THEN
        ss_pred = steadystate_pred
    ENDIF

    !#########################################################################
    ! Compute the coefficient matrix A for the differential equation

    ! temperature annual cycle approximation
    te(1) = climate(1)+4*climate(3)*(1/SQRT(2.0)-1)/pi
    te(2) = climate(1)-4*climate(3)/SQRT(2.0)/pi
    te(3) = climate(1)+4*climate(3)*(1-1/SQRT(2.0))/pi
    te(4) = climate(1)+4*climate(3)/SQRT(2.0)/pi

    tem = 0.0
    temN = 0.0
    temH = 0.0
    DO i = 1,4 ! Average temperature dependence
        tem = tem+EXP(theta(22)*te(i)+theta(23)*te(i)**2.0)/4.0 ! Gaussian
        temN = temN+EXP(theta(24)*te(i)+theta(25)*te(i)**2.0)/4.0
        temH = temH+EXP(theta(26)*te(i)+theta(27)*te(i)**2.0)/4.0
    END DO

    ! Precipitation dependence
    tem = tem*(1.0-EXP(theta(28)*climate(2)/1000.0))
    temN = temN*(1.0-EXP(theta(29)*climate(2)/1000.0))
    temH = temH*(1.0-EXP(theta(30)*climate(2)/1000.0))

    ! Size class dependence -- no effect if d == 0.0
    size_dep = MIN(1.0,(1.0+theta(33)*d+theta(34)*d**2.0)**(-ABS(theta(35))))

    ! check rare case where no decomposition happens for some compartments 
    ! (basically, if no rain)
    IF (tem <= tol) THEN
        xt = init + b*time
        return
    END IF

    ! Calculating matrix A (will work ok despite the sign of alphas)
    DO i = 1,3
        A(i,i) = -ABS(theta(i))*tem*size_dep
    END DO
    A(4,4) = -ABS(theta(4))*temN*size_dep
    
    A(1,2) = theta(5)*ABS(A(2,2))
    A(1,3) = theta(6)*ABS(A(3,3))
    A(1,4) = theta(7)*ABS(A(4,4))
    A(1,5) = 0.0 ! no mass flows from H -> AWEN
    A(2,1) = theta(8)*ABS(A(1,1))
    A(2,3) = theta(9)*ABS(A(3,3))
    A(2,4) = theta(10)*ABS(A(4,4))
    A(2,5) = 0.0
    A(3,1) = theta(11)*ABS(A(1,1))
    A(3,2) = theta(12)*ABS(A(2,2))
    A(3,4) = theta(13)*ABS(A(4,4))
    A(3,5) = 0.0
    A(4,1) = theta(14)*ABS(A(1,1))
    A(4,2) = theta(15)*ABS(A(2,2))
    A(4,3) = theta(16)*ABS(A(3,3))
    A(4,5) = 0.0
    A(5,5) = -ABS(theta(32))*temH ! no size effect in humus
    DO i = 1,4
        A(5,i) = theta(31)*ABS(A(i,i)) ! mass flows AWEN -> H (size effect is present here)
    END DO

    ! Leaching (no leaching for humus)
    DO i = 1,4
        A(i,i) = A(i,i)+leac*climate(2)/1000.0
    END DO

    !#########################################################################
    ! Solve the differential equation x'(t) = A(theta)*x(t) + b, x(0) = init

	IF(ss_pred) THEN
		! Solve DE directly in steady state conditions (time = infinity)
		! using the formula 0 = x'(t) = A*x + b => x = -A^-1*b
		CALL solve(-A, b, xt)
	ELSE
		! Solve DE in given time
		z1 = MATMUL(A,init) + b
		At = A*time !At = A*t
		CALL matrixexp(At,mexpAt)
		z2 = MATMUL(mexpAt,z1) - b
		CALL solve(A,z2,xt) ! now it can be assumed A is non-singular
    ENDIF

    END SUBROUTINE mod5c

    !#########################################################################
    ! Functions for solving the diff. equation, adapted for the Yasso case
    SUBROUTINE matrixexp(A,B)
        IMPLICIT NONE
        ! Approximated matrix exponential using Taylor series with scaling & squaring
        ! Accurate enough for the Yasso case
        INTEGER,PARAMETER :: n = 5
        REAL,DIMENSION(n,n),INTENT(IN) :: A
        REAL,DIMENSION(n,n),INTENT(OUT) :: B
        REAL,DIMENSION(n,n) :: C,D
        REAL :: p,normiter
        INTEGER :: i,q,j
        q = 10 ! #terms in Taylor
        B = 0.0
        DO i = 1,n
            B(i,i) = 1.0
        END DO
        normiter = 2.0 ! Amount of scaling & squaring
        j = 1
        CALL matrixnorm(A, p)
        DO
            IF (p<normiter) THEN
                EXIT
            END IF
            normiter = normiter*2.0
            j = j+1
        END DO
        !write(*,*) normiter
        C = A/normiter ! scale
        B = B+C
        D = C
        DO i = 2,q ! compute Taylor expansion
            D = MATMUL(C,D)/REAL(i)
            B = B+D
        END DO
        DO i = 1,j ! square
            B = MATMUL(B,B)
        END DO
    END SUBROUTINE matrixexp

    SUBROUTINE matrixnorm(A,B)
        !returns elementwise (i.e. Frobenius) norm of a square matrix
        IMPLICIT NONE
        INTEGER,PARAMETER :: n = 5
        REAL,DIMENSION(n,n),INTENT(IN) :: A
        REAL,INTENT(OUT) :: b
        INTEGER :: i
        b = 0.0
        DO i = 1,n
            b = b+SUM(A(:,i)**2.0)
        END DO
        b = SQRT(b)
    END SUBROUTINE matrixnorm


    SUBROUTINE solve(A, b, x)
        ! Solve linear system A*x = b
        IMPLICIT NONE
        INTEGER,PARAMETER :: n = 5
        REAL,DIMENSION(n,n),INTENT(IN) :: A
        REAL,DIMENSION(n),INTENT(IN) :: b
        REAL,DIMENSION(n),INTENT(OUT) :: x
        REAL,DIMENSION(n,n) :: U
        REAL,DIMENSION(n) :: c
        INTEGER :: i

        ! transform the problem to upper diagonal form
        CALL pgauss(A, b, U, c)

        ! solve U*x = c via back substitution
        x(n) = c(n)/U(n,n)
        DO i = n-1,1,-1
            x(i) = (c(i) - DOT_PRODUCT(U(i,i+1:n),x(i+1:n)))/U(i,i)
        END DO
    END SUBROUTINE solve

    SUBROUTINE pgauss(A, b, U, c)
        ! Transform the lin. system to upper diagonal form using gaussian elimination
        ! with pivoting
        IMPLICIT NONE
        INTEGER,PARAMETER :: n = 5
        REAL,DIMENSION(n,n),INTENT(IN) :: A
        REAL,DIMENSION(n),INTENT(IN) :: b
        REAL,DIMENSION(n,n),INTENT(OUT) :: U
        REAL,DIMENSION(n),INTENT(OUT) :: c
        INTEGER :: k, j
        REAL,PARAMETER :: tol = 1E-12

        U = A
        c = b
        DO k = 1,n-1
            CALL pivot(U,c,k) ! do pivoting (though may not be necessary in our case)
            IF (ABS(U(k,k)) <= tol) THEN
                write(*,*) 'Warning!!! Matrix is singular to working precision!'
            END IF
            U(k+1:n,k) = U(k+1:n,k)/U(k,k)
            DO j = k+1,n
                U(j,k+1:n) = U(j,k+1:n) - U(j,k)*U(k,k+1:n)
            END DO
            c(k+1:n) = c(k+1:n) - c(k)*U(k+1:n,k)
        END DO
    END SUBROUTINE pgauss

    SUBROUTINE pivot(A, b, k)
        ! perform pivoting to matrix A and vector b at row k
        IMPLICIT NONE
        INTEGER,PARAMETER :: n = 5
        REAL,DIMENSION(n,n),INTENT(INOUT) :: A
        REAL,DIMENSION(n),INTENT(INOUT) :: b
        INTEGER,INTENT(IN) :: k
        INTEGER :: q, pk

        !write(*,*) 'Pivot elements are: ', A(k:n,k)
        q = MAXLOC(ABS(A(k:n,k)),1)
        !write(*,*) q
        IF (q > 1) THEN
            pk = k-1+q
            A(k:pk:pk-k,:) = A(pk:k:k-pk,:)
            b(k:pk:pk-k) = b(pk:k:k-pk)
        END IF
        !write(*,*) 'Pivot elements are: ', A(k:n,k)
    END SUBROUTINE pivot
END MODULE yasso







