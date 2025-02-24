import click  # noqa: F401
from typing import Any
from pathlib import Path
import importlib.metadata
from pprint import pprint as pp  # noqa: F401

from .prompt import ps1_prompt
from .prompt import themes as prompt_themes
from .prompt import Segment

from .projects import add as project_add, COLOR_TYPE
from .projects import cd as project_cd

# from .edit import test  # noqa: F401

__version__ = importlib.metadata.version("prompt")


def insert_time(line: str, time: float) -> str:
    spline = line.splitlines()
    return "\n".join([spline[0], f"{time:.6f} seconds", spline[1]])


class NaturalOrderGroup(click.Group):
    """Display commands sorted by order in file

    When using -h, display the commands in the order
    they are in the file where they are defined.

    https://github.com/pallets/click/issues/513
    """

    def list_commands(self, ctx: Any) -> Any:
        return self.commands.keys()


CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "token_normalize_func": lambda x: x.lower(),
}


@click.group(context_settings=CONTEXT_SETTINGS, cls=NaturalOrderGroup)
@click.version_option(version=__version__)
def prompt() -> None:
    """Output a PS1 prompt for bash and teleport to projects.

    Add this to your .bashrc or .bash_profile:

    \b
    # load the bash prompt source
    function _prompt_command() {
        export PS1="$(prompt ps1)"
    }
    export PROMPT_COMMAND=_prompt_command

    \b
    Find some long dirs for testing:
    find -type d | awk '{ print length, $0 }' | sort -n -s | cut -d" " -f2- | tail -n 10
    """
    pass


@prompt.command()
def ps1() -> None:
    """Output a PS1 prompt for bash."""
    print()
    if time_function := False:
        from timeit import default_timer as timer

        start = timer()
        line = ps1_prompt()
        end = timer()
        time = end - start
        line = insert_time(line, time)
        print(line)
    else:
        print(ps1_prompt())


@prompt.command()
def themes() -> None:
    """Show the themes and additional info."""
    for prompt_theme in prompt_themes:
        print()
        click.secho(f"{prompt_theme}", fg="bright_yellow")
        for k, v in prompt_themes[prompt_theme].items():
            if not isinstance(k, Segment):
                continue
            colored = click.style(
                str(k).ljust(16),
                fg=v.get("fg", ""),
                bg=v.get("bg", ""),
                bold=v.get("bold", False),
                italic=v.get("italic", False),
                underline=v.get("underline", False),
            )
            print(f"  {colored}", v)


@prompt.group()
def project() -> None:
    """Output commands to teleport to a project dir.

    \b
    For bash:
    ---------
    This is meant to be used from within .bashrc since cd used from a
    script executes in a subprocess. To make work, add the following
    to ~/.bashrc:

    \b
    function cdd
    {
        eval "$(prompt project cd "$1")"
    }
    # completion for cdd
    function _cdd
    {
        # the sed removes blank lines and lines starting with a comment (#)
        local cur=${COMP_WORDS[COMP_CWORD]}
        COMPREPLY=(
            $(compgen -W \\
              "$(sed "/\\(^$\\|^#\\)/d" < $HOME/.prompt-projects | cut -f1 | sort | xargs)" -- "$cur")
        )
    }
    complete -F _cdd cdd

    \b
    For fish:
    ---------
    Create a file called cdd.fish in .config/fish/functions and add the following to it:

    \b
    function cdd
        set dest (prompt project cd $argv)
        eval "$dest"
    end
    # completions
    set -l __cdd_commands (sed '/\\(^$\\|^#\\)/d' < $HOME/.prompt-projects | cut -f1 | sort | xargs)
    complete -f -c cdd -n "not __fish_seen_subcommand_from $__cdd_commands" -a $__cdd_commands
    """
    pass


@project.command()
@click.argument("project-name", type=str)
def cd(project_name: str) -> None:
    """Teleport to a project."""
    project_cd(project_name)


@project.command()
@click.argument("name", type=str)
@click.argument(
    "project-root", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--color", "-c", type=COLOR_TYPE, help="Color for the project name in the prompt."
)
def add(name: str, project_root: Path, color: str) -> None:
    """Add a project to the list of projects."""
    project_add(name, project_root, color)


# @project.command()
# def edit() -> None:
#     """Edit the project list."""
#     test()
