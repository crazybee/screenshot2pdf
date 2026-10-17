#!/usr/bin/env bash
VENV_DIR="${1:-.venv}"
echo "Creating virtual environment in ${VENV_DIR} ..."
python3 -m venv "$VENV_DIR" || python -m venv "$VENV_DIR"
PIP="$VENV_DIR/bin/pip"
if [ -f "$PIP" ]; then
  "$PIP" install --upgrade pip
  if [ -f requirements.txt ]; then
    "$PIP" install -r requirements.txt
  else
    echo "requirements.txt not found. Skipping package installation."
  fi
  echo "Virtual environment created. To activate: source $VENV_DIR/bin/activate"
else
  echo "pip not found in virtualenv. venv creation may have failed." >&2
  exit 1
fi
