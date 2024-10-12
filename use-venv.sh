#!/bin/bash

VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"

if [ ! -d "$VENV_DIR" ]; then
    echo "venv doesn't exist yet, creating.."
    module load python/bundle-3.10
    # Create the virtual environment
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "unable to create venv"
        exit 1
    fi
else
    echo "Virtual environment found."
fi

echo "activating venv"
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "unable to activate venv"
    exit 1
fi

if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        echo "something wrong with requirements install"
        exit 1
    fi
else
    echo "No $REQUIREMENTS_FILE found"
fi

# Notify the user that the virtual environment is active
echo "we did it joe"


# source ./use-venv.sh