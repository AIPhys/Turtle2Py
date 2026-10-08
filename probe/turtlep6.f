      PROGRAM TURTLE
C     +------------------------------------------------------------------------+
C     I MAIN PROGRAM                                                           I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC4/  RAYMAX(6), PBEAM, P0, NORAYS
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC6/  NHISTS, NHIST, LIMNO
      COMMON /BLOC7/  MTYPE(100), NENTRY(100), NCOOR(100), INTVLS(100),
     A                BEGIN(100), END(100), STEP(100), ZHIST(100)
      COMMON /BLOC8/  MTABLE(10000)
      COMMON /BLOC9/  L, H, N, BDB
      REAL            L, N
      COMMON /BLOC10/ APB(2), LAYL, LAYX, RAB1, RAB2, FACE
      REAL            LAYL, LAYX
      COMMON /BLOC11/ QAP(3), ELLIPS, HYPER
      LOGICAL         ELLIPS, HYPER
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
        COMMON /BLOC14/ MMAX, GTOP, DB(20), COSM(20), SINM(20)
      COMMON /BLOC15/ LL, KH2, KV2, KH, KV, KHL, KVL, RAY2(6),
     A                RH(4), RV(4)
      REAL LL, KH2, KV2, KH, KV, KHL, KVL
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      COMMON /BLOC17/ IP, IC(4), IS(4)
      COMMON /BLOC18/ LOSS, NBLK(10), KFLG(10),
     A                XSTRT(10), XEND(10), LTHX(10), XBIN(10), NUNX(10),
     A                YSTRT(10), YEND(10), LTHY(10), YBIN(10), NUNY(10)
      COMMON /BLOC41/ LW, IMAGE(20), FLUSH, INDIC, NTYPE, LABLE, LENGTH,
     A                NWORD, NVARY, DATUM(30), VARY(30)
      INTEGER VARY, TEXT(30)
      LOGICAL FLUSH
      EQUIVALENCE (TEXT, DATUM)
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM
      INTEGER CARD
      LOGICAL EMPTY
      COMMON /BLC12A/ YMOM(100), YMOM2(100), CORR(100)
      CHARACTER*40 INPFIL, OUTFIL
C
      WRITE (*,2001)
 2001 FORMAT('  INPUT FILE NAME? '$)
      READ  (*,2002) INPFIL
 2002 FORMAT(A40)
      WRITE (*,2003)
 2003 FORMAT(' OUTPUT FILE NAME? '$)
      READ  (*,2002) OUTFIL
C
      OPEN (NIN ,FILE=INPFIL,STATUS='OLD')
      OPEN (NOUT,FILE=OUTFIL,STATUS='UNKNOWN')
C
      CALL INITZE
      CALL SETUP
      CALL HEDING
      CALL ZERO
      LEFT = 10000 - LIMNO
      WRITE (NOUT, 100) LEFT
  100 FORMAT(/'0THE REST SPACE OF HIST STORAGE',I6,' CELLS')
C
      CALL RAYRUN
C
      CALL OHIST
      CALL APLIM
C
      CLOSE (NIN)
      CLOSE (NOUT)
      STOP
      END
C
      BLOCK DATA DATUM
C     +------------------------------------------------------------------------+
C     I BLOCK DATA                                                             I
C     +------------------------------------------------------------------------+
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
C
      DATA UNIT / 0.01, 0.001, 0.01, 0.001, 0.01, 0.01, 0.01745329,
     A            1.0, 1.0, 1.0, 1.0 /
      DATA NAME / 4HCM  , 4HMR  , 4HCM  , 4HMR  , 4HCM  , 4HPC  ,
     A            4HDEG , 4HM   , 4HKG  , 4HGEVA, 4HGEVC /
      DATA NOM  / 4H   X, 4H  X', 4H   Y, 4H  Y', 4HJUNK, 4HDP/P,
     A            4HJUNK, 4H   Z, 4HJUNK, 4HJUNK, 4H   P /
      DATA NOM1 / 4H   R, 4H  XI, 4H PSI, 4HZETA /
      DATA TABLE / 1H0, 1H1, 1H2, 1H3, 1H4, 1H5, 1H6, 1H7, 1H8, 1H9,
     A             1HA, 1HB, 1HC, 1HD, 1HE, 1HF, 1HG, 1HH, 1HI, 1HJ,
     B             1HK, 1HL, 1HM, 1HN, 1HO, 1HP, 1HQ, 1HR, 1HS, 1HT,
     C             1HU, 1HV, 1HW, 1HX, 1HY, 1HZ /
      DATA PLUS  / 1H+, 1H? /
      DATA MINUS / 1H- /
      DATA BLANK / 1H  /
      DATA PERIOD/ 1H. /
      DATA SEMI  / 1H;, 1H,, 1H*, 1H&, 1H! /
      DATA QUOTE / 1H', 1H#, 1H/, 1H=, 1H&, 1H^ /
      DATA PAR1  / 1H(, 1H: /
      DATA PAR2  / 1H), 1H< /
      DATA NIN  / 5 /
      DATA NOUT / 6 /
      DATA NOL  / 7 /
      END
C
      SUBROUTINE APLIM
C     +------------------------------------------------------------------------+
C     I PRINTS A TABLE OF PARTICLES HITTING APERTURES                          I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      INTEGER TYPE(3), KSTOP(3)
      DATA TYPE / 4HBEND, 4HQUAD, 4HSLIT /
C
      LAST = 1
      IF(DKFLAG) LAST = 3
      WRITE (NOUT, 900) (KPART(J), J = 1, LAST)
      DO 10 J = 1, LAST
   10 KSTOP(J) = 0
      IAP = 0
      I = 1
      ZC = 0.0
      FZ = 1.0 / UNIT(8)
   20 NTYPE = IDATA(I)
      IF(NTYPE .LE. 0 .OR. NTYPE .GT. 21) GO TO 90
      GO TO (90, 90, 50, 30, 30, 30, 90, 90, 60, 90, 50, 90, 90, 90,
     A       90, 90, 90, 50, 50, 90, 90), NTYPE
   30 IAP = IAP + 1
      IF(ISTOP(1,IAP) + ISTOP(2,IAP) + ISTOP(3,IAP) .EQ. 0) GO TO 50
      DO 40 J = 1, LAST
   40 KSTOP(J) = KSTOP(J) + ISTOP(J,IAP)
      Z = ZC * FZ
      WRITE (NOUT, 910) Z, NAME(8), TYPE(NTYPE-3),
     A                  (ISTOP(J,IAP), J = 1, LAST)
   50 IF(NTYPE .EQ. 6) GO TO 90
      ZC = ZC + DATA(I+1)
      GO TO 90
   60 CALL REPEAT
   90 I = I + NU(NTYPE)
      IF(I .LE. I1) GO TO 20
      WRITE (NOUT, 920) (KSTOP(J), J = 1, LAST)
      RETURN
C
  900 FORMAT(1H1/'0SUMMARY OF PARTICLES STOPPED BY APERTURES'
     A       /1X,41(1H=)/1H0,10X,7HPOSITON,8X,4HTYPE,3(8X,A4))
  910 FORMAT(1X,F15.3,1X,A4,5X,A4,3I12)
  920 FORMAT(' TOTAL',24X,3I12)
      END
C
      SUBROUTINE DECAY
C     +------------------------------------------------------------------------+
C     I TREATS DECAY CINEMATICS                                                I
C     +------------------------------------------------------------------------+
      COMMON /BLOC4/  RAYMAX(6), PBEAM, P0, NORAYS
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
C
      COST = 2.0 * RANF(CT) - 1.0
      SINT = SQRT (1.0 - COST ** 2)
C-----
      FPC = P * (COST + FC) / MASS
      FPN = P * (COST + FN) / MASS
      THETAN = SINT / FPN
      PN = PSTAR * FPN
C-----
	EC = PSTAR * (FC*SQRT(P*P + MASS*MASS) + P*COST) / MASS
	PC = SQRT (EC*EC - MASSC*MASSC)
	THETAC = SINT * PSTAR/PC
C-----
      PHI = 6.2831853 * RANF(PH)
      COSPHI = COS(PHI)
      SINPHI = SIN(PHI)
      RAYC(1) = RAY(1)
      RAYC(2) = RAY(2) + COSPHI * THETAC
      RAYC(3) = RAY(3)
      RAYC(4) = RAY(4) + SINPHI * THETAC
      RAYC(5) = RAY(5)
      RAYC(6) = (PC - P0) / P0
      RAYN(1) = RAY(1)
      RAYN(2) = RAY(2) - COSPHI * THETAN
      RAYN(3) = RAY(3)
      RAYN(4) = RAY(4) - SINPHI * THETAN
      RAYN(5) = RAY(5)
      RAYN(6) = (PN - P0) / P0
      RETURN
      END
C
      SUBROUTINE DECAYP
C     +------------------------------------------------------------------------+
C     I PREPARES DATA FOR 'DECAY'                                              I
C     +------------------------------------------------------------------------+
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC41/ LW, IMAGE(20), FLUSH, INDIC, NTYPE, LABLE, LENGTH,
     A                NWORD, NVARY, DATUM(30), VARY(30)
      INTEGER VARY, TEXT(30)
      LOGICAL FLUSH
      EQUIVALENCE (TEXT, DATUM)
C
      MASS = DATUM(2) * UNIT(11)
      MASSC = DATUM(3) * UNIT(11)
      MASSN = DATUM(4) * UNIT(11)
      FLD = 0.299 * DATUM(5) / MASS
      PSTAR=SQRT((MASS+MASSC+MASSN)*(MASS+MASSC-MASSN)*
     A           (MASS-MASSC+MASSN)*(MASS-MASSC-MASSN))/(2.*MASS)
      FC=SQRT(PSTAR**2+MASSC**2)/PSTAR
      FN=SQRT(PSTAR**2+MASSN**2)/PSTAR
      RETURN
      END
C
      SUBROUTINE DECAYZ (ZD)
C     +------------------------------------------------------------------------+
C     I GENERATES RANDOM DECAY POSISTION                                       I
C     +------------------------------------------------------------------------+
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      REAL LD
C
      X=RANF(XR)
      LD = FLD * P
      IF(ZMAX.NE.0.) X=1.-X*(1.-EXP(-ZMAX/LD))
      ZD = - LD * ALOG (X)
      RETURN
      END
C
      SUBROUTINE EMIT_MY
C     +------------------------------------------------------------------------+
C     I GENERATES A RANDOM INITIAL RAY                                         I
C     +------------------------------------------------------------------------+
      COMMON /BLOC4/  RAYMAX(6), PBEAM, P0, NORAYS
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      dimension xpr(50), fun(50)
      data key /0/
c
	num_max = 50

      rn_sig = 3.
c
c---- Horizontal


      if (key .eq. 0) then
      xa = raymax(1)
      dx = xa / float(num_max)
      sum = 0.
      do 10 i = 1, num_max
      x = dx*float(i) - 0.5*dx

	xaa = 0.001
	h2 = 0.1


      xpr(i) = (1.-(x/xa)**0.25)**3.0


   10 sum = sum + xpr(i)
      s = 0.
      do 20 i = 1, num_max
      s = s + xpr(i)
   20 fun(i) = s / sum
      key = 1
      endif
c
      dx = raymax(1) / float(num_max)
      fi = ranf(fi)

      XR6_temp = 6.2831853 * RANF(R6)

	do 30 i = 1, num_max
      if (fi .lt. fun(i)) go to 31
   30 continue
      i = num_max
   31 ray(1) = dx*(float(i)-ranf(x))



	RAY(2) = 0.

c---- Scattering (prenebregaem izmeneniem coordinaty)

   38 XR1 = SQRT(-2.*ALOG(RANF(XR1)))
      XR2 = 6.2831853 * RANF(XR2)
      del_x1 = RAYMAX(2) * XR1 * SIN(XR2)
      RAY(2) = RAY(2) + del_x1
c-----
C
C---- Vertical
c
c---- Maximov
c     eps_  = 30
c     beta  = 25.4
c     alpha = 1.72
c     gamma*beta - alpha**2 = 1
c     corr = - alpha / (gamma*beta)**0.5 = - alpha / (1+alpha**2)**0.5
c     corry = -0.8645
c     gamma = (1+alpha**2)/beta = 0.155842
c     y1_0 = (eps * gamma)**0.5 = 2.162238 mrad
c     yy_0 = eps / y1_0 = (eps / gamma)**0.5 = 13.8745 mm
c     z = - corry * (yy/y1) = -corry * (beta/gamma)**0.5 = 11.037 m

      z_temp = 11.037

      yy_max = 0.001 * 13.8745
      y1_max = 0.001 *  2.1622


      sig_yy = yy_max / 3.
      sig_y1 = y1_max / 3.

   40 XR3 = SQRT(-2.*ALOG(RANF(XR3)))
      XR4 = 6.2831853 * RANF(XR4)
      del_yy = sig_yy * XR3 * COS(XR4)
      del_y1 = sig_y1 * XR3 * SIN(XR4)

      if (abs(del_yy) .GT. yy_max .OR.
     +	abs(del_y1) .GT. y1_max)  go to 40
	ray(3) = del_yy + del_y1 * z_temp
	ray(4) = del_y1

      IF (ABS(RAY(3)) .GT. RAYMAX(3))  GO TO 40

c---- Scattering

   41 XR3 = SQRT(-2.*ALOG(RANF(XR3)))
      XR4 = 6.2831853 * RANF(XR4)
      del_y1 = RAYMAX(4) * XR3 * SIN(XR4)
      RAY(4) = RAY(4) + del_y1

c----
C
      RAY(5) = RAYMAX(5) * (2.0 * RANF(R5) - 1.0)

   50 XR5 = SQRT(-2.*ALOG(RANF(XR5)))
      XR6 = 6.2831853 * RANF(R6)
      RAY(6) = RAYMAX(6) * XR5 * COS(XR6)
      if (abs(RAY(6)) .GT. 2.* RAYMAX(6))  go to 50

      P = PBEAM * (1. + RAY(6))


c----
      RETURN
      END
C
	SUBROUTINE EHIST
C     +------------------------------------------------------------------------+
C     I ENTERS A RAY INTO HISTOGRAMS                                           I
C     +------------------------------------------------------------------------+
      COMMON /BLOC6/  NHISTS, NHIST, LIMNO
      COMMON /BLOC7/  MTYPE(100), NENTRY(100), NCOOR(100), INTVLS(100),
     A                 BEGIN(100), END(100), STEP(100), ZHIST(100)
      COMMON /BLOC8/  MTABLE(10000)
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      LOGICAL SCALX
      COMMON /BLC12A/ YMOM(100), YMOM2(100), CORR(100)
C
      SCALX = .FALSE.
      DO 400 NH = 1, NHISTS
      NFL = NFLAG(NH)
      KFL = KFLAG(NH) + 1
      NAVEL = MTYPE(NH)
      GO TO (100,200,300), NAVEL
C
C     ONE DIMENSIONAL HISTOGRAM
C
  100 IF(NFL .GT. 0 .AND. .NOT. IFLAG(KFL,NFL)) GO TO 400
      IF(.NOT. SET(NH)) GO TO 400
      VAL = VALUE(NH)
      M = NENTRY(NH)
      N = INTVLS(NH)
      XBEG = BEGIN(NH)
      XEND = END(NH)
      DX = STEP(NH)
      CALL HISTO(VAL,M        ,N,XBEG,XEND,DX)
C      XMOM(NH) = XMOM(NH) + VAL
C      XMOM2(NH) = XMOM2(NH) + VAL ** 2
      SM = MTABLE(M+N+2)
      XM = XMOM(NH)
      XMOM(NH) = ((SM-1.)*XM + VAL) / SM
      XMOM2(NH)= (SM-1.)*(SM*XMOM2(NH) + (VAL-XM)**2) / SM**2
      GO TO 400
C
C     X COORDINATE OF TWO DIMENSIONAL HISTOGRAM
C
  200 SCALX = .FALSE.
      IF(NFL .GT. 0 .AND. .NOT. IFLAG(KFL,NFL)) GO TO 400
      IF(.NOT. SET(NH)) GO TO 400
      SCALX = .TRUE.
      A = VALUE(NH)
      NA = INTVLS(NH)
      AMIN = BEGIN(NH)
      AMAX = END(NH)
      DA = STEP(NH)
      GO TO 400
C
C     Y COORDINATE OF TWO DIMENSIONAL HISTOGRAM
C
  300 IF(NFL .GT. 0 .AND. .NOT. IFLAG(KFL,NFL)) GO TO 400
      IF(.NOT. (SET(NH) .AND. SCALX)) GO TO 400
      D = VALUE(NH)
      M = NENTRY(NH)
      ND = INTVLS(NH)
      DMIN = BEGIN(NH)
      DMAX = END(NH)
      DD = STEP(NH)
      CALL ENTMAT (A,D,M,AMIN,AMAX,NA,DA,DMIN,DMAX,ND,DD)
      XMOM(NH) = XMOM(NH) + A
      XMOM2(NH)= XMOM2(NH)+ A * A
      YMOM(NH) = YMOM(NH) + D
      YMOM2(NH)= YMOM2(NH)+ D * D
      CORR(NH) = CORR(NH) + A * D
  400 CONTINUE
      RETURN
      END
C
      SUBROUTINE ENTMAT (A,D,MATRIX,AMIN,AMAX,NA,DA,DMIN,DMAX,ND,DD)
C     +------------------------------------------------------------------------+
C     I ENTERS (X,Y) COORDINATE FOR 2 DIMENSIONAL HISTOGRAMS                   I
C     +------------------------------------------------------------------------+
      COMMON/BLOC8/  MTABL(10000)
C
      MATR=MATRIX-1
      NAA = NA + 1
      NTT = NAA*(ND + 1)
      MTT = NTT + 5
C
C     OVERFLOW OF X COORDINATE
C
      IF (A - AMIN) 5, 10, 10
    5 NRET = 1
      GO TO 35
   10 IF (A - AMAX) 20, 20, 15
   15 NRET = 2
      GO TO 35
C
C     OVERFLOW OF Y COORDINATE
C
   20 IF (D - DMIN) 25, 30, 30
   25 NRET = 3
      GO TO 35
   30 IF (D - DMAX) 40, 40, 32
   32 NRET = 4
C
   35 NOV = NTT + NRET
   36 MTABL(MATR+NOV) = MTABL(MATR+NOV) + 1
      MTABL(MATR+MTT) = MTABL(MATR+MTT) + 1
      RETURN
C
C     ENTRY INTO HISTOGRAM
C
 40   CONTINUE
      IA = (A - AMIN)/DA + 1.0
      ID = (D - DMIN)/DD + 1.0
      MM = (ID - 1) * NAA + IA
      NAT = ID*NAA
      NDT = ND*NAA + IA
 60   MTABL(MATR+MM) =  MTABL( MATR+MM ) + 1
      MTABL(MATR+NTT) = MTABL( MATR+NTT) + 1
      MTABL(MATR+NAT) = MTABL( MATR+NAT) + 1
      MTABL(MATR+NDT) = MTABL( MATR+NDT) + 1
      MTABL(MATR+MTT) = MTABL( MATR+MTT) + 1
 200  RETURN
      END
C
      SUBROUTINE HEDING
C     +------------------------------------------------------------------------+
C     I PRINTS LIST OF HISTOGRAMS DESIRED                                      I
C     +------------------------------------------------------------------------+
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC4/  RAYMAX(6), PBEAM, P0, NORAYS
      COMMON /BLOC6/  NHISTS, NHIST, LIMNO
      COMMON /BLOC7/  MTYPE(100), NENTRY(100), NCOOR(100), INTVLS(100),
     A                BEGIN(100), END(100), STEP(100), ZHIST(100)
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      COMMON /BLOC18/ LOSS, NBLK(10), KFLG(10),
     A                XSTRT(10), XEND(10), LTHX(10), XBIN(10), NUNX(10),
     A                YSTRT(10), YEND(10), LTHY(10), YBIN(10), NUNY(10)
      COMMON /BLOC41/ LW, IMAGE(20), FLUSH, INDIC, NTYPE, LABLE, LENGTH,
     A                NWORD, NVARY, DATUM(30), VARY(30)
      INTEGER VARY, TEXT(30)
      LOGICAL FLUSH
      EQUIVALENCE (TEXT, DATUM)
C
      WRITE (NOUT,9007) NORAYS
 9007 FORMAT(1H1/'0THE FOLLOWING HISTOGRAMS REFER TO',I8,
     A         ' RAYS PASSING THROUGH THE ABOVE BEAM LINE')
      WRITE (NOUT,9008)
 9008 FORMAT(1X,82(1H=))
      KH = 0
      DO 400 K = 1, NHISTS
      NAVEL = MTYPE(K)
      GO TO (100,200,300), NAVEL
C
C     ONE DIMENSIONAL HISTOGRAM
C
  100 KH = KH + 1
      N = NCOOR(K)
      Z = ZHIST(K)/UNIT(8)
      KFL = KFLAG(K) + 1
      NFL = NFLAG(K)
      WRITE (NOUT, 9400) KH
 9400 FORMAT('0HISTOGRAM NO',I3)
      CALL HISCAP (1, N, KFL, Z, NFL)
      GO TO 400
C
C     X COORDINATE FOR TWO DIMENSIONAL HISTOGRAM
C
  200 NA = NCOOR(K)
      ZA = ZHIST(K)/UNIT(8)
      KFLA = KFLAG(K) + 1
      NFLA = NFLAG(K)
      GO TO 400
C
C     Y COORDINATE FOR TWO DIMENSIONAL HISTOGRAM
C
  300 KH = KH + 1
      ND = NCOOR(K)
      ZD = ZHIST(K) /UNIT(8)
      KFLD = KFLAG(K) + 1
      NFLD = NFLAG(K)
      WRITE (NOUT, 9400) KH
      CALL HISCAP (2, NA, KFLA, ZA, NFLA)
      CALL HISCAP (3, ND, KFLD, ZD, NFLD)
  400 CONTINUE
C
C     HISTOGRAMS OF PARTICLES STOPPED
C
      IF(LOSS .EQ. 0) GO TO 710
      DO 700 K = 1, LOSS
      KH = KH + 1
      KFL = KFLG(K) + 1
      WRITE (NOUT, 9500) KH, KPART(KFL)
 9500 FORMAT('0HISTOGRAM NO',I3,' OF ',A4,' LOST')
      N = NUNX(K)
      NA = NUNY(K)
      IF(NA .NE. 0) GO TO 600
      CALL HISCAP (4, N, 0, 0.0, 0)
      GO TO 700
  600 CALL HISCAP (5, N, 0, 0.0, 0)
      CALL HISCAP (6, NA, 0, 0.0, 0)
  700 CONTINUE
  710 IF(.NOT. DKFLAG .OR. ZMAX .EQ. 0.0) RETURN
      ZMAXX = ZMAX / UNIT(8)
      FAC = 1.0 / (1.0 - EXP(-ZMAX / (FLD*PBEAM)))
      WRITE (NOUT, 9700) ZMAXX, NAME(8), FAC
 9700 FORMAT(1H0,84(1H*)/43H * ALL PARENT PARTICLES ARE FORCED TO DECAY,
     A       8H WITHIN ,F10.3,1X,A4,19H FROM THE TARGET. */
     B       56H * THE NUMBER OF DECAYS WILL BE ENHANCED BY A FACTOR OF
     C       ,F8.3,21H (AVERAGE VALUE)    */1X,84(1H*))
      RETURN
      END
C
      SUBROUTINE HISCAP (IOPT, NUN, KFL, ZH, NFL)
C     +------------------------------------------------------------------------+
C     I PRINTS HISTOGRAM CAPTIONS                                              I
C     +------------------------------------------------------------------------+
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      INTEGER LABEL(4,3), FOR, PART(2), BLANK
      DATA   LABEL
     A     / 4HDIST, 4HRIBU, 4HTION, 4H OF ,
     B       4HHORI, 4HZONT, 4HAL A, 4HXIS ,
     C       4HVERT, 4HICAL, 4H AXI, 4HS    /
      DATA FOR, BLANK / 4HFOR , 4H     /
C
      IF(NUN .LE. 11) GO TO 10
      J = NUN - 20
      N1 = NOM1(J)
      N2 = NAME(J)
      IF(J .GT. 2) N2 = NAME(7)
      GO TO 20
   10 N1 = NOM(NUN)
      N2 = NAME(NUN)
   20 PART(1) = BLANK
      PART(2) = BLANK
      IF(.NOT. DKFLAG) GO TO 30
      PART(1) = FOR
      PART(2) = KPART(KFL)
   30 IF(IOPT .GT. 3) GO TO 50
      J = IOPT
      IF(NFL .NE. 0) GO TO 40
      WRITE (NOUT,110) (LABEL(I,J), I=1,4), N1, N2, PART, ZH, NAME(8)
      RETURN
   40 ZFL = ZFLAG(NFL) / UNIT(8)
      WRITE (NOUT,120) (LABEL(I,J), I=1,4), N1, N2, PART, ZH, NAME(8),
     A                  ZFL, NAME(8)
      RETURN
   50 J = IOPT - 3
      WRITE (NOUT, 110) (LABEL(I,J), I=1,4), N1, N2
      RETURN
C
  110 FORMAT(1X,5A4,' IN ',A4,5X,2A4,5X,F12.3,1X,A4,
     A       ' FROM THE TARGET')
  120 FORMAT(1X,5A4,' IN ',A4,5X,2A4,5X,F12.3,1X,A4,
     A       ' FROM THE TARGET, FLAG AT ',F12.3,1X,A4)
      END
C
      SUBROUTINE HISTO (X, NHST, M, A, B, DX)
C     +------------------------------------------------------------------------+
C     I ENTERS X INTO HISTOGRAM ARRAY NHST                                     I
C     +------------------------------------------------------------------------+
      COMMON/BLOC8/  MTABL(10000)

      N=NHST-1
      MTABL(N+M+3) =MTABL(N+M+3) + 1
C
C     OVERFLOW OF HISTOGRAM
C
      IF (X - B) 104, 102, 102
  102 MTABL(N+M+1) = MTABL(N+M+1) + 1
      RETURN
  104 IF (X - A) 106, 108, 108
  106 MTABL(N+M+2) = MTABL(N+M+2) + 1
      RETURN
C
C     FILL IN HISTOGRAM
C
  108 L = (X - A)/DX + 1.00001
      MTABL(N+L) = MTABL(N+L)+ 1
      RETURN
      END
C
      SUBROUTINE HSTUN (NCO, FACT, LEGAL)
C     +------------------------------------------------------------------------+
C     I FINDS CONVERSION FACTOR FOR HISTOGRAM COORDINATE                       I
C     +------------------------------------------------------------------------+
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      LOGICAL LEGAL
C
      LEGAL = .TRUE.
      IF(NCO .GT. 0 .AND. NCO .LE. 6) GO TO 20
      IF(NCO .EQ. 8) GO TO 30
      IF(NCO .EQ. 11) GO TO 30
      IF(NCO .GT. 20 .AND. NCO .LE. 24) GO TO 40
   10 LEGAL = .FALSE.
      WRITE (NOUT, 100)
      RETURN
   20 IF(NCO .EQ. 5) GO TO 10
   30 FACT = UNIT(NCO)
      RETURN
   40 J = NCO - 20
      IF(J .GT. 2) GO TO 50
      FACT = UNIT(J)
      RETURN
   50 FACT = UNIT(7)
      RETURN
C
  100 FORMAT('0THE COORDINATE SPECIFICATION ON THE HISTOGRAM CARD '
     A       'ABOVE HAS NO MEANING TO TURTLE. HISTOGRAM IGNORED.')
      END
C
      REAL FUNCTION HSTVAL (NCO)
C     +------------------------------------------------------------------------+
C     I RETURNS THE VALUE TO BE HISTOGRAMMED                                   I
C     +------------------------------------------------------------------------+
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
C
      IF(NCO .LE.  6) GO TO 10
      IF(NCO .EQ.  8) GO TO 20
      IF(NCO .EQ. 11) GO TO 30
      IF(NCO .GT. 20) GO TO 40
      RETURN
   10 HSTVAL = RAY(NCO)
      RETURN
   20 HSTVAL = Z
      RETURN
   30 HSTVAL = P
      RETURN
   40 IF(NCO .GT. 22) GO TO 50
      J = NCO - 20
      HSTVAL = SQRT (RAY(J)**2 + RAY(J+2)**2)
      RETURN
   50 J = NCO - 22
      HSTVAL = 0.0
      IF(RAY(J+2) .NE. 0.0 .OR. RAY(J) .NE. 0.0)
     A     HSTVAL = ATAN2 (RAY(J+2), RAY(J))
      RETURN
      END
C
      SUBROUTINE LOADX (XSS, NUM)
C     +------------------------------------------------------------------------+
C     I INSERTS X'S INTO ACTUAL HISTOGRAM                                      I
C     +------------------------------------------------------------------------+
      DIMENSION XSS(100)
      DATA X, BLANK / 1HX, 1H  /
C
      NA = MIN0(NUM,100)
      DO 110 J = 1, NA
  110 XSS(J) = X
      IF (NA - 100) 112, 120, 120
  112 NA = NA + 1
      DO 114 J = NA, 100
  114 XSS(J) = BLANK
  120 CONTINUE
      RETURN
      END
C
      SUBROUTINE OHIST
C     +------------------------------------------------------------------------+
C     I HISTOGRAM OUTPUT ROUTINE                                               I
C     +------------------------------------------------------------------------+
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC6/  NHISTS, NHIST, LIMNO
      COMMON /BLOC7/  MTYPE(100), NENTRY(100), NCOOR(100), INTVLS(100),
     A                BEGIN(100), END(100), STEP(100), ZHIST(100)
      COMMON /BLOC8/  MTABLE(10000)
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      COMMON /BLOC18/ LOSS, NBLK(10), KFLG(10),
     A                XSTRT(10), XEND(10), LTHX(10), XBIN(10), NUNX(10),
     A                YSTRT(10), YEND(10), LTHY(10), YBIN(10), NUNY(10)
      LOGICAL LEGAL
      COMMON /BLC12A/ YMOM(100), YMOM2(100), CORR(100)
C
      NH = 0
      DO 500 K = 1, NHISTS
      M = NENTRY(K)
      N = INTVLS(K)
      NUNIT = NCOOR(K)
      CALL HSTUN (NUNIT, FACT, LEGAL)
      XBEG = BEGIN(K) / FACT
      DX = STEP(K) / FACT
      ZC = ZHIST(K)/UNIT(8)
      KFL = KFLAG(K) + 1
      NFL = NFLAG(K)
      NAVEL = MTYPE(K)
      GO TO (100,200,300), NAVEL
C
C     ONE DIMENSIONAL HISTOGRAM
C
  100 NH = NH + 1
      WRITE (NOUT, 9500) NH
 9500 FORMAT(1H1/'0HISTOGRAM NO',I3)
      CALL HISCAP (1, NUNIT, KFL, ZC, NFL)
      CALL TRHIST (M, N, XBEG, DX, NUNIT)
      SUM = MTABLE(M+N+2)
      IF(SUM .EQ. 0.0) GO TO 500
      XM = XMOM(K) / FACT
      XM2= SQRT(XMOM2(K)) / FACT
      WRITE (NOUT, 9100) XM, XM2
 9100 FORMAT(11X,'CENTER =',F10.5,3X,'RMS HALF WIDTH =',F10.5)
      GO TO 500
C
C     X COORDINATE OF TWO DIMENSIONAL HISTOGRAM
C
  200 NA = N
      NUNA = NUNIT
      ZA = ZC
      AMIN = XBEG
      DA = DX
      KFLA = KFL
      NFLA = NFL
      FACTA = FACT
      GO TO 500
C
C     Y COORDINATE OF TWO DIMENSIONAL HISTOGRAM
C
  300 NH = NH + 1
      WRITE (NOUT, 9500) NH
      CALL HISCAP (2, NUNA, KFLA, ZA, NFLA)
      CALL HISCAP (3, NUNIT, KFL, ZC, NFL)
      CALL OUTMAT (M, AMIN,NA,DA, XBEG,N,DX)
      MTT = M + (NA+1)*(N+1) +4
      SUM = MTABLE(MTT)
      IF(SUM .EQ. 0.) GO TO 500
      XM = XMOM(K) / (SUM*FACTA)
      XM2 = SQRT(XMOM2(K) / (SUM*FACTA**2) - XM**2)
      YM = YMOM(K) / (SUM*FACT)
      YM2 = SQRT(YMOM2(K) / (SUM*FACT**2) - YM**2)
      COR = CORR(K) / (SUM*FACTA*FACT) - XM*YM
      COR = COR / (XM2*YM2)
      WRITE(NOUT, 9100) XM, XM2
      WRITE(NOUT, 9100) YM, YM2
      WRITE(NOUT, 9300) COR
 9300 FORMAT(11X,'CORRELATION =',F10.5)
  500 CONTINUE
C
C     HISTOGRAMS OF PARTICLES LOST
C
      IF(LOSS .EQ. 0) RETURN
      DO 700 K = 1, LOSS
      NH = NH + 1
      KFL = KFLG(K) + 1
      WRITE (NOUT, 9520) NH, KPART(KFL)
 9520 FORMAT(1H1/'0HISTOGRAM NO',I3,' OF ',A4,' LOST')
      M = NBLK(K)
      N = LTHX(K)
      NUNIT = NUNX(K)
      CALL HSTUN (NUNIT, FACT, LEGAL)
      XBEG = XSTRT(K) / FACT
      DX = XBIN(K) / FACT
      NUND = NUNY(K)
      IF(NUND .NE. 0) GO TO 600
C
C     Z DISTRIBUTION
C
      CALL HISCAP (4, NUNIT, 0, 0.0, 0)
      CALL TRHIST (M, N, XBEG, DX, NUNIT)
      GO TO 700
C
C     Z VERSUS ANOTHER COORDINATE
C
  600 ND   = LTHY (K)
      CALL HSTUN (NUND, FACT, LEGAL)
      DMIN = YSTRT(K) / FACT
      DD = YBIN(K) / FACT
      CALL HISCAP (5, NUNIT, 0, 0.0, 0)
      CALL HISCAP (6, NUND,  0, 0.0, 0)
      CALL OUTMAT (M,XBEG,N,DX,DMIN,ND,DD)
  700 CONTINUE
      RETURN
      END
C
      SUBROUTINE OUTMAT (IPLOT, AMIN, NA, DA, DMIN, ND, DD)
C     +------------------------------------------------------------------------+
C     I PRINTS TWO DIMENSIONAL HISTOGRAMS
C     +------------------------------------------------------------------------+
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC8/  MTABL(10000)
      INTEGER IAROW(110)
      REAL    AROW(110), TOT(6), ALABEL(15)
      EQUIVALENCE (AROW(1),IAROW(1))
      DATA TOT / 1HT, 1HO, 1HT, 1HA, 1HL, 1HS /
      DATA IBLANK, IDASH, IEND, IAST / 1H , 1H-, 1HI, 1H* /
      IPLOI = IPLOT - 1
      MTT = (NA + 1)*(ND + 1) + 5
      IF(MTABL (IPLOI+MTT)) 2,2,4
C
C     UNFILLED HISTOGRAM
C
    2 WRITE (NOUT, 9001)
 9001 FORMAT(//,'0HISTOGRAM IS EMPTY')
      RETURN
C
C     X COORDINATES
C
    4 NLA = NA / 10 + 1
      ALABEL(1) = AMIN
      DO 15 N = 2, NLA
   15 ALABEL(N) = ALABEL(N - 1) + 10.0*DA
      WRITE (NOUT,9002) (ALABEL(K), K = 1, NLA)
 9002 FORMAT(1H0/16X,11F10.3)
      NALL = NA + 4
      DO 17 N = 1, NALL
   17 IAROW(N) = IBLANK
      DO 18 N = 1, 6
   18 AROW(NALL+N) = TOT(N)
      NALP = NALL + 6
      WRITE (NOUT,9003) (IAROW(N), N = 1, NALP)
 9003 FORMAT(1H+,22X,110A1)
C
C     UPPER X AXIS
C
      ICT = 1
      NAM = NA + 1
      DO 24 I = 1, NAM
      IAROW(I) = IDASH
      IF (ICT .EQ. 1 .OR. ICT .EQ. 5) IAROW(I) = IAST
      ICT = ICT + 1
      IF (ICT .EQ. 6) ICT = 1
   24 CONTINUE
      IAROW(NA+2) = IEND
      NAM = NA + 3
      NAP = NA + 10
      DO 26 I = NAM, NAP
   26 IAROW(I) = IDASH
      WRITE (NOUT,9024) (IAROW(M), M = 1, NAP)
 9024 FORMAT(1H ,20X,'I*',110A1)
C
C     BODY OF HISTOGRAM
C
      MM = 0
      NAP = NA + 9
      DLOW = DMIN
      DHIGH = DMIN + DD
      DO 60 N = 1, ND
      DO 30 K = 1, NAP
   30 IAROW(K) = IBLANK
      DO 48 K = 1, NA
      MM = MM + 1
      NN = MTABL(IPLOI+MM)
      CALL BCDWR(IBCDW,NN)
      IAROW(K) = IBCDW
   48 CONTINUE
      IAROW(NA+1) = IBLANK
      IAROW(NA+2) = IEND
      MM = MM + 1
      NN = MTABL(IPLOI+MM)
      DO 50 K = 1, 4
      CALL DIGITAL(IDIGIT,NN,K)
   50 IAROW(NA+K+5) = IDIGIT
      WRITE (NOUT,9004) DLOW, DHIGH, (IAROW(K), K = 1, NAP)
 9004 FORMAT(1H ,F8.3,' TO',F8.3,' I ',110A1)
      DLOW = DLOW + DD
      DHIGH = DLOW + DD
   60 CONTINUE
C
C     LOWER X AXIS
C
      ICT = 1
      NAM = NA + 1
      DO 74 I = 1, NAM
      IAROW(I) = IDASH
      IF (ICT .EQ. 1 .OR. ICT .EQ. 5) IAROW(I) = IAST
      ICT = ICT + 1
      IF (ICT .EQ. 6) ICT = 1
   74 CONTINUE
      IAROW(NA+2) = IEND
      NAM = NA + 3
      NAP = NA + 10
      DO 76 I = NAM, NAP
   76 IAROW(I) = IDASH
      WRITE (NOUT,9024) (IAROW(M), M = 1, NAP)
C
C     SUMS OF COLUMNS
C
      NAM = NA + 2
      DO 85 K = 1, NAP
   85 IAROW(K) = IBLANK
      IAROW(NAM) = IEND
      WRITE (NOUT,9007) (IAROW(K), K = 1, NAP)
      DO 90 IR = 1, 4
      DO 86   K = 1, NA
      MM = MM + 1
      NN = MTABL( IPLOI+MM)
      CALL DIGITAL(IDIGIT,NN,IR)
      IAROW(K) = IDIGIT
   86 CONTINUE
      MM = MM + 1
      IF (IR .EQ. 4) GO TO 87
      WRITE (NOUT,9007) (IAROW(K), K = 1, NAP)
      MM = MM - NA - 1
      GO TO 90
   87 NN = MTABL(IPLOI+MM)
      DO 88 K = 1, 4
      CALL DIGITAL(IDIGIT,NN,K)
   88 IAROW(NA+K+5) = IDIGIT
      WRITE (NOUT,9006) (IAROW(K), K = 1, NAP)
 9006 FORMAT(1H ,12X,'TOTALS',2X,'I ',110A1)
 9007 FORMAT(1H ,20X,'I ',110A1)
   90 CONTINUE
C
C     SUMMARY
C
      IAROW(1) = MTABL(IPLOI+MTT)
      DO 95 I = 1, 4
      N = MM + I
   95 IAROW(I+1) = MTABL(IPLOI+N)
  111 WRITE (NOUT,9104) (IAROW(I), I = 1, 5)
 9104 FORMAT(1H0,10X,'TOTAL NUMBER OF ENTRIES =',I8,
     1       ' INCLUDING UNDERFLOW AND OVERFLOW AS FOLLOWS'
     2       /1H0,32X,'UNDERFLOW',7X,'OVERFLOW',
     3       /20X,'ACROSS',2(5X,I10)/20X,'DOWN  ',2(5X,I10)/)
 120  RETURN
      END
C
      SUBROUTINE SCATT_MY
C     +------------------------------------------------------------------------+
C     I THIS ROUTINE ADDS SCATTERING TO THE RAY PARAMETERS                     I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
c-----
      rn_sig  = 6.

      dz_elem = data(i+1)*100.
      theta_0 = data(i+2)

      sig_rr  = theta_0 * dz_elem / sqrt(12.)
      sig_r1  = theta_0
c ---
c     At the end of element
c ---

      go to 30

c---  PDG --> horizontal

      sig = sqrt(-2.*alog(ranf(-1.)))
      phi = 6.283185308 * ranf(-1.)
      xi1 = sig * cos(phi)
      xi2 = sig * sin(phi)

      del_xx = sig_rr * (xi2*sqrt(3.)+ xi1)
      del_x1 = sig_r1 *  xi2
      ray(1) = ray(1) + del_xx
      ray(2) = ray(2) + del_x1

c---  PDG --> vertical

      sig = sqrt(-2.*alog(ranf(-1.)))
      phi = 6.283185308 * ranf(-1.)
      xi1 = sig * cos(phi)
      xi2 = sig * sin(phi)

      del_yy = sig_rr * (xi2*sqrt(3.)+ xi1)
      del_y1 = sig_r1 *  xi2
      ray(3) = ray(3) + del_yy
      ray(4) = ray(4) + del_y1
c---
      return

c==== Horizontal + Vertical

c---  Horizontal

   20 sig = sqrt(-2.*alog(ranf(-1.)))
      phi = 6.283185308 * ranf(-1.)
      del_xx = sig_rr * sig * cos(phi)
      del_x1 = sig_r1 * sig * sin(phi)

c---  Vertical

      sig = sqrt(-2.*alog(ranf(-1.)))
      phi = 6.283185308 * ranf(-1.)
      del_yy = sig_rr * sig * cos(phi)
      del_y1 = sig_r1 * sig * sin(phi)
c----
      if (sqrt(del_x1**2+del_y1**2) .GT. sig_r1*rn_sig .OR.
     +    sqrt(del_xx**2+del_yy**2) .GT. sig_rr*rn_sig)  go to 20

c----
c     ray(1) = ray(1) + del_xx
c     ray(2) = ray(2) + del_x1
c     ray(3) = ray(3) + del_yy
c     ray(4) = ray(4) + del_y1
c     ray(1) = ray(1) + ray(2) * dz_elem * 0.5
c     ray(3) = ray(3) + ray(4) * dz_elem * 0.5
c----
      ray(1) = ray(1) + del_xx + del_x1 * dz_elem * 0.5
      ray(3) = ray(3) + del_yy + del_y1 * dz_elem * 0.5
      ray(2) = ray(2) + del_x1
      ray(4) = ray(4) + del_y1
c----
      return

c==== Angles + Coordinates

c---  Angles

   30 sig = sqrt(-2.*alog(ranf(-1.)))
      phi = 6.283185308 * ranf(-1.)
      del_x1 = sig_r1 * sig * cos(phi)
      del_y1 = sig_r1 * sig * sin(phi)

c---  Coordinates

      sig = sqrt(-2.*alog(ranf(-1.)))
      phi = 6.283185308 * ranf(-1.)
      del_xx = sig_rr * sig * cos(phi)
      del_yy = sig_rr * sig * sin(phi)
c---
      if (sqrt(del_x1**2+del_y1**2) .GT. sig_r1*rn_sig .OR.
     +    sqrt(del_xx**2+del_yy**2) .GT. sig_rr*rn_sig)  go to 30

      ray(1) = ray(1) + del_xx + del_x1 * dz_elem * 0.5
      ray(3) = ray(3) + del_yy + del_y1 * dz_elem * 0.5
      ray(2) = ray(2) + del_x1
      ray(4) = ray(4) + del_y1

c====
      RETURN
      END
C
      SUBROUTINE RAYRUN
C     +------------------------------------------------------------------------+
C     I TRACKS RAYS AND GENERATES HISTOGRAMS                                   I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC4/  RAYMAX(6), PBEAM, P0, NORAYS
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC6/  NHISTS, NHIST, LIMNO
      COMMON /BLOC7/  MTYPE(100), NENTRY(100), NCOOR(100), INTVLS(100),
     A                BEGIN(100), END(100), STEP(100), ZHIST(100)
      COMMON /BLOC8/  MTABLE(10000)
      COMMON /BLOC10/ APB(2), LAYL, LAYX, RAB1, RAB2, FACE
      REAL            LAYL, LAYX
      COMMON /BLOC11/ QAP(3), ELLIPS, HYPER
      LOGICAL         ELLIPS, HYPER
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC14/ MMAX, GTOP, DB(20), COSM(20), SINM(20)
      COMMON /BLOC15/ LL, KH2, KV2, KH, KV, KHL, KVL, RAY2(6),
     A                RH(4), RV(4)
      REAL LL, KH2, KV2, KH, KV, KHL, KVL
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      COMMON /BLOC17/ IP, IC(4), IS(4)
      COMMON /BLOC18/ LOSS, NBLK(10), KFLG(10),
     A                XSTRT(10), XEND(10), LTHX(10), XBIN(10), NUNX(10),
     A                YSTRT(10), YEND(10), LTHY(10), YBIN(10), NUNY(10)
      LOGICAL ELLS, HYPS, BSTOP, QSTOP
      INTEGER ICS(4), ISS(4)
      REAL QAPS(3), VALX(4), RAYADD(4), LS
C
C     SELECT RAY AT RANDOM
C
      NCT = 0
  100 NCT = NCT + 1
      P0 = PBEAM
c
      CALL EMIT_MY
c
      Z = 0.
      LFLAG = 0
      IF(DKFLAG) CALL DECAYZ (ZD)
      IAP = 0
      NHIST = 0
      IP = 0
      ELLIPS = .FALSE.
      HYPER = .FALSE.
      APB(1) = 0.0
      APB(2) = 0.0
      MMAX = 0
      INEXT = - 10
      IF(.NOT. MPA) GO TO 130
      DO 120 IM = 1, 20
  120 DB(IM) = 0.0
  130 I = 1
      DO 140 KFL = 1, 3
      DO 140 IFL = 1, 9
  140 IFLAG(KFL,IFL) = .FALSE.
      DO 150 NH = 1, NHISTS
  150 SET(NH) = .FALSE.
C
C     TRACK THROUGH ONE ELEMENT
C
  200 NTYPE = IDATA(I)
      IF(NTYPE .EQ. 53) GO TO 530
      IF(NTYPE .GE. 50) GO TO 500
      GO TO (210, 220, 230, 240, 250, 260, 270, 600, 290, 600,
     A       600, 600, 600, 340, 600, 360, 600, 380, 390, 400,
     B       410), NTYPE
C
C     RMS ADDITION TO BEAM
C
  210 IF(IDATA(I+8) .NE. LFLAG) GO TO 600
c
      call SCATT_MY
      P = P + DATA(I+7)
	go to 600
c
  211 CONTINUE
      DO 215 IR = 1, 4
      VALX(IR) = 2.0 * RANF(-1.) - 1.0
  215 RAYADD(IR) = DATA(I+IR) * VALX(IR)
      RN1 = VALX(1) ** 2 + VALX(3) ** 2
      RN2 = VALX(2) ** 2 + VALX(4) ** 2
      IF(RN1 .GT. 1.0 .OR. RN2 .GT. 1.0) GO TO 211
      DO 217 IR = 1, 4
  217 RAY(IR) = RAY(IR) + RAYADD(IR)
      VALX(1) = 2.0 * RANF(-1.) - 1.0
      P = P + P0 * DATA(I+6) * VALX(1) + DATA(I+7)
c
c --- Normal Distribution -> Thin Scatterer
c
  218 XI1 = SQRT(-2.*ALOG(RANF(-1.)))
      XI2 = 6.283185308 * RANF(-1.)
      XR1 = XI1 * COS(XI2)
      XR2 = XI1 * SIN(XI2)
c     ray(1) = ray(1) + XR1*DATA(I+1)
      ray(2) = ray(2) + XR2*DATA(I+2)
C
      YI1 = SQRT(-2.*ALOG(RANF(-1.)))
      YI2 = 6.283185308 * RANF(-1.)
      YR1 = YI1 * COS(YI2)
      YR2 = YI1 * SIN(YI2)
c     ray(3) = ray(3) + YR1*DATA(I+3)
      ray(4) = ray(4) + YR2*DATA(I+4)
c---
      GO TO 600
C
C     FRINGE FIELD
C
  220 IF(LFLAG .EQ. 2) GO TO 600
      H = DATA(I+1) / P
      TANB = DATA(I+2)
      TANCOR = TANB - H * DATA(I+5)
      RAY2(1) = RAY(1)
      RAY2(2) = RAY(2) + H * RAY(1) * TANB
      RAY2(3) = RAY(3)
      RAY2(4) = RAY(4) - H * RAY(3) * TANCOR
      IF(.NOT. SEC) GO TO 225
      SECB = DATA(I+3)
      SEX = DATA(I+4)
      RAY2(1) = RAY(1) + 0.5 * H * ((SECB*RAY(3))**2 - (TANB*RAY(1))**2)
      RAY2(2) = RAY2(2) + H * (TANB**2 * (RAY(1)*RAY(2) - RAY(3)*RAY(4))
     B     + (H * DATA(I+6) + SEX) * RAY(1) ** 2
     C     + (H * DATA(I+7) - SEX) * RAY(3) ** 2)
      RAY2(3) = RAY(3) + H * TANB * TANCOR * RAY(1) * RAY(3)
      RAY2(4) = RAY2(4) - H * (TANCOR * TANB * RAY(1) * RAY(4)
     B    + (H * DATA(I+8) + 2.0 * SEX) * RAY(1) * RAY(3)
     C    + SECB ** 2 * RAY(2) * RAY(3))
  225 CALL RESET (RAY, RAY2)
      GO TO 600
C
C     DRIFT SPACE
C
  230 LL = DATA(I+1)
      IF(.NOT. DKFLAG) GO TO 235
      IF(LFLAG .NE. 0 .OR. Z + LL .LT. ZD) GO TO 235
      LL = ZD - Z
      RAY(1) = RAY(1) + LL * RAY(2)
      RAY(3) = RAY(3) + LL * RAY(4)
      GO TO 700
  235 RAY(1) = RAY(1) + LL * RAY(2)
      RAY(3) = RAY(3) + LL * RAY(4)
      GO TO 590
C
C     BENDING MAGNET
C
  240 IAP = IAP + 1
      IF(BSTOP(LFLAG)) GO TO 650
      LL = DATA(I+1)
      IF(.NOT. DKFLAG) GO TO 244
      IF(LFLAG - 1) 241, 244, 245
  241 IF(Z + LL .LT. ZD) GO TO 244
      LL = ZD - Z
      CALL BEND (KSTOP)
      IF(KSTOP) 650, 700, 650
  244 CALL BEND (KSTOP)
      IF(KSTOP) 650, 249, 650
  245 IF(DATA(I+4) .EQ. 0.0) GO TO 247
      THETA = LL * DATA(I+2)
      TANTH = TAN(THETA)
      THE2 = (RAY(2) + TANTH) / (1.0 - RAY(2) * TANTH)
      F = SQRT ((1.0 + THE2 ** 2) / (1.0 + RAY(2) ** 2))
      RAY(1) = F * (RAY(1) + DATA(I+4)) - DATA(I+4)
      RAY(2) = THE2
      RAY(3) = RAY(3) + (DATA(I+4) + RAY(1)) * SIN(THETA) * RAY(4)
      RAY(4) = F * RAY(4)
      GO TO 249
  247 RAY(1) = RAY(1) + LL * RAY(2)
      RAY(3) = RAY(3) + LL * RAY(4)
  249 IF(BSTOP(LFLAG)) GO TO 650
      GO TO 590
C
C     QUADRUPOLE
C
  250 IAP = IAP + 1
      IF(QSTOP(LFLAG)) GO TO 650
      LL = DATA(I+1)
      IF(LFLAG .EQ. 2) GO TO 255
      GTOP = 0.5 * DATA(I+1) * DATA(I+2) / P
      IF(MMAX .NE. 0) CALL MULTI
      IF(.NOT. DKFLAG) GO TO 254
      IF(LFLAG .NE. 0) GO TO 254
      IF(Z + LL .LT. ZD) GO TO 254
      LL = ZD - Z
      CALL QUAD
      GO TO 700
  254 CALL QUAD
      IF(MMAX .NE. 0) CALL MULTI
      GO TO 259
  255 RAY(1) = RAY(1) + LL * RAY(2)
      RAY(3) = RAY(3) + LL * RAY(4)
  259 IF(QSTOP(LFLAG)) GO TO 650
      GO TO 590
C
C     SLIT
C
  260 IAP = IAP + 1
      IFP = IDATA(I+1) / 100
      IFF = IDATA(I+1) - 100 * IFP
      IF(IFP .NE. LFLAG) GO TO 267
      IFG = IDATA(I+3)
      IF(IFG .NE. 0) GO TO 265
c
        if (data(i+2) .ge. 0.) then
      IF(ABS(RAY(IFF)) .LT. DATA(I+2)) GO TO 267
      GO TO 266
        else
      IF(ABS(RAY(IFF)) .GT. ABS(DATA(I+2))) GO TO 267
      GO TO 266
        endif
  265 RAD2 = (RAY(IFF)/DATA(I+2))**2+(RAY(IFG)/DATA(I+4))**2
        if (data(i+2) .ge. 0.) then
      IF(RAD2 .LT. 1.0) GO TO 267
      GO TO 266
        else
      IF(RAD2 .GT. 1.0) GO TO 267
      GO TO 266
        endif
c
  266 I = I + NU(6)
      NTYPE = IDATA(I)
      IF(NTYPE .EQ. 1 .AND. IDATA(I+8) .EQ. LFLAG) GO TO 211
      GO TO 650
  267 I = I + NU(6)
      IF(I .GT. I1) GO TO 610
      NTYPE = IDATA(I)
      IF(NTYPE .EQ. 1 .AND. IDATA(I+8) .EQ. LFLAG) GO TO 600
      GO TO 200
C
C     SHIFT
C
  270 CONTINUE
      DO 271 J = 1, 6
  271 RAY(J) = RAY(J) + DATA(I+J)
      P = P + DATA(I+6) * P0
      GO TO 600
C
C     REPEAT
C
  290 CALL REPEAT
      GO TO 600
C
C     ARBITRARY MATRIX
C
  340 NROW = IDATA(I+7)
      IF(I .NE. INEXT) CALL RESET(RAY2, RAY)
      RAY2(NROW) = 0.0
      DO 342 IR = 1, 6
  342 RAY2(NROW) = RAY2(NROW) + RAY(IR) * DATA(I+IR)
      IF(.NOT. SEC .OR. IDATA(I+8) .NE. 0) GO TO 344
      IPL = I + 8
      DO 343 IB = 1, 6
      DO 343 JC = IB, 6
      IPL = IPL + 1
  343 RAY2(NROW) = RAY2(NROW) + RAY(IB) * RAY(JC) * DATA(IPL)
  344 INEXT = I + NU(14)
      IF(IDATA(INEXT) .NE. 14) CALL RESET (RAY, RAY2)
      GO TO 600
C
C     MULTIPOLE ABERRATIONS AND BENDING MAGNET PARAMETERS
C
  360 NM = IDATA(I+1)
      IF(NM .GT. 0) GO TO 362
      IF(LFLAG .EQ. 2) GO TO 600
      NM = - NM
      DB(NM) = DATA(I+2)
      COSM(NM) = DATA(I+3)
      SINM(NM) = DATA(I+4)
      MAXX = MAX0(NM,MMAX)
      MMAX = 0
      DO 361 IM = 1, MAXX
      IF(DB(IM) .NE. 0.0) MMAX = IM
  361 CONTINUE
      GO TO 600
  362 IF(NM .EQ. 4 .OR. NM .EQ. 5) GO TO 363
      IF (NM .EQ. 11) GO TO 366
      IF(NM .EQ. 100) GO TO 364
      IF(NM .EQ. 101) GO TO 365
      GO TO 600
  363 APB(NM-3) = DATA(I+2)
      GO TO 600
  364 ELLIPS = .TRUE.
      QAP(1) = DATA(I+2)
      QAP(2) = DATA(I+3)
      GO TO 600
  365 HYPER = .TRUE.
      QAP(3) = DATA(I+2)
      GO TO 600
  366 P0 = DATA(I+2)
      RAY(6) = (P - P0) / P0
      GO TO 600
C
C     SEXTUPOLE
C
  380 LL = DATA(I+1)
      IF(.NOT. DKFLAG) GO TO 384
      IF(LFLAG - 1) 381, 384, 235
  381 IF(Z + LL .LT. ZD) GO TO 384
      LL = ZD - Z
      CALL SEXT
      GO TO 700
  384 CALL SEXT
      GO TO 590
C
C     SOLENOID
C
  390 LL = DATA(I+1)
      IF(.NOT. DKFLAG) GO TO 394
      IF(LFLAG - 1) 391, 394, 235
  391 IF(Z + LL .LT. ZD) GO TO 394
      LL = ZD - Z
      CALL SOLO
      GO TO 700
  394 CALL SOLO
      GO TO 590
C
C     BEAM ROTATION
C
  400 CS = DATA(I+1)
      SN = DATA(I+2)
      RAY2(1) = RAY(1) * CS + RAY(3) * SN
      RAY2(3) = - RAY(1) * SN + RAY(3) * CS
      RAY2(2) = RAY(2) * CS + RAY(4) * SN
      RAY2(4) = - RAY(2) * SN + RAY(4) * CS
      CALL RESET (RAY, RAY2)
      GO TO 600
C
C     THIN FOIL
C
  410 th = data(i+1)
      xr1 = sqrt(-2.*alog(ranf(r1)))
      xr2 = 6.2831853 * ranf(r2)
      ray(2) = ray(2) + th * xr1 * sin(xr2)
c
      xr3 = sqrt(-2.*alog(ranf(r3)))
      xr4 = 6.2831853 * ranf(r4)
      ray(4) = ray(4) + th * xr3 * sin(xr4)
      go to 600
C
C     SAVE VALUES FOR HISTOGRAM
C
  500 NHIST = NHIST + 1
      IF(LFLAG .NE. KFLAG(NHIST)) GO TO 600
      NCO = NCOOR(NHIST)
      VALUE(NHIST) = HSTVAL(NCO)
      SET(NHIST) = .TRUE.
      GO TO 600
C
C     SET HISTOGRAM FLAG
C
  530 IFL = IDATA(I+1)
      IFLAG(LFLAG+1,IFL) = .TRUE.
      GO TO 600
C
C     NEXT ELEMENT
C
  590 Z = Z + DATA(I+1)
  600 I = I + NU(NTYPE)
      IF(NCT .EQ. 4) WRITE (6,9710) NCT, Z, I, (RAY(J),J=1,6), P
 9710 FORMAT('EL',I3,1X,1PE24.16,1X,I5,6(1PE24.16,1X),1PE24.16)
      IF(I .LE. I1) GO TO 200


C
C     END OF SYSTEM REACHED. IF WANTED SWITCH TO NEUTRAL DAUGHTER
C
  610 go to 690
      DO 620 J = 1, 6
  620 RAY(J) = RAYN(J)
      NHIST = NHS
      I = ISAVE
      NTYPE = IDATA(I)
      IP = IPS
      DO 625 J = 1, 4
      IC(J) = ICS(J)
  625 IS(J) = ISS(J)
      Z = ZS
      LL = LS
      P = PN
      P0 = P0S
      LFLAG = 2
      IAP = IAPS
      ELLIPS = ELLS
      HYPER = HYPS
      APB(1) = APBS1
      APB(2) = APBS2
      DO 630 J = 1, 3
  630 QAP(J) = QAPS(J)
  640 GO TO (600,600,235,245,254,600,600,600,600,600,
     A       600,600,600,600,600,600,600,384,394,600),NTYPE
C
C     PARTICLE STOPPED BY APERTURE
C
  650 ISTOP(LFLAG+1,IAP) = ISTOP(LFLAG+1,IAP) + 1
      IF(LOSS .EQ. 0) GO TO 610
      DO 670 K = 1, LOSS
      IF(LFLAG .NE. KFLG(K)) GO TO 670
      M = NBLK(K)
      XMIN = XSTRT(K)
      XMAX = XEND(K)
      XSTP = XBIN(K)
      NX = LTHX(K)
      NUX = NUNX(K)
      X = HSTVAL(NUX)
      NUY = NUNY(K)
      IF(NUY .NE. 0) GO TO 660
      CALL HISTO (X, M, NX, XMIN, XMAX, XSTP)
      GO TO 670
  660 YMIN = YSTRT(K)
      YMAX = YEND(K)
      YSTP = YBIN(K)
      NY = LTHY(K)
      Y = HSTVAL(NUY)
      CALL ENTMAT (X,Y,M,XMIN,XMAX,NX,XSTP,YMIN,YMAX,NY,YSTP)
  670 CONTINUE
      GO TO 610
C
C     ENTER RAY INTO HISTOGRAMS
C
  690 CALL EHIST
      IF (NCT .LT. NORAYS) GO TO 100
      RETURN
C
C     DECAY
C
  700 CALL DECAY
      DO 710 J = 1, 6
  710 RAY(J) = RAYC(J)
      NHS = NHIST
      ISAVE = I
      IPS = IP
      DO 715 J = 1, 4
      ICS(J) = IC(J)
  715 ISS(J) = IS(J)
      ZS = Z
      LL = DATA(I+1) - LL
      LS = LL
      P = PC
      P0S = P0
      LFLAG = 1
      IAPS = IAP
      ELLS = ELLIPS
      HYPS = HYPER
      APBS1 = APB(1)
      APBS2 = APB(2)
      DO 720 J = 1, 3
  720 QAPS(J) = QAP(J)
      GO TO (600, 600, 235, 244, 254, 600, 600, 600, 600, 600, 600,
     A       600, 600, 600, 600, 600, 600, 384, 394, 600, 600), NTYPE
      END
C
      SUBROUTINE TRHIST (NHST, M, A, D, NHTYP)
C     +------------------------------------------------------------------------+
C     I PRINTS ONE DIMENSIONAL HISTOGRAM                                       I
C     +------------------------------------------------------------------------+
      COMMON /BLOC8/  MTABL(10000)
      COMMON /BLOC3/  NIN, NOUT, NOL
      DIMENSION       HIST(100)
C
      NHSI = NHST-1
      NSUM = MTABL(NHSI+M+3)
      MORE = M+1
      LIM = M+2
      AA = A
      IF(NSUM .NE. 0) GO TO 106
C
C     UNFILLED HISTOGRAM
C
      WRITE (NOUT, 9005)
 9005 FORMAT(//,'0HISTOGRAM IS EMPTY')
      RETURN
C
C     DETERMINATION OF SCALE
C
  106 IF (NHTYP .EQ. 21) THEN
        R1 = A
        DO 180 I = 1, M
        R2 = R1 + D
        SSS = 3.14159265 * (R2+R1) * D
        MTABL(NHSI+I) = MTABL(NHSI+I) / SSS
        R1 = R2
  180   CONTINUE
        ENDIF
      NSCALE = 0
      DO 190 I = 1, M
      IF (MTABL(NHSI+I) - NSCALE)  190, 190, 185
  185 NSCALE = MTABL(NHSI+I)
  190 CONTINUE
      WRITE (NOUT, 9010) NSCALE
 9010 FORMAT(1H0/11X,'INTERVAL',30X,'SCALE FACTOR.. 100 X"S EQUAL',I6,
     A       ' ENTRIES')
C
C     PLOTTING OF HISTOGRAM
C
      WRITE (NOUT,9020)  MTABL(NHSI+LIM)
 9020 FORMAT(10X,' UNDERFLOW',2X,I5,1X,1HI,/1X,28(1H=))
      DO 300 I = 1, M
      AB = AA + D
      NUM = (MTABL(NHSI+I)*100)/NSCALE
      CALL LOADX ( HIST, NUM)
      WRITE (NOUT,9030) AA, AB, MTABL(NHSI+I), HIST
 9030 FORMAT(1H ,F8.3,' TO ',F8.3,1X,I5,1X,1HI,1X,100A1)
      AA = AB
  300 CONTINUE
      WRITE (NOUT,9040)  MTABL(NHSI+MORE)
 9040 FORMAT(1X,28(1H=),/10X,' OVERFLOW ',2X,I5,1X,1HI)
C
C     SUMMARY
C
      WRITE (NOUT, 9050) NSUM
 9050 FORMAT(1H0,10X,'TOTAL NUMBER OF ENTRIES =',I8,
     A       ' INCLUDING UNDERFLOW AND OVERFLOW'/)
 5000 RETURN
      END
C
      SUBROUTINE ZERO
C     +------------------------------------------------------------------------+
C     I CLEARS HISTOGRAM STORAGE                                               I
C     +------------------------------------------------------------------------+
      COMMON /BLOC6/  NHISTS, NHIST, LIMNO
      COMMON /BLOC8/  MTABLE(10000)
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      COMMON /BLC12A/ YMOM(100), YMOM2(100), CORR(100)
C
      DO 50 NH = 1, NHISTS
      XMOM(NH) = 0.0
      XMOM2(NH) = 0.0
      YMOM(NH) = 0.0
      YMOM2(NH) = 0.0
   50 CORR(NH) = 0.0
      DO 100 KK = 1, LIMNO
  100 MTABLE(KK) = 0
      DO 150 K = 1, 500
      DO 150 L = 1, 3
  150 ISTOP(L,K) = 0
      RETURN
      END
C
C === TURT00
C
      SUBROUTINE BCDWR (BCDW, INTGER)
C     +------------------------------------------------------------------------+
C     I RETURNS INTEGER AS RIGHT-JUSTIFIED EBCDIC WORD                         I
C     +------------------------------------------------------------------------+
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      INTEGER BCDW
C
      IF (INTGER .GT. 0) GO TO 100
      BCDW = BLANK
      RETURN
  100 IF (INTGER .GT. 35) GO TO 200
      BCDW = TABLE(INTGER+1)
      RETURN
  200 BCDW = SEMI(4)
      RETURN
      END
C
      SUBROUTINE BEND (KSTOP)
C     +------------------------------------------------------------------------+
C     I TRACKS CHARGED PARTICLES THROUGH A BENDING MAGNET                      I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC4/  RAYMAX(6), PBEAM, P0, NORAYS
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC9/  L, H, N, BDB
      REAL            L, N
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC15/ LL, KH2, KV2, KH, KV, KHL, KVL, RAY2(6),
     A                RH(4), RV(4)
      REAL LL, KH2, KV2, KH, KV, KHL, KVL
C
      KSTOP = 0
      H     = DATA(I+2)
      N     = DATA(I+3)
      BDB   = DATA(I+5)
      IF(N .EQ. 0.0 .AND. BDB .EQ. 0.0) GO TO 300
      KH2 = H ** 2 * (1.0 - N)
      KV2 = H ** 2 * N
      CALL FOCUS (KH2, LL, KH, KHL, RH)
      CALL FOCUS (KV2, LL, KV, KVL, RV)
      CX = RH(1)
      SX = RH(2)
      CY = RV(1)
      SY = RV(2)
      IF(ABS(KHL) .LT. 0.01) GO TO 10
      X10 = (1.0 - CX) / KH2
      Q1  = (LL  - SX) / KH2
      Q2  = (3.0 * Q1 - SX * X10) / KH2
      GO TO 20
   10 SKL = KHL ** 2
      X10 = LL ** 2 * (0.5 - SKL / 24.0)
      Q1  = LL ** 3 * (1.0 / 6.0 - SKL / 120.0)
      Q2  = LL ** 5 * (0.1 - SKL / 84.0)
   20 IF(ABS(KVL) .LT. 0.01) GO TO 30
      Y34 = 0.5 * (SY - LL * CY) / KV2
      GO TO 40
   30 Y34 = LL ** 3 * (1.0 / 6.0 - KV2 * LL ** 2 / 60.0)
   40 X11 = 0.5 * LL * SX
      X12 = 0.5 * (LL * X10 - Q1)
      X16 = 0.5 * (X10 ** 2 - SX * Q1)
      X21 = 0.5 * (SX + LL * CX)
      X22 = X11
      X26 = X12
      Y33 = 0.5 * LL * SY
      Y43 = 0.5 * (SY + LL * CY)
      Y44 = Y33
      D = KH2 - 4.0 * KV2
      IF(ABS(D * LL ** 2) .LT. 1.0E-6) GO TO 50
      X144 = (SY ** 2 - 2.0 * X10) / D
      X244 = 2.0 * (SY * CY - SX) / D
      Y324 = (2.0 * CY * X10 - SX * SY) / D
      Y424 = (SX * CY - CX * SY + 2.0 * RV(3) * X10) / D
      GO TO 100
   50 X144 = 2.0 * X16
      X244 = 2.0 * X12
      Y324 = 0.5 * SY * Q1
      Y424 = 0.5 * (SY * X10 + CY * Q1)
  100 X112 = SX * X10 / 3.0
      X116 = 0.5 * SX * Q1 - X10 ** 2 / 6.0
      X122 = X10 ** 2 / 3.0
      X126 = (SX * X10 ** 2 - CX * Q2) / 6.0
      X166 = (X10 ** 3 - SX * Q2) / 3.0
      X212 = (2.0 * SX ** 2 - X10) / 3.0
      X216 = 2.0 * X112 - 0.5 * (LL * X10 - Q1)
      X222 = 2.0 * X112
      X226 = SX * Q1 - X116
      X266 = 2.0 * X126
      Y323 = SY * X10 - Y424
      Y423 = CY * X10 + KV2 * Y324
      Y336 = 0.5 * (SY * Q1 - Y324)
      Y436 = 0.5 * (CY * Q1 + Y323)
      IF(ABS(KH2) .LT. 0.0001) GO TO 110
      Y346 = (Y34 + SY * X10 - 2.0 * Y424) / KH2
      GO TO 120
  110 Y346 = 0.5 * (SY * X10 - CY * Q1 - Y424) / KV2
  120 Y446 = 0.5 * (SY * Q1 + Y324)
      A1 = H ** 3 * (N + N - BDB - 1.0) * 2.0
      A2 = H * (2.0 - N)
      C1 = H ** 3 * (BDB - N) * 2.0
      C2 = H * N
      T116 = A1*X116 - KH2*H*X122 + A2*X11
      T216 = A1*X216 - KH2*H*X222 + A2*X21 - H * (RH(1)*SX + RH(3)*X10)
      T126 = A1*X126 + H*X112 + A2*X12
      T226 = A1*X226 + H*X212 + A2*X22 - H * (RH(2)*SX + RH(4)*X10)
      T166 = 0.5 * (A1*X166 + H*X122) + A2*X16
      T266 = 0.5 * (A1*X266 + H*X222) + A2*X26 - H*X10*SX
      T336 = C1*Y336 - KV2*H*Y324 + C2*Y33
      T436 = C1*Y436 - KV2*H*Y424 + C2*Y43 - H*X10*RV(3)
      T346 = C1*Y346 + H*Y323 + C2*Y34
      T446 = C1*Y446 + H*Y423 + C2*Y44 - H*X10*RV(4)
      DH = H * (P - P0) / P
      RAY2(1) = (RH(1) + DH*T116) * RAY(1) + (RH(2) + DH*T126) * RAY(2)
     A        + (X10  + DH*T166) * DH
      RAY2(2) = (RH(3) + DH*T216) * RAY(1) + (RH(4) + DH*T226) * RAY(2)
     A        + (SX   + DH*T266) * DH
      RAY2(3) = (RV(1) + DH*T336) * RAY(3) + (RV(2) + DH*T346) * RAY(4)
      RAY2(4) = (RV(3) + DH*T436) * RAY(3) + (RV(4) + DH*T446) * RAY(4)
      IF(.NOT. SEC) GO TO 400
      X111 = X10 - KH2 * X122
      X133 = X10 - KV2 * X144
      X134 = 0.5 * X244
      X211 = SX  - KH2 * X222
      X233 = SX  - KV2 * X244
      X234 = X133 - KV2 * X144
      Y313 = 0.5 * (SX * SY + KH2 * Y324)
      Y314 = 2.0 * Y424 - SY * X10
      Y413 = 0.5 * (CX * SY + SX * CY + KH2 * Y424)
      Y414 = 0.5 * (SX * SY - KH2 * Y324)
      T111 = 0.5 * (A1*X111 + KH2**2*H*X122)
      T211 = 0.5 * (A1*X211 + KH2**2*H*X222) - H*RH(1)*RH(3)
      T112 = (A1 - KH2*H) * X112 + H*RH(2)
      T212 = (A1 - KH2*H) * X212 + H * (RH(4)-RH(1)*RH(4)-RH(3)*RH(2))
      T122 = 0.5 * (A1*X122 + H*X111)
      T222 = 0.5 * (A1*X222 + H*X211) - H*RH(2)*RH(4)
      B1 = H ** 3 * (BDB + BDB - N)
      T133 = 0.5 * (B1*X133 - KV2**2*H*X144)
      T233 = 0.5 * (B1*X233 - KV2**2*H*X244)
      T134 = (B1 + KV2*H) * X134
      T234 = (B1 + KV2*H) * X234
      T144 = 0.5 * (B1*X144 - H*X133)
      T244 = 0.5 * (B1*X244 - H*X233)
      T313 = C1*Y313 + KH2*KV2*H*Y324
      T413 = C1*Y413 + KH2*KV2*H*Y424 - H*RH(1)*RV(3)
      T314 = C1*Y314 - KH2*H*Y323 + H*RV(2)
      T414 = C1*Y414 - KH2*H*Y423 + H * (RV(4) - RH(1)*RV(4))
      T323 = C1*Y323 - KV2*H*Y314
      T423 = C1*Y423 - KV2*H*Y414 - H*RH(2)*RV(3)
      T324 = C1*Y324 + H*Y313
      T424 = C1*Y424 + H*Y413 - H*RH(2)*RV(4)
      RAY2(1) = RAY2(1) +
     A     T111*RAY(1)**2 + T112*RAY(1)*RAY(2) + T122*RAY(2)**2 +
     B     T133*RAY(3)**2 + T134*RAY(3)*RAY(4) + T144*RAY(4)**2
      RAY2(2) = RAY2(2) +
     A     T211*RAY(1)**2 + T212*RAY(1)*RAY(2) + T222*RAY(2)**2 +
     B     T233*RAY(3)**2 + T234*RAY(3)*RAY(4) + T244*RAY(4)**2
      RAY2(3) = RAY2(3) + (T313*RAY(3) + T314*RAY(4)) * RAY(1) +
     A                    (T323*RAY(3) + T324*RAY(4)) * RAY(2)
      RAY2(4) = RAY2(4) + (T413*RAY(3) + T414*RAY(4)) * RAY(1) +
     A                    (T423*RAY(3) + T424*RAY(4)) * RAY(2)
      GO TO 400
  300 ALFA = LL * H
      RHO0 = DATA(I+4)
      RHO  = RHO0 * P/P0
      THETA1 = ATAN(RAY(2))
      COST1  = COS(THETA1)
      SINT2 = SIN(THETA1+ALFA) - SIN(ALFA) * (RAY(1) + RHO0) / RHO
      IF(ABS(SINT2) .GE. 1.0) GO TO 310
      COST2 = SQRT(1. - SINT2**2)
      COSAL = COS(ALFA)
      RAY2(1)=RAY(1)*COSAL+RHO*(COST2-COS(THETA1+ALFA))-RHO0*(1.-COSAL)
      RAY2(2)=SINT2/COST2
      RAY2(3)=RAY(3)+RAY(4)*RHO*COST1*(ALFA+THETA1-ASIN(SINT2))
      RAY2(4)=RAY(4)*COST1/COST2
      GO TO 400
  310 KSTOP = 1
      RETURN
  400 CONTINUE
      CALL RESET (RAY, RAY2)
      RETURN
      END
C
      LOGICAL FUNCTION BSTOP (LFLAG)
C     +------------------------------------------------------------------------+
C     I RETURNS .TRUE., IF A PARTICLE HITS A BENDING APERTURE                  I
C     +------------------------------------------------------------------------+
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC10/ APB(2), LAYL, LAYX, RAB1, RAB2, FACE
      REAL            LAYL, LAYX
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
C
      IF(.NOT. CAP(LFLAG+1)) GO TO 20
      IF(APB(1) .EQ. 0.0) GO TO 10
      IF(ABS(RAY(1)) .GT. APB(1)) GO TO 30
   10 IF(APB(2) .EQ. 0.0) GO TO 20
      IF(ABS(RAY(3)) .GT. APB(2)) GO TO 30
   20 BSTOP = .FALSE.
      RETURN
   30 BSTOP = .TRUE.
      RETURN
      END
C
      SUBROUTINE DIGITAL (DIGIT, INT, IR)
C     +------------------------------------------------------------------------+
C     I RETURNS ONE DIGIT OF AN INTEGER AS A RIGHT-JUSTIFIED EBCDIC WORD       I
C     +------------------------------------------------------------------------+
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2,DIGIT
C
      IF(INT .GT. 9999) INT = 9999
      MODEL = 10**(4-IR)
      MITE = INT/MODEL
      ITEN = MOD(MITE,10)
      IF(ITEN .GT. 0) GO TO 50
      DIGIT = BLANK
      IF(IR .EQ. 4 .OR. MITE .GE. 10) DIGIT = TABLE(1)
      RETURN
   50 DIGIT = TABLE(ITEN+1)
      RETURN
      END
C
      SUBROUTINE FOCUS (K2, L, K, KL, R)
C     +------------------------------------------------------------------------+
C     I COMPUTES TRANSFER MATRICES FOR LINEAR DIPOLES AND QUADRUPOLES          I
C     +------------------------------------------------------------------------+
      REAL K2, L, K, KL, R(4)
C
      K = SQRT(ABS(K2))
      KL = K * L
      IF(K2) 20, 10, 10
   10 R(1) = COS(KL)
      R(3) = - K * SIN(KL)
      R(4) = R(1)
      IF(ABS(KL) .LT. 0.01) GO TO 30
      R(2) = - R(3) / K2
      RETURN
   20 EXPKL = EXP(KL)
      EXIKL = 1.0 / EXPKL
      R(1) = 0.5 * (EXPKL + EXIKL)
      R(3) = 0.5 * (EXPKL - EXIKL) * K
      R(4) = R(1)
      IF(ABS(KL) .LT. 0.01) GO TO 30
      R(2) = - R(3) / K2
      RETURN
   30 R(2) = L * (1.0 - K2 * L ** 2 / 6.0)
      RETURN
      END
C
      SUBROUTINE INITZE
C     +------------------------------------------------------------------------+
C     I CLEARS DATA STORAGE BEFORE SETTING UP SYSTEM                           I
C     +------------------------------------------------------------------------+
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC9/  L, H, N, BDB
      REAL            L, N
      COMMON /BLOC10/ APB(2), LAYL, LAYX, RAB1, RAB2, FACE
      REAL            LAYL, LAYX
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
C
      DO 10 J = 1, 9
   10 ZFLAG(J) = -1.0
      SEC = .FALSE.
      CAP(1) = .FALSE.
      CAP(2) = .FALSE.
      CAP(3) = .FALSE.
      MPA = .FALSE.
      BDB = 0.0
      APB(1) = 0.0
      APB(2) = 0.0
      LAYL = 0.5
      LAYX = 0.0
      RAB1 = 0.0
      RAB2 = 0.0
      RETURN
      END
C
      SUBROUTINE MULTI
C     +------------------------------------------------------------------------+
C     I TREATS MULTIPOLE ABERRATIONS IN QUADRUPOLES                            I
C     +------------------------------------------------------------------------+
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC14/ MMAX, GTOP, DB(20), COSM(20), SINM(20)
C
      DBX = 0.0
      DBY = 0.0
      DBC = 0.0
      DBS = 1.0
      X = RAY(1)
      Y = RAY(3)
      DO 10 NM = 1, MMAX
      IF(DB(NM) .EQ. 0.0) GO TO 5
      DBX = DBX + DB(NM) * (DBC * COSM(NM) - DBS * SINM(NM))
      DBY = DBY + DB(NM) * (DBC * SINM(NM) + DBS * COSM(NM))
    5 DBT = DBC * X + DBS * Y
      DBS = DBS * X - DBC * Y
   10 DBC = DBT
      RAY(2) = RAY(2) - GTOP * DBY
      RAY(4) = RAY(4) + GTOP * DBX
      RETURN
      END
C
      INTEGER FUNCTION NU (TYPE)
C     +------------------------------------------------------------------------+
C     I NUMBER OF DATA ELEMENTS STORED INTERNALLY IN PROGRAM                   I
C     +------------------------------------------------------------------------+
      INTEGER         TYPE
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      INTEGER NO1(21), NO2(4), TYP1
C
      DATA NO1 / 9,9,2,6,4,5,7,0,2,0,0,0,0,8,0,5,0,3,3,3, 2 /
      DATA NO2 / 1,1,1,2 /
C
      IF(SEC .AND. TYPE .EQ. 4) GO TO 200
      IF(TYPE .EQ. 14 .AND. IDATA(I+8) .EQ. 0) GO TO 300
      IF(TYPE .GE. 50) GO TO 100
      IABST = IABS(TYPE)
      NU = NO1(IABST)
      RETURN
  100 TYP1 = TYPE - 49
      IF(TYP1.LE.4) GO TO 110
C=====
      NU = 0
C=====
      RETURN
  110 NU = NO2(TYP1)
      RETURN
  200 NU = 41
      RETURN
  300 NU = 30
      RETURN
      END
C
      SUBROUTINE PRINT1 (LABEL, NWORD, DATA, VARY)
C     +------------------------------------------------------------------------+
C     I PRINTS DATA FOR ONE ELEMENT                                            I
C     +------------------------------------------------------------------------+
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      INTEGER VARY(30), CHAR(12), NV(21), VARK
      REAL    DATA(30)
      DATA NV / 6,1,1,3,2,0,0,6,0,1,0,0,0,6,0,2,0,2,2,1, 1/
C
      NTYPE = DATA(1)
      KTYPE = IABS(NTYPE)
      IF(KTYPE .EQ. 15) GO TO 50
      DO 10 J = 1, 12
   10 CHAR(J) = BLANK
      IF(NTYPE .LE. 0) GO TO 40
      KV = 1
      IF(NTYPE .LE. 21) KV = NV(NTYPE)
      IF(KV .EQ. 0) GO TO 40
      LV = 0
      DO 30 JV = 1, KV
      VARK = VARY(JV+1)
      K = IABS(VARK)
      IF(VARY(JV+1) .GE. 0) GO TO 20
      LV = LV + 1
      CHAR(LV) = MINUS
   20 LV = LV + 1
   30 CHAR(LV) = TABLE(K+1)
   40 IF(NWORD .LE. 1) GO TO 60
      WRITE (NOUT, 940) NTYPE, CHAR, LABEL,
     A                  (BLANK, DATA(J), J = 2, NWORD), SEMI(1)
      RETURN
   50 WRITE (NOUT, 950) NTYPE, LABEL, (DATA(J), J = 2, 4)
      RETURN
   60 WRITE (NOUT, 960) NTYPE, CHAR, LABEL
      RETURN
C
  940 FORMAT(1H0,I4,1H.,12A1,2H ',A4,2H' ,A1,8(F11.5,A1)/
     A       (27X,8(F11.5,A1)))
  950 FORMAT(1H0,I4,1H.,13X,1H',A4,2H' ,F12.5,4H   ',A4,4H'   ,
     A       F12.5,2H ;)
  960 FORMAT(1H0,I4,1H.,12A1,2H ',A4,3H' ;)
      END
C
      SUBROUTINE QUAD
C     +------------------------------------------------------------------------+
C     I TRACKS CHARGED PARTICLES THROUGH A QUADRUPOLE                          I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC15/ LL, KH2, KV2, KH, KV, KHL, KVL, RAY2(6),
     A                RH(4), RV(4)
      REAL LL, KH2, KV2, KH, KV, KHL, KVL
C
      KH2 = DATA(I+2) / P
      KH2 = KH2
      KV2 = - KH2
      CALL FOCUS (KH2, LL, KH, KHL, RH)
      CALL FOCUS (KV2, LL, KV, KVL, RV)
      RAY2(1) = RH(1) * RAY(1) + RH(2) * RAY(2)
      RAY2(2) = RH(3) * RAY(1) + RH(4) * RAY(2)
      RAY2(3) = RV(1) * RAY(3) + RV(2) * RAY(4)
      RAY2(4) = RV(3) * RAY(3) + RV(4) * RAY(4)
      CALL RESET (RAY, RAY2)
      RETURN
      END
C
      LOGICAL FUNCTION QSTOP (LFLAG)
C     +------------------------------------------------------------------------+
C     I RETURNS .TRUE., IF A PARTICLE HITS A QUADRUPOLE APERTURE               I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC11/ QAP(3), ELLIPS, HYPER
      LOGICAL         ELLIPS, HYPER
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
C
      IF(.NOT. CAP(LFLAG+1)) GO TO 30
      IF(ELLIPS) GO TO 10
      IF(HYPER) GO TO 20
      IF(RAY(1)**2 + RAY(3)**2 .GT. DATA(I+3)) GO TO 40
      GO TO 30
   10 IF((RAY(1)/QAP(1))**2 + (RAY(3)/QAP(2))**2 .GT. 1.0) GO TO 40
      IF(.NOT. HYPER) GO TO 30
   20 IF(ABS(RAY(1) * RAY(3)) .GT. QAP(3)) GO TO 40
   30 QSTOP = .FALSE.
      RETURN
   40 QSTOP = .TRUE.
      RETURN
      END
C
      SUBROUTINE RDELMT
C     +------------------------------------------------------------------------+
C     I READS DATA FOR ONE ELEMENT                                             I
C     +------------------------------------------------------------------------+
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC41/ LW, IMAGE(20), FLUSH, INDIC, NTYPE, LABLE, LENGTH,
     A                NWORD, NVARY, DATUM(30), VARY(30)
      INTEGER VARY, TEXT(30),IWORD(1)
      LOGICAL FLUSH
      EQUIVALENCE (TEXT, DATUM)
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM
      INTEGER CARD
      LOGICAL EMPTY
      INTEGER NO1(21), UTABLE(14)
      REAL    CTABLE(14)
      LOGICAL SNTNL, SEPAR
      DATA SNTNL  / .FALSE. /
      DATA NO1    / 8,2,2,4,4,3,7,8,2, 2, 3, 3, 2,8,4,3,1,4,3,2, 2 /
      DATA UTABLE / 2HCM , 1HM  , 2HIN , 2HFT , 2HMM , 1HR  , 2HMR ,
     A              2HPC , 4HP/10, 1HN , 3HMEV, 3HGEV, 2HKG , 1HG   /
      DATA CTABLE / 1.0, 100.0, 2.54, 30.48, 0.1, 1000.0, 1.0, 1.0,
     A              0.1, 100.0, 0.001, 1.0, 1.0, 0.001 /
      DATA IARROW / 1H^ /
C
C     SET DEFAULT VALUES
C
   10 CONTINUE
      DO 20 J = 1, 30
      DATUM(J) = 0.0
   20 VARY (J) = 0
      NWORD = 0
      NVARY = 1
      LABLE = BLANK
C
C     HAS SENTINEL BEEN READ AT PREVIOUS CALL
C
      IF(.NOT. SNTNL) GO TO 30
      SNTNL = .FALSE.
      RETURN
   30 SEPAR = .TRUE.
      CALL RDSKIP
      GO TO 110
C
C     SEPARATORS
C
  100 SEPAR = ITEM .EQ. BLANK
      CALL RDNEXT (-1)
  110 CONTINUE
      DO 115 J = 1, 5
      IF(ITEM .EQ. SEMI(J)) GO TO 500
  115 CONTINUE
      DO 120 J = 1, 6
      IF(ITEM .EQ. QUOTE(J)) GO TO 350
  120 CONTINUE
      IF(ITEM .EQ. TABLE(29)) GO TO 450
      IF(SEPAR) GO TO 150
  130 WRITE (NOUT, 9130) CARD, (BLANK, J = 1, MC), IARROW
      RETURN
  150 IF(NWORD) 300, 200, 300
C
C     TYPE CODE
C
  200 CALL RDFIX (NTYPE, IFLAG)
      IF(IFLAG .NE. 0) GO TO 130
      NWORD = 1
      DATUM(1) = NTYPE
      NTYPE = IABS(NTYPE)
      IF(ITEM .NE. PERIOD) GO TO 100
C
C     VARY CODES
C
  210 CALL RDNEXT (0)
      IFLAG = 0
      IF(ITEM .EQ. MINUS) GO TO 220
      ISIG = 1
      IF(ITEM .EQ. PLUS(1) .OR. ITEM .EQ. PLUS(2)) GO TO 230
      GO TO 240
  220 ISIG = -1
  230 CALL RDNEXT (0)
      IFLAG = 1
  240 CONTINUE
      DO 250 J = 1, 36
      IF(ITEM .EQ. TABLE(J)) GO TO 260
  250 CONTINUE
      IF(IFLAG) 130, 100, 130
  260 IF(NVARY .GE. 30) GO TO 210
      NVARY = NVARY + 1
      VARY(NVARY) = ISIGN(J - 1, ISIG)
      GO TO 210
C
C     DATA VALUE
C
  300 CALL RDFLT (VALUE, IFLAG)
      IF(IFLAG .NE. 0) GO TO 130
      NWORD = NWORD + 1
      IF(NWORD .LE. 30) DATUM(NWORD) = VALUE
      GO TO 100
C
C     LABEL
C
  350 CALL RDSTRG (IWORD, 1, L)
      IF(L .GT. 1) WRITE (NOUT, 9350)
      SEPAR = .TRUE.
      IF(NWORD .EQ. 2 .AND. NTYPE .EQ. 15) GO TO 360
      IF(LABLE .NE. BLANK) WRITE (NOUT, 9360) LABLE
      LABLE = IWORD(1)
      GO TO 110
  360 TEXT(3) = IWORD(1)
      NWORD = 3
      GO TO 110
C
C     SENTINEL
C
  450 EMPTY = .TRUE.
      IF(NWORD .EQ. 0) RETURN
      SNTNL = .TRUE.
      GO TO 502
C
C     CHECK VALIDITY OF ELEMENT JUST READ
C
  500 IF(NWORD .EQ. 0) GO TO 130
      CALL RDNEXT (1)
  502 IF(NTYPE .EQ.  0) GO TO 510
      IF(NTYPE .LE. 21) GO TO 530
      IF(NTYPE .LT. 50) GO TO 510
      IF(NTYPE .LE. 53) GO TO 540
      IF(NTYPE .EQ. 60) GO TO 545
  510 WRITE (NOUT, 9510)
      FLUSH = .TRUE.
      GO TO 700
  530 LENGTH = NO1(NTYPE)
      IF(NTYPE .NE. 16) GO TO 535
      IF(DATUM(2).EQ. 9) LENGTH=6
      IF(DATUM(2).EQ.14) LENGTH=6
      IF(DATUM(2) .GE. 0.0 .AND. DATUM(2) .LT. 99.5) GO TO 535
      LENGTH = 4
      IF(DATUM(2) .GE. 199.5) LENGTH = 2
  535 IF(NWORD - LENGTH) 600, 700, 550
  540 LENGTH = 5
      GO TO 546
  545 LENGTH = 8
  546 IF(NTYPE .EQ. 53) LENGTH = 1
      IF(NWORD - LENGTH) 600, 700, 550
C
C     DATA OVERFLOW
C
  550 IF(NTYPE .NE. 6) GO TO 555
      IF(DATUM(4) .NE. 0.0) LENGTH = 5
      IF(NWORD - LENGTH) 600, 700, 560
  555 IF(NTYPE .EQ.  1) LENGTH = 9
      IF(NTYPE .EQ. 14) LENGTH = 30
      IF(NWORD - LENGTH) 600, 700, 560
  560 WRITE (NOUT, 9560)
      GO TO 690
C
C     FILL IN INCOMPLETE 15 ELEMENT
C
  600 IF(INDIC .NE.  0) GO TO 700
      IF(NTYPE .NE. 15) GO TO 690
      IF(NWORD - 2) 620, 610, 630
  610 IF(DATUM(2) .NE. 0.0) GO TO 650
  620 TEXT(3) = BLANK
      GO TO 690
  630 CONTINUE
      DO 640 J = 1, 14
      IF(TEXT(3) .EQ. UTABLE(J)) GO TO 660
  640 CONTINUE
  650 WRITE (NOUT, 9650)
      FLUSH = .TRUE.
      GO TO 700
  660 DATUM(4) = CTABLE(J)
      IF(DATUM(2) .GT. 6.0 .AND. J .LT. 6) DATUM(4) = 0.01 * DATUM(4)
  690 NWORD = LENGTH
C
C     PRINT OUT
C
  700 CALL PRINT1 (LABLE, NWORD, DATUM, VARY)
      IF(FLUSH) GO TO 10
      RETURN
C
 9130 FORMAT(52H0SCANNING STOPS DUE TO ERROR AT POSITION SHOWN BELOW/
     A       11X,80A1/10X,81A1)
 9350 FORMAT(33H0NEXT LABEL TRUNCATED TO 4 CHARS.)
 9360 FORMAT( 8H0LABEL ',A4,33H' ON NEXT ELEMENT WAS OVERWRITTEN)
 9510 FORMAT(38H0NEXT ELEMENT IS ILLEGAL - RUN FLUSHED)
 9560 FORMAT(39H0DATA LIST FOR NEXT ELEMENT IS TOO LONG)
 9650 FORMAT(31H0ERROR ON FOLLOWING 15. ELEMENT)
      END
C
      SUBROUTINE RDFIX (IVALUE, IFLAG)
C     +------------------------------------------------------------------------+
C     I READS ONE INTEGER                                                      I
C     +------------------------------------------------------------------------+
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM
      INTEGER CARD
      LOGICAL EMPTY
C
      IFLAG = -1
      IVAL = 0
      IF(ITEM .EQ. MINUS) GO TO 10
      ISIG = 1
      IF(ITEM .EQ. PLUS(1) .OR. ITEM .EQ. PLUS(2)) GO TO 20
      GO TO 30
   10 ISIG = -1
   20 CALL RDNEXT (0)
   30 CONTINUE
      DO 40 J = 1, 10
      IF(ITEM .EQ. TABLE(J)) GO TO 50
   40 CONTINUE
      IVALUE = ISIGN (IVAL, ISIG)
      RETURN
   50 IVAL = 10 * IVAL + J - 1
      IFLAG = 0
      GO TO 20
      END
C
      SUBROUTINE RDFLT (VALUE, IFLAG)
C     +------------------------------------------------------------------------+
C     I READS ONE FLOATING-POINT NUMBER                                        I
C     +------------------------------------------------------------------------+
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM
      INTEGER CARD
      LOGICAL EMPTY
C
      IFLAG = -1
      VAL = 0.0
      NPL = 0
      JPL = 0
      NEX = 0
      IF(ITEM .EQ. MINUS) GO TO 10
      SIG =  1.0
      IF(ITEM .EQ. PLUS(1) .OR. ITEM .EQ. PLUS(2)) GO TO 20
      GO TO 30
   10 SIG = -1.0
   20 CALL RDNEXT (0)
   30 CONTINUE
      DO 40 J = 1, 10
      IF(ITEM .EQ. TABLE(J)) GO TO 50
   40 CONTINUE
      IF(ITEM .NE. PERIOD) GO TO 70
      IF(JPL .NE. 0) GO TO 60
      JPL = 1
      FF = 0.1
      GO TO 20
   50 IFLAG = 0
      IF(JPL .NE. 0) GO TO 55
      VAL = 10.0 * VAL + FLOAT(J - 1)
      GO TO 20
   55 VAL = VAL + FF * FLOAT(J - 1)
      FF = 0.1 * FF
      GO TO 20
   60 IFLAG = 1
      GO TO 90
   70 IF(ITEM .NE. TABLE(15)) GO TO 80
      CALL RDNEXT (0)
      CALL RDFIX (NEX, IFLAG)
      GO TO 90
   80 IF(ITEM .EQ. PLUS(1) .OR. ITEM .EQ. PLUS(2) .OR. ITEM .EQ. MINUS)
     A       CALL RDFIX (NEX, IFLAG)
   90 VALUE = SIGN (VAL, SIG)
      IF(NEX .NE. 0) VALUE = VALUE * 10.0 ** NEX
      RETURN
      END
C
      SUBROUTINE RDNEXT (ISKIP)
C     +------------------------------------------------------------------------+
C     I DELIVERS THE NEXT INPUT CHARACTER                                      I
C     +------------------------------------------------------------------------+
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM
      INTEGER CARD
      LOGICAL EMPTY
C
      IF(ISKIP .LT. 0) GO TO 40
      IF(ISKIP .GE. 2) GO TO 20
      IF(EMPTY) GO TO 20
   10 IF(MC .LT. 80) GO TO 30
      IF(ISKIP .NE. 0) GO TO 20
      EMPTY = .TRUE.
      ITEM = BLANK
      RETURN
   20 MC = 0
      EMPTY = .FALSE.
      READ (NIN, 100) CARD
      NCD = NCD + 1
   30 MC = MC + 1
      ITEM = CARD(MC)
      IF(ISKIP .EQ. 0) RETURN
   40 IF(ITEM .EQ. BLANK) GO TO 10
      IF(ITEM .EQ. TABLE(29) .AND. ISKIP .EQ. 2) STOP
      RETURN
  100 FORMAT(80A1)
      END
C
      SUBROUTINE RDPACK (CHAR, TEXT, N)
C     +------------------------------------------------------------------------+
C     I PACKS UP TO 4 CHARACTERS INTO ONE MACHINE WORD                         I
C     +------------------------------------------------------------------------+
C
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      INTEGER CHAR(4), TEXT
C
      TEXT = BLANK
      IF(N .LE. 0) RETURN
      CALL UBUNCH (CHAR(1), TEXT, N)
      RETURN
      END
C
      SUBROUTINE RDSKIP
C     +------------------------------------------------------------------------+
C     I SKIPS COMMENTS ON INPUT                                                I
C     +------------------------------------------------------------------------+
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM
      INTEGER CARD
      LOGICAL EMPTY
      INTEGER LINE(20)
C
   10 IF(ITEM .NE. PAR1(1) .AND. ITEM .NE. PAR1(2)) RETURN
      CALL RDSTRG (LINE, 20, L)
      IF(L .GT. 20) WRITE (NOUT, 100)
      WRITE (NOUT, 110) LINE
      GO TO 10
  100 FORMAT(36H0NEXT COMMENT TRUNCATED TO 80 CHARS.)
  110 FORMAT( 2H0(,20A4,1H))
      END
C
      SUBROUTINE RDSTRG (STRING, LMAX, L)
C     +------------------------------------------------------------------------+
C     I READS A CHARACTER STRING                                               I
C     +------------------------------------------------------------------------+
C
      COMMON /BLOC42/ TABLE(36), PLUS(2), MINUS, BLANK, PERIOD,
     A                SEMI(5), QUOTE(6), PAR1(2), PAR2(2)
      INTEGER TABLE, PLUS, BLANK, PERIOD, SEMI, QUOTE, PAR1, PAR2
      COMMON /BLOC43/ NCD, CARD(80), MC, EMPTY, ITEM
      INTEGER CARD
      LOGICAL EMPTY
      INTEGER STRING(LMAX), CHAR(4)
C
      DO 10 L = 1, LMAX
   10 STRING(L) = BLANK
      L = 0
      DO 12 J = 1, 2
      IF(ITEM .EQ. PAR1(J)) GO TO 20
   12 CONTINUE
      DO 14 J = 1, 6
      IF(ITEM .EQ. QUOTE(J)) GO TO 16
   14 CONTINUE
      RETURN
   16 ISTOP = QUOTE(J)
      GO TO 30
   20 ISTOP = PAR2(J)
   30 ISKIP = 1
   40 IC = 0
   50 CALL RDNEXT (ISKIP)
      IF(ITEM .EQ. ISTOP) GO TO 60
      ISKIP = 0
      IF(ITEM .EQ. BLANK .OR. LMAX .EQ. 1) ISKIP = 1
      IC = IC + 1
      CHAR(IC) = ITEM
      IF(IC - 4) 50, 70, 70
   60 IF(IC .EQ. 0) GO TO 80
   70 L = L + 1
      IF(L .LE. LMAX) CALL RDPACK (CHAR, STRING(L), IC)
      IF(ITEM .NE. ISTOP) GO TO 40
   80 CALL RDNEXT (1)
      RETURN
      END
C
      SUBROUTINE REPEAT
C     +------------------------------------------------------------------------+
C     I KEEPS TRACK OF TYPE CODE 9 (REPEAT ELEMENT)                            I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC17/ IP, IC(4), IS(4)
C
      IF(IDATA(I+1) .NE. 0) GO TO 1
      IC(IP) = IC(IP) - 1
      IF(IC(IP) .EQ. 0) GO TO 2
      I = IS(IP)
      RETURN
    2 IP = IP-1
      RETURN
    1 IP = IP+1
      IC(IP) = IDATA(I+1)
      IS(IP) = I
      RETURN
      END
C
      SUBROUTINE RESET (A,B)
C     +------------------------------------------------------------------------+
C     I COPIES RAY B INTO RAY A                                                I
C     +------------------------------------------------------------------------+
      DIMENSION A(6), B(6)
C
      DO 100 I = 1, 4
 100  A(I) = B(I)
      RETURN
      END
C
      SUBROUTINE SETUP
C     +------------------------------------------------------------------------+
C     I DIRECTS READING OF DATA AND PREPROCESSES IT FOR USE IN RAY TRACING     I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC2/  UNIT(11), NAME(11), NOM(11), NOM1(4)
      COMMON /BLOC3/  NIN, NOUT, NOL
      COMMON /BLOC4/  RAYMAX(6), PBEAM, P0, NORAYS
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC6/  NHISTS, NHIST, LIMNO
      COMMON /BLOC7/  MTYPE(100), NENTRY(100), NCOOR(100), INTVLS(100),
     A                BEGIN(100), END(100), STEP(100), ZHIST(100)
      COMMON /BLOC8/  MTABLE(10000)
      COMMON /BLOC9/  L, H, N, BDB
      REAL            L, N
      COMMON /BLOC10/ APB(2), LAYL, LAYX, RAB1, RAB2, FACE
      REAL            LAYL, LAYX
      COMMON /BLOC11/ QAP(3), ELLIPS, HYPER
      LOGICAL         ELLIPS, HYPER
      COMMON /BLOC12/ VALUE(100), XMOM(100), XMOM2(100), NFLAG(100),
     A                SET(100), KFLAG(100), IFLAG(3,9), ZFLAG(9)
      LOGICAL SET, IFLAG
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC16/ KPART(3), ISTOP(3,500)
      COMMON /BLOC18/ LOSS, NBLK(10), KFLG(10),
     A                XSTRT(10), XEND(10), LTHX(10), XBIN(10), NUNX(10),
     A                YSTRT(10), YEND(10), LTHY(10), YBIN(10), NUNY(10)
      COMMON /BLOC41/ LW, IMAGE(20), FLUSH, INDIC, NTYPE, LABLE, LENGTH,
     A                NWORD, NVARY, DATUM(30), VARY(30)
      INTEGER VARY, TEXT(30)
      LOGICAL FLUSH
      EQUIVALENCE (TEXT, DATUM)
      INTEGER         TYPE
      LOGICAL         LEGAL
      REAL            UORIG(11), ZL(4), WORK(30)
      INTEGER         ICC(4), NORIG(11)
      EQUIVALENCE (TYPEC, WORK, DATUM), (TYPE, NTYPE), (NFL, VARY(2))
      DATA NORIG / 4HCM  , 4HMR  , 4HCM  , 4HMR  , 4HCM  , 4HPC  ,
     A             4HDEG , 4HM   , 4HKG  , 4HGEVA, 4HGEVC /
      DATA UORIG / 0.01, 0.001, 0.01, 0.001, 0.01, 0.01, 0.01745329,
     A             1.0, 1.0, 1.0, 1.0 /
      DATA IRAYS / 4HRAYS /
      DATA IFACE /-10/, INEXT /-10/
C
C     READ TITLE
C
   10 CALL RDNEXT (2)
      CALL RDSKIP
      CALL RDSTRG (IMAGE, 20, LW)
      WRITE (NOUT, 9000) IMAGE
      CALL RDSKIP
      CALL RDFIX (NORAYS, IFLG)
      CALL RDNEXT (-1)
      WRITE (NOUT, 9005) NORAYS
      INDIC = 0
 9000 FORMAT(1H1//1X,20A4)
 9005 FORMAT('0NUMBER OF RAYS',I8)
C
C     READ DATA
C
      DO 50 ISBK = 1, 3001
   50 DATA(ISBK) = 0.0
      I = 1
      NHISTS = 0
      LIMNO = 0
      ZC = 0.0
      DKFLAG = .FALSE.
      LOSS = 0
      DO 55 J = 1, 3
   55 KPART(J) = IRAYS
      ZMAX = 0.0
      IP = 0
      NEL = 0
      FLUSH  = .FALSE.
      DO 60 J = 1, 11
      NAME(J) = NORIG(J)
   60 UNIT(J) = UORIG(J)
  100 CALL RDELMT
      IF(NWORD .EQ. 0) GO TO 600
      IF(FLUSH) GO TO 100
      IF(I + NU(NTYPE) .LE. 3001) GO TO 200
      WRITE(NOUT, 1000) NEL, I
 1000 FORMAT(21H0DATA OVERFLOW, NEL =,I4,6H   I =,I6)
      FLUSH = .TRUE.
      GO TO 100
  200 IF(TYPEC .LT. 0.0) GO TO 100
      IF(TYPE .EQ. 60) GO TO 550
      IF(TYPE .EQ. 53) GO TO 480
      IF(TYPE .GE. 50) GO TO 450
      GO TO (210,220,230,240,250,260,270,280,290,300,
     A       310,320,330,340,350,360,370,380,390,400,
     B       410), TYPE
C
C     BEAM
C
  210 IF (NWORD .GE. 9) GO TO 212
      PBEAM = WORK(8) * UNIT(11)
      P0 = PBEAM
      DO 211 IB = 1, 6
  211 RAYMAX(IB) = WORK(IB+1)*UNIT(IB)
      GO TO 100
  212 IDATA(I) = TYPE
      DO 213 IB = 1, 6
  213 DATA(I+IB) = WORK(IB+1)*UNIT(IB)
      DATA(I+7) = WORK(8)*UNIT(11)
      IDATA(I+8) = WORK(9) / 100. + .001
      GO TO 500
C
C     MAGNET POLE FACE ROTATION
C
  220 IDATA(I) = TYPE
      FACE = WORK(2) * UNIT(7)
      TANB = TAN(FACE)
      SECB = 1.0 / COS(FACE)
      TCOR = 2.0 * APB(2) * LAYL
      SB = SECB * (1.0 + 2.0 * TANB ** 2)
      IF (I .EQ. INEXT) GO TO 221
      IFACE = I
      GO TO 500
C
C     FRINGE FIELD AT MAGNET EXIT.
C
  221 DATA(I+1) = - H * P0
      DATA(I+2) = - TANB
      DATA(I+3) = SECB
      DATA(I+4) = N * H * TANB - 0.5 * RAB2 * SECB ** 3
      DATA(I+5) = TCOR * SB * (1.0 - H * LAYX * TCOR * TANB)
      DATA(I+6) = - 0.5 * TANB ** 3
      DATA(I+7) = DATA(I+6)
      DATA(I+8) = - TANB * SECB ** 2
      INEXT = - 10
      GO TO 500
C
C     DRIFT SPACE
C
  230 IDATA(I) = TYPE
      L = WORK(2)*UNIT(8)
      DATA(I+1) = L
      GO TO 490
C
C     BENDING MAGNET

C
  240 IDATA(I) = TYPE
      L = WORK(2)*UNIT(8)
      H = WORK(3)*UNIT(9)/(33.356*P0)
      N = WORK(4)
      IF(I .NE. IFACE + NU(2)) GO TO 245
C
C     FRINGE FIELD AT MAGNET ENTRANCE.
C
      DATA(IFACE+1) = H * P0
      DATA(IFACE+2) = TANB
      DATA(IFACE+3) = SECB
      DATA(IFACE+4) = 0.5 * RAB1 * SECB ** 3 - N * H * TANB
      DATA(IFACE+5) = TCOR * SB * (1.0 - H * LAYX * TCOR * TANB)
      DATA(IFACE+6) = 0.0
      DATA(IFACE+7) = TANB * (0.5 + TANB ** 2)
      DATA(IFACE+8) = 0.0
  245 DATA(I+1) = L
      DATA(I+2) = H
      DATA(I+3) = N
      DATA(I+4) = 0.0
      DATA(I+5) = 0.0
      INEXT = I + NU(4)
      IF(DATA(I+2) .EQ. 0.0) GO TO 490
      DATA(I+4) = 1.0 / DATA(I+2)
      IF(SEC) DATA(I+5) = BDB * DATA(I+4) ** 2
      GO TO 490
C
C     QUADRUPOLE
C
  250 IDATA(I) = TYPE
      L = WORK(2)*UNIT(8)
      DATA(I+1) = L
      DATA(I+2) = WORK(3)*UNIT(9)/(WORK(4)*UNIT(1)*33.356)
      DATA(I+3) = (WORK(4) * UNIT(1)) ** 2
      GO TO 490
C
C     SLIT
C
  260 IDATA(I) = TYPE
      IFF = WORK(2) + .001
      IDATA(I+1) = IFF
      IUN = MOD(IFF,100)
      IF(IUN .LE. 0 .OR. IUN .GT. 6) GO TO 100
      DATA(I+2) = WORK(3) * UNIT(IUN)
      IFG = WORK(4) + .001
      IUN = MOD(IFG, 100)
      IF(IUN .LT. 0 .OR. IUN .GT. 6) GO TO 100
      IDATA(I+3) = IUN
      DATA(I+4) = 0.0
      IF(IUN .NE. 0) DATA(I+4) = WORK(5) * UNIT(IUN)
      GO TO 500
C
C     DISPLACEMENT OF RAY
C
  270 IDATA(I) = TYPE
      DO 271 IB = 1, 6
  271 DATA(IB+I) = WORK(IB+1)*UNIT(IB)
      GO TO 500
C
C     MISALIGNMENTS
C
  280 WRITE (NOUT,1001)
 1001 FORMAT('0THIS PROGRAM WILL NOT DO MISALIGNMENTS')
      STOP
C
C     REPEAT
C
  290 IDATA(I) = TYPE
      IDATA(I+1) = WORK(2) + .001
      IF (IDATA(I+1) .EQ. 0) GO TO 291
      IP = IP + 1
      ICC(IP) = IDATA(I+1)
      ZL(IP) = ZC
      GO TO 500
  291 ZC = ZC + FLOAT(ICC(IP) - 1)*(ZC - ZL(IP))
      IP = IP - 1
      GO TO 500
C
C     CONSTRAINTS
C
  300 GO TO 100
C
C     ACCELERATOR
C
  310 GO TO 100
C
C     BEAM ROTATED ELLIPSE
C
  320 GO TO 100
C
C     INPUT OUTPUT OPTIONS
C
  330 KODE = WORK(2) + .001
      KFL = KODE / 100
      INDEX = KODE - 100 * KFL
      IF(INDEX .NE. 10) GO TO 100
      CAP(KFL+1) = .TRUE.
      GO TO 100
C
C     ARBITRARY MATRIX
C
  340 IDATA(I) = TYPE
      NROW = WORK(8) + .001
      DO 341 IB = 1, 6
  341 DATA(I+IB) = WORK(IB+1)*UNIT(NROW)/UNIT(IB)
      IDATA(I+7) = NROW
      IF (SEC .AND. NWORD .GT. 8) GO TO 342
      IDATA(I+8) = 1
      GO TO 500
  342 IDATA(I+8) = 0
      IPL = 9
      DO 343 IB = 1, 6
      DO 343 IC = IB, 6
      IPL = IPL + 1
      IST = IPL + I - 1
  343 DATA(IST) = WORK(IPL)*UNIT(NROW)/(UNIT(IB)*UNIT(IC))
      GO TO 500
C
C     UNITS
C
  350 NUN = WORK(2) + .001
      IF(NUN .EQ. 0) GO TO 355
      NAME(NUN) = TEXT(3)
      UNIT(NUN) = WORK(4) * UORIG(NUN)
      IF(NUN .GT. 2) GO TO 100
      UNIT(NUN+2) = UNIT(NUN)
      NAME(NUN+2) = NAME(NUN)
      GO TO 100
  355 CONTINUE
      DO 356 J = 1, 11
      NAME(J) = NORIG(J)
  356 UNIT(J) = UORIG(J)
      GO TO 100
C
C     MULTIPOLE ABERRATIONS IN QUADS AND BENDING MAGNET PARAMETERS
C
  360 IDATA(I) = TYPE
      NM = ABS(WORK(2)) + .001
      IF (WORK(2) .GT. 0.0) GO TO 361
      IF (NM .LE. 20) GO TO 3601
      WRITE (NOUT,1010)
 1010 FORMAT('0INDEX OF MULTIPOLE MAY NOT EXCEED 20')
      STOP
 3601 MPA = .TRUE.
      IDATA(I+1) = - NM
      DATA(I+2) = WORK(3)/UNIT(1)**(NM-2)
      ANGLE = WORK(4)/57.29578
      DATA(I+3) = COS(ANGLE)
      DATA(I+4) = SIN(ANGLE)
      GO TO 500
  361 IF (NM .EQ. 1) GO TO 362
      IF (NM .EQ. 4 .OR. NM .EQ. 5) GO TO 363
      IF (NM .EQ. 6) GO TO 3635
      IF (NM .EQ. 7) GO TO 364
      IF (NM .EQ. 8) GO TO 365
      IF (NM .EQ. 9) GO TO 3655
      IF (NM .EQ. 11) GO TO 3657
      IF (NM .EQ. 12) GO TO 366
      IF (NM .EQ. 13) GO TO 367
      IF (NM .EQ. 100) GO TO 368
      IF(NM .EQ. 101) GO TO 369
      IF(NM .GE. 200) GO TO 3695
      GO TO 100
  362 BDB = WORK(3)/UNIT(1)**2
      GO TO 100
  363 APB(NM-3) = WORK(3)*UNIT(2*NM-7)
      IDATA(I+1) = NM
      DATA(I+2) = APB(NM-3)
      GO TO 500
 3635 ZC = WORK(3) * UNIT(8)
      GO TO 100
  364 LAYL = WORK(3)
      GO TO 100
  365 LAYX = WORK(3)
      GO TO 100
 3655 ZMAX = WORK(3) * UNIT(8)
      GO TO 100
 3657 P0 = WORK(3) * UNIT(11)
      IDATA(I+1) = NM
      DATA(I+2) = P0
      GO TO 500
  366 RAB1 = WORK(3)/UNIT(8)
      GO TO 100
  367 RAB2 = WORK(3)/UNIT(8)
      GO TO 100
  368 IDATA(I+1) = NM
      DATA(I+2) = WORK(3)*UNIT(1)
      DATA(I+3) = WORK(4)*UNIT(3)
      GO TO 500
  369 IDATA(I+1) = NM
      DATA(I+2) = 0.5 * (WORK(3) * UNIT(1)) ** 2
      GO TO 500
 3695 KPART(NM-199) = LABLE
      GO TO 100
C
C     SECOND ORDER
C
  370 SEC = .TRUE.
      GO TO 500
C
C     SEXTUPOLE
C
  380 IDATA(I) = TYPE
      L = WORK(2)*UNIT(8)
      DATA(I+1) = L
      DATA(I+2) = WORK(3)*UNIT(9)/((WORK(4)*UNIT(1))**2*33.356)
      GO TO 490
C
C     SOLENOID
C
  390 IDATA(I) = TYPE
      L = WORK(2) * UNIT(8)
      DATA(I+1) = L
      DATA(I+2) = 0.5 * WORK(3) * UNIT(9) / 33.356
      GO TO 490
C
C     BEAM ROTATION
C
  400 IDATA(I) = TYPE
      ANGLE = WORK(2) * UNIT(7)
      DATA(I+1) = COS(ANGLE)
      DATA(I+2) = SIN(ANGLE)
      GO TO 500
C
C     THIN FOIL
c
  410 idata(i) = type
      data(i+1) = work(2) * unit(2)
      go to 500
C
C     SET UP HISTOGRAM
C
  450 KODE = WORK(2) + .001
      KFL = KODE / 100
      NUN = KODE - 100 * KFL
      CALL HSTUN (NUN, FACT, LEGAL)
      IF(.NOT. LEGAL) GO TO 100
      M = LIMNO + 1
      WORK(3) = WORK(3) * FACT
      WORK(4) = WORK(4) * FACT
      WORK(5) = WORK(5) * FACT
      IF(WORK(5) .EQ. 0.0) WORK(5) = (WORK(4) - WORK(3)) / 100.0
      IF(WORK(5) .EQ. 0.0) WORK(5) = 0.001
      INTVL = AMAX1((WORK(4) - WORK(3)) / WORK(5), 1.0) + 0.001
      NINNY = TYPE - 49
      GO TO (452, 454, 456), NINNY
C
C     ONE DIMENSIONAL HISTOGRAM
C
  452 LIM = LIMNO + INTVL + 3
      IF(LIM .GT. 10000) GO TO 470
      LIMNO = LIM
      IF(NUN .NE. 8) GO TO 460
C
C     Z HISTOGRAM OF LOSSES
C
      LOSS = LOSS + 1
      XSTRT(LOSS) = WORK(3)
      XEND (LOSS) = WORK(4)
      LTHX (LOSS) = INTVL
      XBIN (LOSS) = WORK(5)
      NUNX (LOSS) = 8
      NUNY (LOSS) = 0
      NBLK (LOSS) = M
      KFLG (LOSS) = KFL
      GO TO 100
C
C     SET X SCALE (HORIZONTAL)
C
  454 ASTRT = WORK(3)
      AEND  = WORK(4)
      NA    = MIN0 (INTVL, 100)
      DA    = (WORK(4) - WORK(3)) / FLOAT(NA)
      NUNA = NUN
      IF(NUN - 8) 460, 100, 460
C
C     Y SCALE (VERTICAL)
C
  456 LIM = LIMNO + (NA + 1) * (INTVL + 1) + 5
      IF(LIM .GT. 10000) GO TO 470
      LIMNO = LIM
      IF(NUN .NE. 8 .AND. NUNA .NE. 8) GO TO 460
C
C     TWO DIMENSIONAL LOSS HISTOGRAM
C
      LOSS = LOSS + 1
      XSTRT(LOSS) = ASTRT
      XEND (LOSS) = AEND
      LTHX (LOSS) = NA
      XBIN (LOSS) = DA
      NUNX (LOSS) = NUNA
      YSTRT(LOSS) = WORK(3)
      YEND (LOSS) = WORK(4)
      LTHY (LOSS) = INTVL
      YBIN (LOSS) = WORK(5)
      NUNY (LOSS) = NUN
      NBLK (LOSS) = M
      KFLG (LOSS) = KFL
      GO TO 100
C
C     STORE HISTOGRAM DATA TO DATA ARRAY
C
  460 IDATA(I) = 50
      NHISTS = NHISTS + 1
      MTYPE (NHISTS) = NINNY
      NENTRY(NHISTS) = M
      NCOOR (NHISTS) = NUN
      BEGIN (NHISTS) = WORK(3)
      END   (NHISTS) = WORK(4)
      STEP  (NHISTS) = WORK(5)
      INTVLS(NHISTS) = INTVL
      ZHIST (NHISTS) = ZC
      NFLAG (NHISTS) = NFL
      KFLAG (NHISTS) = KFL
      GO TO 500
C
C     HISTOGRAM SPACE OVERFLOW
C
  470 WRITE (NOUT, 1470)
      GO TO 100
 1470 FORMAT('0THE HISTOGRAM SPECIFIED ABOVE CAUSED A STORAGE OVERFLOW,'
     A       ' IT HAS BEEN IGNORED.')
C
C     FLAG FOR HISTOGRAM ENTRY
C
  480 IDATA(I) = TYPE
      IDATA(I+1) = NFL
      ZFLAG(NFL) = ZC
      GO TO 500
C
C     ACCUMULATE LENGTH AND DATA POINTER
C
  490 ZC = ZC + L
  500 I = I + NU(TYPE)
      ZZC = ZC / UNIT(8)
      WRITE (NOUT,1234) ZZC, I
 1234 FORMAT(1H+,110X,F8.2,2X,I4)
      GO TO 100
C
C     PREPARE FOR DECAY CALCULATION
C
  550 DKFLAG = .TRUE.
      SEC = .TRUE.
      CALL DECAYP
      GO TO 100
C
C     END OF INPUT DATA
C
  600 IF(FLUSH) GO TO 10
      I1 = I - 1
      WRITE (NOUT, 1103)
 1103 FORMAT('0SENTINEL')
      RETURN
      END
C
      SUBROUTINE SEXT
C     +------------------------------------------------------------------------+
C     I TRACKS CHARGED PARTICLES THROUGH A SEXTUPOLE                           I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC5/  SEC, CAP(3), MPA
      LOGICAL         SEC, CAP, MPA
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC15/ LL, KH2, KV2, KH, KV, KHL, KVL, RAY2(6),
     A                RH(4), RV(4)
      REAL LL, KH2, KV2, KH, KV, KHL, KVL
C
      RAY2(1) = RAY(1) + LL * RAY(2)
      RAY2(2) = RAY(2)
      RAY2(3) = RAY(3) + LL * RAY(4)
      RAY2(4) = RAY(4)
      IF(.NOT. SEC) GO TO 10
      C = LL * DATA(I+2) / P
      U = RAY(1) ** 2 - RAY(3) ** 2
      UP = LL * (RAY(1) * RAY(2) - RAY(3) * RAY(4))
      UPP = LL ** 2 * (RAY(2) ** 2 - RAY(4) ** 2)
      RAY2(1) = RAY2(1) - C * (0.5 * U + UP / 3.0 + UPP / 12.0) * LL
      RAY2(2) = RAY2(2) - C * (U + UP + UPP / 3.0)
      U = RAY(1) * RAY(3)
      UP = LL * (RAY(1) * RAY(4) + RAY(2) * RAY(3))
      UPP = LL ** 2 * RAY(2) * RAY(4)
      RAY2(3) = RAY2(3) + C * (U + UP / 3.0 + UPP / 6.0) * LL
      RAY2(4) = RAY2(4) + C * (U + U + UP + UPP / 1.5)
   10 CALL RESET (RAY, RAY2)
      RETURN
      END
C
      SUBROUTINE SOLO
C     +------------------------------------------------------------------------+
C     I TRACKS CHARGED PARTICLES THROUGH A SOLENOID                            I
C     +------------------------------------------------------------------------+
      COMMON /BLOC1/  DATA(3001), I, I1
      INTEGER         IDATA(3001)
      EQUIVALENCE     (IDATA, DATA)
      COMMON /BLOC13/ RAY(6), RAYC(6), RAYN(6), P, PC, PN, FLD, MASS,
     A                MASSC, MASSN, FC, FN, PSTAR, ZMAX, DKFLAG, Z
      REAL MASS, MASSC, MASSN
      LOGICAL DKFLAG
      COMMON /BLOC15/ LL, KH2, KV2, KH, KV, KHL, KVL, RAY2(6),
     A                RH(4), RV(4)
      REAL LL, KH2, KV2, KH, KV, KHL, KVL
C
      KH = DATA(I+2) / P
      KHL = LL * KH
      C = COS(KHL)
      S = SIN(KHL)
      IF(KHL .LT. 0.01) GO TO 10
      SOK = S / KH
      GO TO 20
   10 SOK = LL * (1.0 - (KH * LL) ** 2 / 6.0)
   20 SK = S * KH
      RAY2(1) = C * RAY(1) + SOK * RAY(2)
      RAY2(2) = - SK * RAY(1) + C * RAY(2)
      RAY2(3) = C * RAY(3) + SOK * RAY(4)
      RAY2(4) = - SK * RAY(3) + C * RAY(4)
      RAY(1) = C * RAY2(1) + S * RAY2(3)
      RAY(3) = - S * RAY2(1) + C * RAY2(3)
      RAY(2) = C * RAY2(2) + S * RAY2(4)
      RAY(4) = - S * RAY2(2) + C * RAY2(4)
      RETURN
      END
C
      REAL FUNCTION RANF(X)
      DOUBLE PRECISION    DRANF,    G900GT,   G900ST
      DOUBLE PRECISION    DS(2),    DM(2),    DSEED
      DOUBLE PRECISION    DX24,     DX48
      DOUBLE PRECISION    DL,       DC,       DU,       DR
      LOGICAL             SINGLE
      DATA      DS     /  1665 1885.D0, 286 8876.D0  /
      DATA      DM     /  1518 4245.D0, 265 1554.D0  /
      DATA      DX24   /  1677 7216.D0  /
      DATA      DX48   /  281 4749 7671 0656.D0  /
      SINGLE  =  .TRUE.
      GOTO 10
      ENTRY DRANF()
      SINGLE  =  .FALSE.
  10  DL  =  DS(1) * DM(1)
      DC  =  DINT(DL/DX24)
      DL  =  DL - DC*DX24
      DU  =  DS(1)*DM(2) + DS(2)*DM(1) + DC
      DS(2)  =  DU - DINT(DU/DX24)*DX24
      DS(1)  =  DL
      DR     =  (DS(2)*DX24 + DS(1)) / DX48
      IF(SINGLE) THEN
         RANF  =  SNGL(DR)
      ELSE
         DRANF  =  DR
      ENDIF
      RETURN
      ENTRY G900GT()
      G900GT  =  DS(2)*DX24 + DS(1)
      RETURN
      ENTRY G900ST(DSEED)
      DS(2)  =  DINT(DSEED/DX24)
      DS(1)  =  DSEED - DS(2)*DX24
      G900ST =  DS(1)
      RETURN
      END
C
      SUBROUTINE UBUNCH (MS,MT,NCHP)
      DIMENSION MS(99), MT(99), NCHP(9)
      COMMON /BLOC3/  NIN, NOUT, NOL
      data iblan1/538976288/
      data mask1/255/
      NCH = NCHP(1)
      IF (NCH) 91,39,11
   11 NWT = ISHFT (NCH,-2)
      NTRAIL = IAND (NCH,3)
      JS = 0
      IF (NWT.EQ.0) GO TO 31
      DO 24 JT=1,NWT
      MT(JT) = IOR (IOR (IOR (
     + IAND(MS(JS+1),MASK1),
     + ISHFT (IAND(MS(JS+2),MASK1), 8)),
     + ISHFT (IAND(MS(JS+3),MASK1),16)),
     + ISHFT (MS(JS+4), 24) )
   24 JS = JS + 4
      IF (NTRAIL.EQ.0) RETURN
   31 MWD = IBLAN1
      JS = NCH
      DO 34 JT=1,NTRAIL
      MWD = IOR (ISHFT(MWD,8), IAND(MS(JS),MASK1))
   34 JS = JS - 1
      MT(NWT+1) = MWD
   39 RETURN
   91 write (nout, 101)
  101 format(' ubunch >>> abnormal end')
      END
