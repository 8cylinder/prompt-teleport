import click
from typing import Any
from pathlib import Path
import importlib.metadata

from .prompt import ps1_prompt
from .projects import add as project_add
from .projects import cd as project_cd

__version__ = importlib.metadata.version("prompt")


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
    """Output a PS1 prompt for bash and teleport to projects."""
    pass


@prompt.command()
def ps1() -> None:
    """Output a PS1 prompt for bash."""
    ps1_prompt()


@prompt.command()
def themes() -> None:
    """Show the themes and additional info."""
    ps1_prompt(info=True)


@prompt.group()
def project() -> None:
    """Manage project information."""
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
    "--color", "-c", type=str, help="Color for the project name in the prompt."
)
def add(name: str, project_root: Path, color: str) -> None:
    """Add a project to the list of projects."""
    project_add(name, project_root, color)


@project.command()
def edit() -> None:
    """Edit the project list."""
    print("TBD")
