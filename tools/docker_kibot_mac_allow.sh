#!/bin/bash

#Follow xhost setup guide here https://gist.github.com/sorny/969fe55d85c9b0035b0109a31cbcb088
#Steps 1 - 7

# Two optional arguments, first is the command to run, the second the image name
cmd=/bin/bash
image=kicad8_auto_full:latest

# If this script is named "blender" it will try to start blender from the docker image
SCRIPT_NAME=$(basename "$0")
# Define a variable based on the script name
if [ "$SCRIPT_NAME" == "blender" ]; then
    ARGS=$(printf "%q " "$@")
    cmd="nice blender $ARGS"
    INTERACTIVE=""
else
    INTERACTIVE="-it"
    # Check for optional arguments
    if [ ! -z "$1" ]; then
        cmd="$1"
    fi

    if [ ! -z "$2" ]; then
        image="$2"
    fi
fi

# Save current xhost access control state to a variable
original_state=$(xhost)

# Add access for the local user
# allow_to=SI:localuser:$USER #Doesn't look to work on MacOS, using localhost as a work around
allow_to=localhost
added_access="false"
if [[ "$original_state" == *"access control disabled"* || "$original_state" == *"$allow_to"* ]]; then
    echo "The user already has access."
else
    echo "Adding access for " $allow_to " ..."
    xhost +$allow_to
    added_access="true"
fi

# Try to export the Direct Rendering Interface for Blender
DOCKER_DEV=""
if [ -d "/dev/dri" ]; then
    DOCKER_DEV=" --device /dev/dri:/dev/dri"
fi

# Start the docker container
echo "Starting " $image " ..."
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
echo "Command:" $cmd
docker run --rm $INTERACTIVE \
    --user $USER_ID:$GROUP_ID \
    --env NO_AT_BRIDGE=1 \
    --env DISPLAY=docker.for.mac.host.internal:0 \
    --workdir=$(pwd) \
    --volume=/tmp/.X11-unix:/tmp/.X11-unix \
    --volume="/etc/group:/etc/group:ro" \
    --volume="/etc/passwd:/etc/passwd:ro" \
    --volume="/etc/shadow:/etc/shadow:ro" \
    --volume="/etc/timezone:/etc/timezone:ro" \
    --volume="/Users/$USER:/home/$USER:rw" \
    $DOCKER_DEV \
    ghcr.io/inti-cmnb/$image /bin/bash -c "$cmd"

if [[ "$added_access" == "true" ]]; then
    # Revert back to original xhost access control state
    echo "Reverting xhost to original state..."
    # Remove the added access for local:docker
    xhost -$allow_to
fi
