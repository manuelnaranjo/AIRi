0 REM AIRi Protocol

@ERASE

0 REM PIN
1 1234

0 REM VERSION
2 0002

0 REM uniq
3 NONE

0 REM PIO inout
4 RESERVED


@INIT 9
9 Z = 0
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
0 REM let VM set name before interrupts enable
22 WAIT 1

0 REM keep FTP going
23 G = 0
24 K = 1
0 REM button state variable
25 W = 0

0 REM check for button, virtual PIO17
26 A=pioirq"P00000000000000001"
27 RETURN

@SLAVE 40
40 PRINTS "$AIRi v"
41 PRINTS $2
42 PRINTS "\r\n"
43 B = pioset 20
0 REM connect CAMERA port, only 3-DH5
44 A = edr 2
0 REM mode 4, QVGA
0 REM 45 A = camera 1
0 REM 46 C = link 9
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
110 $4 = $0;
111 W = 1;
112 ALARM 3
113 RETURN

0 REM button press disconnects slave, just in case we have one
120 A = disconnect 0
0 REM red charger LED on
121 A = pioout 19
122 A = pioset 19
0 REM we make a picture and put it into SD card
123 A = camera 1
0 REM this will take 5 seconds to stabilize the sensor
124 A = camflash 1
0 REM we take the time to open a file, which takes a while too...
125 A = open "/*.jpg"

0 REM wait for a picture
126 A = camcopy
127 IF A <> 0 THEN 130
128 WAIT 1
129 GOTO 126

0 REM get picture from memory into SD card
130 A = camcopy;
131 IF A > 0 THEN 130;

0 REM close file, get file name in $0
132 A = close $0
133 PRINTU $0
0 REM switch camera off, turns SD card off too
134 A = camera 0
135 A = pioin 19
136 A = pioclr 20
137 RETURN


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
179 A = pioclr 17;
180 A = reboot;

181 FOR E = 0 TO 2
182   A = ring E
183   WAIT 1
184 NEXT E
185 RETURN

0 REM check if we have a connection
190 A = status;
191 IF A>0 THEN 400;
0 REM no we don't
192 GOTO 297;

0 REM make undiscoverable after FTP off
297 IF G = 0 THEN 300
298 A = slave 15
299 GOTO 301
300 A = slave -15

301 A = pioset 20;
302 A = pioclr 20
303 A = delayms 100
304 A = pioset 20;
305 A = pioclr 20;
306 IF G = 1 THEN 310
307 ALARM 1
308 RETURN

310 A = readcnt
311 IF A < 30 THEN 307
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
400 A = pioclr 20;
401 A = delayms 100;
402 A = pioset 20;
403 $0[0] = 0;
404 TIMEOUTS 5
405 INPUTS $0
406 A = status;
0 REM lost slave connection, back to slave
407 IF A <> 1 THEN 300;
410 IF $0[0]<>36 THEN 400;
411 IF $0[1]=83 THEN 420;
412 IF $0[1]=70 THEN 430;
413 IF $0[1]=80 THEN 440;
414 IF $0[1]=69 THEN 450;
415 IF $0[1]=68 THEN 460;
416 IF $0[1]=76 THEN 470;
417 IF $0[1]=84 THEN 480;
419 GOTO 400;

0 REM set size
420 B = atoi $0[2];
421 A = camera B
422 GOTO 400;
423 RETURN

0 REM set flash
430 A = camflash $0[2]-48
431 GOTO 400;

0 REM do PAN
440 A = campan $0[2]
441 GOTO 400;

0 REM exposure
450 B = atoi $0[2];
451 A = camexpo B
452 GOTO 400;

0 REM date
460 A = setdate $0[2];
461 GOTO 400;

0 REM link enable/disable
470 IF $0[2] = 49 THEN 475;
471 A = unlink 9;
472 GOTO 400;

475 A = link 9;
476 GOTO 400;

0 REM take picture
480 PRINTS"TAKING 
481 $479 = $0[2]
482 $0[0] = 0
483 PRINTV $479
484 PRINTS $479
485 A = open $479

0 REM wait for a picture
490 A = camcopy
491 IF A <> 0 THEN 495
492 WAIT 1
493 GOTO 490

0 REM get picture from FIFO into target
495 A = camcopy;
496 IF A > 0 THEN 495;

0 REM close file, get file name in $0
497 A = close $0
498 PRINTS $0
499 GOTO 400

600 END
