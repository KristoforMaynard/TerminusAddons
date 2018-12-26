# TerminusAddons

A collection of keybindings and extra commands to make Terminus just a little more awesome.

## SplitOpenTerminus Command

- Open Terminus in a new split view
- It knows not to perform a split if there already exists a split with 1+ terminals

## RunInTerminus

Run current file in new or existing terminal. An existing terminal is used if it is sitting at a command prompt.

This command will automagically activate a conda environment if there is a setting named ``conda_env``

This command will automagically use `pipenv run python ...` if it can detect a ``Pipfile.lock``.

## Installation

Add "https://github.com/KristoforMaynard/TerminusAddons" to the ``repositories`` list in your ``Package Control.sublime-settings``. Then install using package control as normal. It may make sense to contribute these changes to the Terminus project at some point.

## Shortcuts

- Split Open New Default Terminal
  - Linux / Windows: ``ctrl+k`` ``ctrl+t``
  - MacOS: ``cmd+k`` ``cmd+t``

- Run in Terminus
  - Linux / Windows: ``ctrl+alt+b``
  - MacOS: ``cmd+alt+b``
