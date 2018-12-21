# TerminusAddons

A collection of keybindings and extra commands to make Terminus just a little more awesome.

## SplitOpenTerminus Command

- Open Terminus in a new split view
- It knows not to perform a split if there already exists a split with 1+ terminals
- It can optionally reuse an existing terminal if it's sitting at a command prompt

## RunInTerminus

Run current file in new or existing terminal

This command will automagically activate a conda environment if there is a setting named ``conda_env``

This command will automagically use `pipenv run python ...` if it can detect a ``Pipfile.lock``.

## Shortcuts

- Split Open New Default Terminal
  - Linux / Windows: ``ctrl+k`` ``ctrl+t``
  - MacOS: ``cmd+k`` ``cmd+t``

- Run in Terminus
  - Linux / Windows: ``ctrl+alt+b``
  - MacOS: ``cmd+alt+b``

# Coming Soon

- selecting default venv for Run
