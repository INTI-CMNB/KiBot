# KiCad 8 to KiCad 9 layer translation

KiCad 9 changed the layer numbers, I guess thinking in the future posibility
to support more than 32 layers.

This introduced a lot of problems. This code was used to create a KiCad 8 to
KiCad 9 translation dictionary used by KiDiff.

        KiCad 8   KiCad 9  KiCad 11
F.Cu       0        0        3
In1.Cu     1        4        4
In2.Cu     2        6        5
...
In30.Cu   30       62       33
B.Cu      31        2       34

