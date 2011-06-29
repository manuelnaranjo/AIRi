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

0 REM boot flag for automatic start
5 0

@INIT 13
0 REM we are booting
13 R = 1
14 IF $5[0] <> 0 THEN 16
15 R = 0
16 $0="AIRi v"
17 PRINTV $2
18 A = getuniq $3
19 PRINTV " "
20 PRINTV $3
21 A = name $0
0 REM let VM set name before interrupts enable
22 WAIT 1

0 REM we switch off everything
23 A = disable 3
24 A = pioclr 20
0 REM give charger LED back
25 A = pioclr 19

0 REM make discoverable
26 G = 0
27 K = 1
0 REM button state variable, set to ignore
28 W = 3

0 REM check for button, virtual PIO17
29 A=pioirq"P00000000000000001"
30 RETURN



@SLAVE 40
40 PRINTS "$AIRi v"
41 PRINTS $2
42 PRINTS "\r\n"
43 B = pioset 20
0 REM allow only 3-DH5
44 A = edr 2
0 REM mode 1, QVGA
0 REM 45 A = camera 1
0 REM 46 C = link 9
47 ALARM 1
48 RETURN


@IDLE 60
0 REM camera off
60 A = camera 0
0 REM LED off
61 A = pioclr 20;
62 IF R=0 THEN 64
63 GOTO 300
64 RETURN



@PIO_IRQ 100
100 IF $0[17]=49 THEN 110;

0 REM ignore button release on shutdown/startup
101 IF W = 3 THEN 103;
0 REM was it a release, handle it
102 IF W <> 0 THEN 120;
103 RETURN

0 REM button press, save state, start ALARM
110 $4 = $0;
0 REM set state to pressed, when booted
111 IF R = 0 THEN 113;
112 W = 1;
113 ALARM 3
114 RETURN

0 REM this is "take one picture to SD"
0 REM button press disconnects slave, just in case we have one
120 A = disconnect 0
0 REM red charger LED on
122 A = pioset 20
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
136 A = pioclr 20
137 RETURN


@ALARM 170
0 REM check for button pressed
170 A = pioget 17;
171 IF A = 0 THEN 294;

0 REM long press for power down or up
172 ALARM 0;

0 REM wait until button release, blink yellow LED fast
173 B = pioget 17
174 A = pioclr 20
175 A = delayms 100
176 A = pioset 20
177 IF B = 1 THEN 173;
0 REM state shutdown/startup
178 W = 3;
179 IF R=0 THEN 200

0 REM this is shutdown
180 A = pioclr 17;
181 R = 0;
0 REM mark reboot persistent 
182 $5[0] = 0;
183 A = disable 3
184 A = reboot;
185 FOR E = 0 TO 10
186   WAIT 1
187 NEXT E
0 REM if not shutdown, schedule alarm
0 REM may not get here if shutdown successful
188 ALARM 60
189 RETURN
 



0 REM BOOT UP procedure
200 A = zerocnt
201 A = enable 1
0 REM set to booted
202 R = 1
0 REM make discoverable
203 G = 1
204 A = pioset 20
0 REM persitent marked running
205 $5[0] = 1
206 GOTO 295


0 REM this ALARM message, no button pressed
0 REM when not booted call shutdown
294 IF R = 0 THEN 180
295 A = status;
296 IF A>0 THEN 400;

0 REM this is no connection, meaning call slave
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
307 ALARM 5
308 RETURN

0 REM disable FTP after 30 secs
310 A = readcnt
311 IF A < 30 THEN 307
312 WAIT 3
313 A = disable 3
0 REM make slave undiscoverable
314 G = 0
315 GOTO 307




@PIN_CODE 340
0 REM fixed PIN code
340 $0=$1;
341 RETURN


0 REM this is command line protocol 
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
408 IF $0[0]<>36 THEN 400;
409 IF $0[1]=83 THEN 420;
410 IF $0[1]=70 THEN 430;
411 IF $0[1]=80 THEN 440;
412 IF $0[1]=69 THEN 450;
413 IF $0[1]=68 THEN 460;
414 IF $0[1]=76 THEN 470;
415 IF $0[1]=84 THEN 480;
418 ALARM 1
419 RETURN

0 REM set size
420 B = atoi $0[2];
421 A = camera B
422 ALARM 1
423 RETURN

0 REM set flash
430 A = camflash $0[2]-48
431 ALARM 1
432 RETURN

0 REM do PAN
440 A = campan $0[2]
441 ALARM 1
442 RETURN

0 REM exposure
450 B = atoi $0[2];
451 A = camexpo B
452 ALARM 1
453 RETURN

0 REM date
460 A = setdate $0[2];
461 ALARM 1
462 RETURN

0 REM link enable/disable
470 IF $0[2] = 49 THEN 475;
471 A = unlink 9;
472 ALARM 1
473 RETURN

475 A = link 9;
476 ALARM 1
477 RETURN

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
499 ALARM 1
500 RETURN

600 END
