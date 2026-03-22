# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Prompt** is a terminal utility that generates customizable bash PS1 prompts and provides project directory teleportation. It displays contextual information about the current environment (git branch, virtual environment, SSH status, time, etc.) and allows quick navigation between registered projects.

## Development Commands

```bash
# Install editable version for development
uv tool install --editable .

# Build distribution wheel
uv build

# Type checking with mypy
mypy src/

# Code linting and formatting with ruff
ruff check src/
ruff format src/

# Run the CLI directly from source
python -m prompt.ui

# View available commands
prompt --help
prompt ps1 --help
prompt project --help
```

## Architecture

### Core Modules

**src/prompt/ui.py** - CLI entry point and command structure
- Defines the main click group with subcommands: `ps1`, `themes`, `project`
- `project` group has subcommands: `cd` (teleport to project), `add` (register new project)
- Imports theming and prompt logic from other modules

**src/prompt/prompt.py** - Prompt generation and terminal styling
- `Chunks` class: Responsible for building individual prompt segments
- Segment types: PATH, USER, TIME, BRANCH, VENV, POETRY, NIX, SSH, DDEV, SINK (project), FILLER, DOLLAR
- Theme system: Defines Local (local terminal) and Remote (SSH) color schemes for each segment
- Key methods:
  - `_chunk_*` methods: Generate content for each segment type
  - `apply_chunk_theme`: Apply colors and styling to segments
  - `get_project_info`: Reads project config from `~/.prompt-projects` file
- Utility functions: `hex_to_rgb`, `colorscale`, `snip` (truncate paths), `urlize` (make clickable links)
- Terminal integration: `set_kitty_tabs`, `set_iterm2_tabs` for setting terminal tab colors/titles

**src/prompt/projects.py** - Project management
- Project config file: `~/.prompt-projects` (TSV format: `NAME\tPATH\tCOLOR`)
- `read_csv`, `write_csv`: Config file I/O
- `cd`: Output shell command to teleport to project directory
- `add`: Register a new project with optional color
- `ColorParamType`: Click parameter type for validating color inputs (named or hex)

**src/prompt/__init__.py** - Package entry point
- Minimal wrapper that imports and calls `prompt()` from `ui.py`

### Configuration

- **Python version**: 3.13+
- **Dependencies**: `click>=8.1.7`
- **Dev dependencies**: mypy, ruff, ipython, pudb, pprofile

## Key Concepts

### Prompt Segments

The PS1 prompt is built from an ordered list of segments defined in `ps1_prompt()` function:
1. Build right segments first (TIME) so their lengths are known before calculating filler
2. Build left segments in order
3. Calculate filler (dots) to pad the remaining space
4. Append dollar sign on new line

### Project Color Theming

Projects are registered in `~/.prompt-projects` with a hex color. The SINK segment (project name) is displayed with this color, and the foreground color is automatically derived by scaling the background 3x (via `colorscale()` function).

### Terminal-Specific Features

- **Kitty**: Uses kitten protocol to set tab colors and title
- **iTerm2**: Uses escape codes to set tab title and RGB colors
- **General**: Creates clickable file:// URLs for paths in terminals that support them

### Path Truncation

Long paths are intelligently snipped using the `snip()` function:
- Splits path at 25% position with a large dot character as separator
- Keeps beginning and end of path visible
- Preserves relative home directory `~` notation

## Important Implementation Details

- The segment lengths must be calculated before output because terminal width affects path truncation
- Right segments (TIME) are processed first to account for their length before calculating filler
- The project color is read from config file on each prompt generation (for quick config updates without shell restart)
- Git status is checked with `--porcelain=v1` for efficiency
- DOLLAR segment styling is intentionally disabled to avoid terminal paste/history issues
