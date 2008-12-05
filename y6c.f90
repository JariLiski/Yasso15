  FUNCTION mod6c(a,t,cl,k,x,init,cc,inf) RESULT(z1) !components separately      
    !*******************************************                                
    ! WOODY LITTER INCLUDED, LITTERBAG OUTPUTS                                  
    !*******************************************                                
    !returns the model prediction for given parameters                          
    ! 1-16 matrix A entries: 4*k, 12*p                                          
    !17-25 T-dependence parameters: b1, b2, -, -, -, -, -, -, -                 
    !26-34 P-dependence parameters: g1, -, -, -, -, -, -, -, -                  
    !35-38 Humus parametens: kH, pH, -, -                                       
    !39-42 Woody parameters: kW, -, -, -                                        
    !43-44 Other system parameters: S, -                                        
    REAL(KIND=pres),DIMENSION(44),INTENT(IN) :: a !parameters                   
    REAL(KIND=pres),INTENT(IN) :: t,x !time, woody size                         
    REAL(KIND=pres),DIMENSION(6,6) :: m,m2                                      
    INTEGER :: l,i                                                              
    REAL(KIND=pres),DIMENSION(2),INTENT(IN) :: cl !climatic conditionsTm, Pa
    INTEGER,INTENT(IN) :: k                                                     
    REAL(KIND=pres),DIMENSION(6),INTENT(IN) :: init                             
    REAL(KIND=pres) :: h,tem                                                    
    REAL(KIND=pres),DIMENSION(4) :: te                                          
    REAL(KIND=pres),DIMENSION(6),INTENT(IN) :: inf,cc !infall                   
    REAL(KIND=pres),DIMENSION(6) :: z1,z2                                       
    tem=EXP(a(17)*cl(1)+a(18)*cl(1)**2.0)
    tem=tem*(1.0-EXP(a(26)*cl(2)/1000))          
    !Calculating matrix M, normal                                               
    IF(k==2)THEN !woody litter
      m(1,1)=a(39)*tem*x**(a(41))                                               
      m(1,2)=cc(2)*ABS(m(1,1))/SUM(cc(2:5))*a(40) !mass flows to fast           
      m(1,3)=cc(3)*ABS(m(1,1))/SUM(cc(2:5))*a(40) !determined by chemical compo$
      m(1,4)=cc(4)*ABS(m(1,1))/SUM(cc(2:5))*a(40)                               
      m(1,5)=cc(5)*ABS(m(1,1))/SUM(cc(2:5))*a(40)                               
    END IF                                                                      
    m(2,2)=a(1)*tem                                                             
    m(3,3)=a(2)*tem                                                             
    m(4,4)=a(3)*tem                                                             
    m(5,5)=a(4)*tem                                                             
    m(3,2)=a(5)*ABS(m(3,3))                                                     
    m(4,2)=a(6)*ABS(m(2,2))                                                     
    m(5,2)=a(7)*ABS(m(5,5))                                                     
    m(2,3)=a(8)*ABS(m(2,2))                                                     
    m(4,3)=a(9)*ABS(m(4,4))                                                     
    m(5,3)=a(10)*ABS(m(5,5))                                                    
    m(2,4)=a(11)*ABS(m(2,2))                                                    
    m(3,4)=a(12)*ABS(m(3,3))                                                    
    m(5,4)=a(13)*ABS(m(5,5))                                                    
    m(2,5)=a(14)*ABS(m(2,2))                                                    
    m(3,5)=a(15)*ABS(m(3,3))                                                    
    m(4,5)=a(16)*ABS(m(4,4))                                                    
    m(6,6)=a(35)*tem                                                            
    DO i=2,5                                                                    
      m(i,5)=a(36)*ABS(m(i,i)) !mass flows EWAN -> H                            
    END DO                                                                      
    DO i=1,6                                                                    
      z1(i)=DOT_PRODUCT(m(:,i),init)+inf(i)                                     
    END DO                                                                      
    m2=matrixexp(m*t,6)                                                         
    DO i=1,6                                                                    
      z2(i)=DOT_PRODUCT(m2(:,i),z1)-inf(i)                                      
    END DO                                                                      
    m=inverse(m,6)                                                              
    DO i=1,6                                                                    
      z1(i)=DOT_PRODUCT(m(:,i),z2)                         
    END DO                                                                      
  END FUNCTION mod6c                                                            
                            





  FUNCTION matrixexp(a,r) RESULT(b)                                             
    !returns approximated matrix exponential                                    
    !Taylor (Bade to be written) approximation..another algorithm perhaps?      
    REAL(KIND=pres),DIMENSION(:,:),INTENT(IN) :: a                              
    INTEGER,INTENT(IN) :: r                                                     
    REAL(KIND=pres),DIMENSION(r,r) :: b,c,d                                     
    REAL(KIND=pres) :: p                                                        
    INTEGER :: i,q,m,j                                                          
    q=10                                                                        
    b=0.0                                                                       
    DO i=1,r                                                                    
      b(i,i)=1.0                                                                
    END DO                                                                      
    m=2                                                                         
    j=1                                                                         
    p=matrix2norm(a)                                                            
    DO                                                                          
      IF(p<REAL(m))EXIT                                                         
      m=m*2                                                                     
      j=j+1                                                                     
    END DO                                                                      
    c=a/REAL(m)                                                                 
    b=b+c                                                                       
    d=c                                                                         
    DO i=2,q                                                                    
      d=MATMUL(c,d)/REAL(i)                                                     
      b=b+d                                                                     
    END DO                                                                      
    DO i=1,j                                                                    
      b=MATMUL(b,b)                                                             
    END DO                                                                      
  END FUNCTION matrixexp 




  FUNCTION matrix2norm(a) RESULT(b)                                             
    !returns matrix 2-norm with cartesian vector x, ||x|| = 1                   
    !square matrix input (generalize if necessary)                              
    REAL(KIND=pres),DIMENSION(:,:) :: a                                         
    REAL(KIND=pres) :: b,c                                                      
    INTEGER :: n,i                                                              
    n=SIZE(a(1,:))                                                              
    b=0.0                                                                       
    DO i=1,n                                                                    
      b=b+SUM(a(:,i))**2.0                                                      
    END DO                                                                      
    b=SQRT(b)                                                                   
  END FUNCTION matrix2norm            


  FUNCTION inverse(a,s) RESULT(b)                                               
    !returns an inverse of matrix a (column elimination strategy)               
    !input has to be a square matrix, otherwise erroneous                       
    INTEGER,INTENT(IN) :: s                                                     
    REAL(KIND=pres),DIMENSION(:,:),INTENT(IN)  :: a                             
    REAL(KIND=pres),DIMENSION(s,s) :: b,c                                       
    INTEGER :: n,m,i,j                                                          
    n=SIZE(a(1,:))                                                              
    m=SIZE(a(:,1))                                                              
    IF(m/=n) THEN                                                               
      WRITE(*,*) "Does not compute."                                            
      WRITE(*,*) "No square matrix input."                                      
      WRITE(*,*) "Error in function: inverse"                                   
    ELSE                                                                        
!      ALLOCATE(b(n,n),c(n,n))                                                  
      c=a                                                                       
      b=0.0                                                                     
      DO i=1,n !setting b a unit matrix                                         
        b(i,i)=1.0                                                              
      END DO                                                                    
      DO i=1,n                                                                  
      !what if diagonal values are zeros?                                       
        IF(c(i,i)==0.0)THEN!case of singuar matrix, is it?                      
          b(i,:)=0.0                                                            
          c(i,:)=0.0                                                            
          b(:,i)=0.0                                                            
          c(:,i)=0.0                                                            
          !        b(i,i)=1.0                                                   
          !        c(i,i)=1.0                                                   
        ELSE                                                                    
          b(i,:)=b(i,:)/c(i,i)                                                  
          c(i,:)=c(i,:)/c(i,i)                                                  
        END IF                                                                  
        DO j=1,i-1                                                              
          b(j,:)=b(j,:)-b(i,:)*c(j,i)                                           
          c(j,:)=c(j,:)-c(i,:)*c(j,i)                                           
        END DO                                                                  
        DO j=i+1,n                                                              
          b(j,:)=b(j,:)-b(i,:)*c(j,i)                                           
          c(j,:)=c(j,:)-c(i,:)*c(j,i)                                           
        END DO                                                                  
      END DO        
      IF(c(n,n)==0.0)THEN                                                       
        b(n,:)=0.0                                                              
        b(:,n)=0.0                                                              
        !      b(n,n)=1.0                                                       
      ELSE                                                                      
        b(n,:)=b(n,:)/c(n,n)                                                    
      END IF                                                                    
    !now, b is supposed to be the requested inverse                             
    END IF                                                                      
  END FUNCTION inverse    
