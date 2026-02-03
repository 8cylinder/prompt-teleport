# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`prompt` is a terminal PS1 prompt generator and project directory teleporter. It outputs styled bash prompts with git status, virtual environment indicators, and project-specific theming. It also provides quick directory navigation to registered projects.

## Development Commands

```bash
# Install editable for development
uv tool install --editable .

# Run the prompt
prompt ps1

# Type checking
mypy src/prompt

# Linting
ruff check src/prompt
ruff format src/prompt
```

## Architecture

### Entry Point
- `src/prompt/__init__.py` - Imports and immediately calls `prompt()` from `ui.py`
- `src/prompt/ui.py` - Click CLI definition with commands: `ps1`, `themes`, `project cd`, `project add`

### Core Modules
- `src/prompt/prompt.py` - PS1 prompt rendering engine
  - `Chunks` class: Builds each prompt segment (path, git branch, user, time, etc.)
  - `Segment` enum: Defines all available prompt segments
  - `themes` dict: Color/style definitions for "Local" and "Remote" environments
  - Detects environment (local, SSH, OrbStack) and applies appropriate theme
  - Handles iTerm2 and Kitty terminal tab coloring

- `src/prompt/projects.py` - Project directory management
  - Reads/writes `~/.prompt-projects` (TSV format: name, path, color)
  - `cd()`: Outputs shell commands for directory teleportation
  - `add()`: Adds new project entries

### Configuration
- `~/.prompt-projects` - TSV file mapping project names to directories and colors
- Colors can be hex (`#2e004c`) or named (`red`, `blue`, etc.)

### Key Patterns
- Prompt segments are built via `_chunk_*` methods that follow the naming pattern `_chunk_{segment.name.lower()}`
- Terminal colors use RGB tuples `(R, G, B)` or color names
- Git worktree directories get hue-adjusted colors based on directory hash for visual differentiation
