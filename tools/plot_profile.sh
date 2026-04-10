#!/bin/bash
if [ ! -f "pp/light_control-panel.kicad_pcb" ]; then
    src/kibot -c tests/yaml_samples/panelize_1.kibot.yaml -b tests/board_samples/kicad_9/light_control.kicad_pcb -d pp
fi
sed -i 's/PROFILE_PLOT = False/PROFILE_PLOT = True/' kibot/out_pcbdraw.py
time src/kibot -L log_pcbdraw.txt -c tests/yaml_samples/pcbdraw_simple.kibot.yaml -b pp/light_control-panel.kicad_pcb -d pp
sed -i 's/PROFILE_PLOT = True/PROFILE_PLOT = False/' kibot/out_pcbdraw.py
