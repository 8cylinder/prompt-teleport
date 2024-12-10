# -*- mode: python -*-
#!/bin/sh
"exec" "$(dirname $0)/.venv/bin/python" "$0" "$@"

import os
import sys
import re
import click
import csv
import getpass
import random
import colorsys
from pathlib import Path

# from collections import OrderedDict

# from typing import orderedDict


CONFIG_FILE = "~/.sink-projects"


def error(msg: str) -> None:
    err = click.style("Error:", bold=True, fg="red")
    msg = click.style(msg, fg="red")
    print(f'printf "\n{err} {msg}\n"')
    sys.exit(1)


def read_csv() -> dict[str, list[str]]:
    datafile = os.path.expanduser(CONFIG_FILE)
    data = {}
    try:
        with open(datafile, newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                if row and not row[0].startswith("#"):
                    data[row[0]] = [row[1], row[2]]
    except FileNotFoundError:
        error(f"sink projects list ({datafile}) not found.")

    data = dict(sorted(data.items(), key=lambda item: item[1]))
    return data


def write_csv(odict: dict[str, list[str]]) -> None:
    datafile = os.path.expanduser(CONFIG_FILE)
    data = [[i, j[0], j[1]] for i, j in odict.items()]
    with open(datafile, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        for line in data:
            writer.writerow(line)


def get_project_dir(projects: dict[str, list[str]]) -> str | bool:
    pwd = os.path.realpath(os.path.curdir)
    for project, project_info in projects.items():
        path = project_info[0]
        if pwd == path:
            # is in root of project and the user
            # probably wants to change projects
            return False
        if pwd.startswith(path):
            # is in a subdir of a project and
            # the user probably want to go to root
            return path
    return False


def add_line(name: str, project_root: Path, color: str) -> None:
    if not color:
        color = get_random_color()

    edit = False
    projects = read_csv()
    for project in projects:
        if project == name:
            click.echo(f"New color: {color}")
            path = projects[project][0]
            projects[project] = [path, color]
            edit = True
    if not edit:
        projects[name] = [str(project_root), color]
    write_csv(projects)


def filter_projects(
    projects: dict[str, list[str]], project: str
) -> dict[str, list[str]]:
    filtered = {
        key: val
        for key, val in projects.items()
        if key.lower().startswith(project.lower())
    }
    return filtered


def pretty_print(projects: dict[str, list[str]]) -> None:
    out = []
    for name, project_info in projects.items():
        path = project_info[0]
        name = name.ljust(15)
        name = click.style(name, bold=True)
        username = getpass.getuser()
        missing = None if os.path.exists(path) else "red"
        path = re.sub(f"^/home/{username}", "~", path)
        path = click.style(path, dim=True, fg=missing)
        out.append(f"{name}  {path}\\n")
    joined_out = "".join(out)
    formated_out = f'printf "{joined_out}"'
    print(formated_out)


def print_list(projects: dict[str, list[str]]) -> None:
    pretty = "".join(projects)
    print(f'printf "{pretty}"')


def get_random_color() -> str:
    hue = round(random.random(), 3)  # between 0 and 1
    value = random.choice([0.15, 0.2, 0.25, 0.3])
    saturation = random.choice([0.1, 0.2, 0.4, 0.6, 0.8, 1])
    rgb = colorsys.hls_to_rgb(hue, value, saturation)
    scaled_rgb = [round(scale_to_255(i)) for i in rgb]
    hex_color = "#{0:02x}{1:02x}{2:02x}".format(*scaled_rgb)
    return hex_color


def scale_to_255(i: float) -> float:
    return (i * 100) * 255 / 100


class ColorParamType(click.ParamType):
    name = "color"
    named_colors = [
        "white",
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
        "black",
    ]
    hex_colors = "^#(?:[0-9a-fA-F]{3}){1,2}$"

    def convert(self, value: str, param, ctx) -> str:
        is_color = False
        if value in self.named_colors:
            is_color = True
        elif re.search(self.hex_colors, value):
            is_color = True

        if not is_color:
            named_colors = ", ".join(self.named_colors)
            self.fail(
                f'"{value}" is not a named color \n({named_colors}) or hex color (#ffffff)',
                param,
                ctx,
            )
        return value


COLOR_TYPE = ColorParamType()

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}


# @click.group(context_settings=CONTEXT_SETTINGS)
# def main() -> None:
#     """Teleport to project directories."""


# @main.command(context_settings=CONTEXT_SETTINGS)
# @click.argument("project", required=False)
def cd(project: str) -> None:
    r"""Output commands to teleport to a project dir.

    \b
    For bash:
    ---------
    This is meant to be used from within .bashrc since cd used from a
    script executes in a subprocess. To make work, add the following
    to ~/.bashrc:

    \b
    function cdd
    {
        eval "$($HOME/path/to/cd-projects.py cd "$1")"
    }

    And for completion add this:

    \b
    function _cdd
    {
        local cur=${COMP_WORDS[COMP_CWORD]}
        COMPREPLY=(
            $(compgen -W \\
              "$(sed "/\(^$\|^#\)/d" < $HOME/.sink-projects | cut -f1 | sort | xargs)" -- "$cur")
        )
    }
    complete -F _cdd cdd

    \b
    For fish:
    ---------
    Create a file called cdd.fish in .config/fish/functions and add the following to it:

    \b
    function cdd
        set dest ($HOME/bin/cd-projects.py cd $argv)
        eval "$dest"
    end
    # completions
    set -l __cdd_commands (sed '/\(^$\|^#\)/d' < $HOME/.sink-projects | cut -f1 | sort | xargs)
    complete -f -c cdd -n "not __fish_seen_subcommand_from $__cdd_commands" -a $__cdd_commands
    """
    projects = read_csv()
    if not project:
        project_dir = get_project_dir(projects)
        if project_dir:
            print(f"cd {project_dir}")
        else:
            pretty_print(projects)
    else:
        matching = filter_projects(projects, project)
        if len(matching) > 1:
            pretty_print(matching)
        elif len(matching) == 0:
            pretty_print(projects)
            error(f"No project match for: {project}")
        else:
            project_info = list(matching.values())[0]
            path = project_info[0]
            print(f"cd {path}")


# @main.command(context_settings=CONTEXT_SETTINGS)
# @click.argument("name")
# @click.argument(
#     "project-root",
#     type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
# )
@click.argument("color", type=COLOR_TYPE, required=False)
def add(name: str, project_root: Path, color: str) -> None:
    r"""Add a project entry to the config file.

    If color is a hex color, it should be enclosed in single quotes or escaped:
    '#2e004c' OR \#2e004c

    \b
    NAME:         Name of project, should have no spaces.
    PROJECT_ROOT: Must be an existing dir.
    COLOR:        Named or hex.  If not supplied, a random color will be used.
    """
    add_line(name, project_root, color)


# @main.command(context_settings=CONTEXT_SETTINGS)
# @click.argument("name")
def remove(name: str) -> None:
    """Remove a project entry from the config file.

    NAME must be the full name of the project.
    """
    datafile = os.path.expanduser("~/.sink-projects")
    with open(datafile, "r") as f:
        contents = f.readlines()

    with open(datafile, "w") as f:
        for line in contents:
            if not line.startswith(f"{name}\t"):
                f.write(line)


# if __name__ == "__main__":
#     main()
