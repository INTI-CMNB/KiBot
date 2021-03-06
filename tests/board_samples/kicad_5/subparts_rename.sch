EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "KiCost subparts test"
Date "2021-03-16"
Rev "r1"
Comp "KiBot"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Mechanical:Heatsink HS1
U 1 1 6063AB02
P 3750 1325
F 0 "HS1" H 3891 1491 50  0000 L CNN
F 1 "322400B00000G" H 3891 1400 50  0000 L CNN
F 2 "" H 3762 1325 50  0001 C CNN
F 3 "~" H 3762 1325 50  0001 C CNN
F 4 "Aavid" H 3750 1325 50  0001 C CNN "manufacturer"
F 5 "322400B00000G" H 3891 1309 50  0000 L CNN "mpn"
F 6 "HS100-ND" H 3750 1325 50  0001 C CNN "digikey_part#"
F 7 "HEAT SINK TO-18 1W BLK" H 3750 1325 50  0001 C CNN "Description"
	1    3750 1325
	1    0    0    -1  
$EndComp
$Comp
L Device:Q_NPN_BCE Q2
U 1 1 6063D25D
P 3750 1550
F 0 "Q2" V 3675 1350 50  0000 C CNN
F 1 "2N2222A" V 3575 1250 50  0000 C CNN
F 2 "Package_TO_SOT_THT:TO-18-3" H 3950 1650 50  0001 C CNN
F 3 "~" H 3750 1550 50  0001 C CNN
F 4 "Central Semiconductor Corp" V 3750 1550 50  0001 C CNN "mnf"
F 5 "2N2222A PBFREE" V 3500 1100 50  0000 C CNN "pn"
F 6 "TRANS NPN 40V 0.8A TO-18" V 3750 1550 50  0001 C CNN "Description"
F 7 "1514-2N2222APBFREE-ND" V 3750 1550 50  0001 C CNN "digikey_p#"
	1    3750 1550
	0    -1   -1   0   
$EndComp
Text Notes 3600 1100 0    50   ~ 0
A Transistor and its heatsink\nOnly one goes to the PCB
Text Notes 575  825  0    200  ~ 40
KiCost subparts
$Comp
L Device:Q_NPN_BCE Q1
U 1 1 60640F08
P 1075 1300
F 0 "Q1" V 1000 1100 50  0000 C CNN
F 1 "2N2222A" V 900 1000 50  0000 C CNN
F 2 "Package_TO_SOT_THT:TO-18-3" H 1275 1400 50  0001 C CNN
F 3 "~" H 1075 1300 50  0001 C CNN
F 4 "Central Semiconductor Corp; Aavid" V 1075 1300 50  0001 C CNN "man"
F 5 "2N2222A PBFREE; 322400B00000G" V 825 500 50  0000 C CNN "manf_num"
F 6 "TRANS NPN 40V 0.8A TO-18 + Heatsink" V 1075 1300 50  0001 C CNN "Description"
F 7 "1514-2N2222APBFREE-ND; HS100-ND" V 1075 1300 50  0001 C CNN "digikey_pn"
F 8 "2N2222A;322400B00000G" V 1150 2600 50  0001 C CNN "Value_Subparts"
	1    1075 1300
	0    -1   -1   0   
$EndComp
Text Notes 2650 1550 0    50   ~ 0
Equivalent to ->
$Comp
L Connector_Generic:Conn_01x06 J1
U 1 1 60649B1F
P 1150 2600
F 0 "J1" V 1114 2212 50  0000 R CNN
F 1 "Conn_01x06" V 1023 2212 50  0000 R CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical" H 1150 2600 50  0001 C CNN
F 3 "~" H 1150 2600 50  0001 C CNN
F 4 "Molex; Molex; Molex; LEM; LEM" V 1150 2600 50  0001 C CNN "mfg"
F 5 "0022232061;0022012067; 6: 08-50-0114;  LA 55-P; lv 25-P" V 1150 2600 50  0001 C CNN "mfg part#"
F 6 "WM4204-ND; WM2015-ND; WM1114-ND; 398-1010-ND; 398-1019-ND" V 1150 2600 50  0001 C CNN "digikey_vendor#"
F 7 "CONN HEADER VERT 6POS 2.54MM; CONN HOUSING 6POS .100 W/RAMP; CONN 22-30AWG CRIMP TIN; SENSOR CURRENT HALL 50A AC/DC; TRANSDUCR VOLTAG CLOSE LOOP 10MA" V 1150 2600 50  0001 C CNN "Description"
F 8 "Male_01x06;Female_01x06;Crimp_Pin;LA 55-P;LV 25-P" V 1150 2600 50  0001 C CNN "Value_Subparts"
	1    1150 2600
	0    -1   -1   0   
$EndComp
Text Notes 900  2400 0    50   ~ 0
A male header\nBut we want to include the female, the pins and the two\nsensors wired to the female.
$Comp
L Device:R R1
U 1 1 6064C12F
P 3750 2650
F 0 "R1" H 3820 2696 50  0000 L CNN
F 1 "0" H 3820 2605 50  0000 L CNN
F 2 "" V 3680 2650 50  0001 C CNN
F 3 "~" H 3750 2650 50  0001 C CNN
F 4 "Bourns" H 3750 2650 50  0001 C CNN "mfr"
F 5 "CR0603-J/-000ELF:5" H 3750 2650 50  0001 C CNN "mfg#"
F 6 "CR0603-J/-000ELFCT-ND:  5" H 3750 2650 50  0001 C CNN "digikey_vpn"
F 7 "RES SMD 0 OHM JUMPER 1/8W 0603" H 3750 2650 50  0001 C CNN "Description"
	1    3750 2650
	1    0    0    -1  
$EndComp
Text Notes 3675 2475 0    50   ~ 0
A simple resistor, \nbut multiplied by 5\nWe add: R4 no mult \n      and R5 no manf#\nTotal: 7
$Comp
L Device:R R2
U 1 1 6064CA86
P 3750 3400
F 0 "R2" H 3820 3446 50  0000 L CNN
F 1 "100" H 3820 3355 50  0000 L CNN
F 2 "" V 3680 3400 50  0001 C CNN
F 3 "~" H 3750 3400 50  0001 C CNN
F 4 "Bourns" H 3750 3400 50  0001 C CNN "manf"
F 5 "CR0603-JW-101ELF   :   4.5" H 3750 3400 50  0001 C CNN "mfg-num"
F 6 "CR0603-JW-101ELFCT-ND   :4.5" H 3750 3400 50  0001 C CNN "digikey_num"
F 7 "RES SMD 100 OHM 5% 1/10W 0603" H 3750 3400 50  0001 C CNN "Description"
	1    3750 3400
	1    0    0    -1  
$EndComp
Text Notes 3675 3225 0    50   ~ 0
A simple resistor, \nbut multiplied by 4.5
$Comp
L Device:R R3
U 1 1 6064D8D1
P 3750 4150
F 0 "R3" H 3820 4196 50  0000 L CNN
F 1 "100k" H 3820 4105 50  0000 L CNN
F 2 "" V 3680 4150 50  0001 C CNN
F 3 "~" H 3750 4150 50  0001 C CNN
F 4 "Bourns" H 3750 4150 50  0001 C CNN "manf"
F 5 "4/5 : CR0603-JW-104ELF  " H 3750 4150 50  0001 C CNN "mfg_num"
F 6 "  4/5  :   CR0603-JW-104ELFCT-ND" H 3750 4150 50  0001 C CNN "digikey-p#"
F 7 "RES SMD 100K OHM 5% 1/10W 0603" H 3750 4150 50  0001 C CNN "Description"
	1    3750 4150
	1    0    0    -1  
$EndComp
Text Notes 3675 3975 0    50   ~ 0
A simple resistor, \nbut multiplied by 4/5
$Comp
L Device:R R4
U 1 1 6064EF62
P 4250 2650
F 0 "R4" H 4320 2696 50  0000 L CNN
F 1 "0" H 4320 2605 50  0000 L CNN
F 2 "" V 4180 2650 50  0001 C CNN
F 3 "~" H 4250 2650 50  0001 C CNN
F 4 "Bourns" H 4250 2650 50  0001 C CNN "manf"
F 5 "CR0603-J/-000ELF" H 4250 2650 50  0001 C CNN "manf-num"
F 6 "CR0603-J/-000ELFCT-ND" H 4250 2650 50  0001 C CNN "digikeyvp#"
F 7 "RES SMD 0 OHM JUMPER 1/8W 0603" H 4250 2650 50  0001 C CNN "Description"
	1    4250 2650
	1    0    0    -1  
$EndComp
$Comp
L Device:R R5
U 1 1 6064F812
P 4500 2650
F 0 "R5" H 4570 2696 50  0000 L CNN
F 1 "0" H 4570 2605 50  0000 L CNN
F 2 "" V 4430 2650 50  0001 C CNN
F 3 "~" H 4500 2650 50  0001 C CNN
F 4 "RES SMD 0 OHM JUMPER 1/8W 0603" H 4500 2650 50  0001 C CNN "Description"
	1    4500 2650
	1    0    0    -1  
$EndComp
$EndSCHEMATC
