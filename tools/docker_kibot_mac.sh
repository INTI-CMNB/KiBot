#!/bin/sh
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
docker run --rm -it \
    --user $USER_ID:$GROUP_ID \
    --env NO_AT_BRIDGE=1 \
    --env DISPLAY=$DISPLAY \
    --workdir="/Users/$USER" \
    --volume=/tmp/.X11-unix:/tmp/.X11-unix \
    --volume="/etc/group:/etc/group:ro" \
    --volume="/Users/$USER:/home/$USER:rw" \
    --volume="/etc/passwd:/etc/passwd:ro" \
    --volume="/etc/shadow:/etc/shadow:ro" \
    --volume="/Users/$USER:/home/$USER:rw" \
    ghcr.io/inti-cmnb/kicad8_auto_full:latest /bin/bash
