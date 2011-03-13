0 REM AIRi Protocol

@ERASE

0 REM PIN
1 1234

0 REM VERSION
2 0001

0 REM uniq
3 NONE


@INIT 10
0 REM PIN code
10 $1 = "1234"
0 REM get control over RED LED
11 A = pioout 19
12 A = pioset 19
0 REM YELLOW LED output and on
13 A = pioset 20
14 R = 0

15 A = zerocnt
16 $0="AIRi v"
17 PRINTV $2
18 A = getuniq $3
19 PRINTV " "
20 PRINTV $3
21 A = name $0

0 REM keep FTP going
22 G = 0
23 K = 1
0 REM button state variable
24 W = 0

0 REM check for button, virtual PIO17
25 A=pioirq"P00000000000000001"
26 RETURN

@SLAVE 40
40 PRINTS "$AIRi v"
41 PRINTS $2
42 PRINTS "\r\n"
43 B = pioset 20
0 REM connect CAMERA port, only 3-DH5
44 A = edr 2
0 REM mode 4, QVGA
45 A = camera 12
46 C = link 9
47 ALARM 1
48 RETURN

@IDLE 60
0 REM camera off
60 A = camera 0
0 REM LED off
61 A = pioclr 20;
62 GOTO 300


@PIO_IRQ 100
100 IF $0[17]=49 THEN 110;
0 REM ignore button release on rebooting
101 IF W = 3 THEN 103;
0 REM was it a release, handle it
102 IF W <> 0 THEN 120;
103 RETURN

0 REM button press, save state, start ALARM
110 $2 = $0;
111 W = 1;
112 ALARM 3
113 RETURN

0 REM button press disconnects slave
120 A = disconnect 0
121 A = pioclr 20
122 RETURN


@ALARM 170
0 REM check for button pressed
170 A = pioget 17;
171 IF A = 0 THEN 190;

0 REM long press power down
172 ALARM 0;

0 REM wait until button release, blink blue LED fast
173 B = pioget 17
174 A = pioclr 20
175 A = delayms 100
176 A = pioset 20
177 IF B = 1 THEN 173;
178 W = 3;
179 A = pioclr 117;
180 A = reboot;

181 FOR E = 0 TO 10
182   WAIT 1
183 NEXT E
184 RETURN

0 REM we have a connection
190 A = status;
191 IF A>=1 THEN 400;
192 ALARM 0
193 RETURN

300 A = slave 15
301 A = pioset 20;
302 A = pioclr 20
303 A = delayms 100
304 A = pioset 20;
305 A = pioclr 20;
306 IF G = 1 THEN 310
307 ALARM 5
308 RETURN

310 A = readcnt
311 IF A < 10000 THEN 307
312 WAIT 3
313 A = disable 3
314 G = 0
315 GOTO 307

@PIN_CODE 340
0 REM fixed PIN code
340 $0=$1;
341 RETURN

0 REM protocol checking
0 REM $<LETTER><VALUE><newline>
400 INPUTS $0;
401 IF $0[0]!=36 THEN 400;
402 IF $0[1]=83 THEN 410;
403 IF $0[1]=70 THEN 420;
404 IF $0[1]=80 THEN 430;
405 IF $0[1]=69 THEN 440;
406 GOTO 400;

0 REM set size
410 B = atoi $0[2];
411 A = camera B;
412 GOTO 400;

0 REM set flash
420 IF $0[1]=49 THEN 423;
421 A = camflash 0;
422 GOTO 400;
423 A = camflash 1;
424 GOTO 400;

0 REM do PAN
430 A = campan $0[1];
431 GOTO 400;

0 REM exposure
440 B = atoi $0[2];
441 A = camexpo B;
442 GOTO 400;

450 blabla



