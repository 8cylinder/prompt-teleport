#!/usr/bin/env python3

import csv
import datetime
import os
import random
import socket
import subprocess
import sys
from dataclasses import dataclass, fields
from enum import Enum, auto
from pathlib import Path
from typing import Any

try:
    import click
except ImportError:
    print("Click not installed.")


__version__ = "2.1.0"


# class Click:
#     def style(self, msg, fg, bg, bold, underline, italic):
#         print(msg)
#
#
# click = Click()


class Segment(Enum):
    POETRY = auto()
    PIPENV = auto()
    SINK = auto()
    BRANCH = auto()
    USER = auto()
    TIME = auto()
    VIRTUAL = auto()
    VENV = auto()
    NIX = auto()
    SSH = auto()
    PATH = auto()
    FILLER = auto()
    DOLLAR = auto()
    DDEV = auto()
    INVISIBLE = auto()


@dataclass
class Ellipses:
    unicode_ellipsis: str = "…"  # "\u2026"
    ascii_ellipsis: str = "..."
    bar: str = "|"
    bars: str = "|||"
    large_square: str = "▉"  # "\u2589"
    small_square: str = "▮"  # "\u25ae"
    large_dot: str = "⏺"  # "\u25cf"
    medium_dot: str = "•"
    small_dot: str = "·"
    three_square: str = "▮▮▮"  # "\u25ae\u25ae\u25ae"
    three_dots: str = "●●●"  # "\u25cf\u25cf\u25cf"
    triple_bar: str = "⦀"
    ex: str = "╳"
    diagonal: str = "⧄"
    hr: str = "─"

    @staticmethod
    def list_fields() -> list[str]:
        return [f.name for f in fields(Ellipses)]

    @staticmethod
    def list_values() -> list[str]:
        return [str(field.default) for field in fields(Ellipses)]

    @staticmethod
    def random() -> str:
        return random.choice(Ellipses.list_values())


# "segment-name": {
#     "fg": (R, G, B) | int | str,
#     "bg": (R, G, B) | int | str,
#     "bold": Bool,
#     "italic": Bool,
#     "underline": Bool,
# },
themes: dict[str, dict[Segment | str, dict[str, Any]]] = {
    "Local": {
        Segment.SINK: {"fg": (29, 135, 165), "bg": (13, 58, 101)},
        Segment.SSH: {"fg": "white", "bg": "red"},
        Segment.USER: {"fg": (136, 183, 108)},
        Segment.PATH: {"fg": (93, 159, 222)},
        Segment.TIME: {"fg": (52, 90, 125)},
        Segment.PIPENV: {"fg": (70, 204, 64), "bg": (36, 135, 75)},
        Segment.BRANCH: {"fg": (93, 159, 222)},
        Segment.VIRTUAL: {"fg": (70, 204, 64), "bg": (25, 94, 52)},
        Segment.POETRY: {"fg": (70, 204, 64), "bg": (25, 94, 52)},
        Segment.NIX: {"fg": "white", "blue": "88"},
        Segment.VENV: {"fg": (239, 255, 0), "bg": (90, 95, 2)},
        Segment.FILLER: {"fg": (25, 61, 85)},
        # dollar styles are ignored for now.
        Segment.DOLLAR: {"fg": (239, 41, 41)},
        "snip_char": {"char": Ellipses.large_dot, "fg": "red"},
        "filler_char": {"char": Ellipses.small_dot},
    },
    "Remote": {
        Segment.SINK: {"fg": (252, 175, 62), "bg": (74, 70, 0)},
        Segment.USER: {"fg": (204, 0, 0), "bg": "", "italic": True},
        Segment.PATH: {"fg": (252, 175, 62), "bg": ""},
        Segment.SSH: {"fg": (204, 0, 0), "bg": (66, 12, 5)},
        Segment.TIME: {"fg": "red", "bg": ""},
        Segment.PIPENV: {"fg": (70, 204, 64), "bg": (36, 135, 75)},
        Segment.BRANCH: {"fg": (252, 175, 62)},
        Segment.VIRTUAL: {"fg": (70, 204, 64), "bg": (25, 94, 52)},
        Segment.POETRY: {"fg": (70, 204, 64), "bg": (25, 94, 52)},
        Segment.NIX: {"fg": "white", "blue": "88"},
        Segment.VENV: {"fg": (239, 255, 0), "bg": (90, 95, 2)},
        Segment.FILLER: {"fg": (65, 65, 65)},
        Segment.DOLLAR: {"fg": (204, 0, 0), "bg": (0, 0, 0)},
        "snip_char": {"char": Ellipses.large_square},
        "filler_char": {"char": Ellipses.small_dot},
    },
}


def error(message: str | Exception, exit: bool = True) -> None:
    print(f"Error: {message}")
    print(">")
    if exit:
        sys.exit(1)


def clamp(val: int | float, minimum: int = 0, maximum: int = 255) -> int | float:
    """Clamp a value between a minimum and maximum value"""
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return val


def hex_to_rgb(hex_string: str) -> tuple[int, int, int]:
    """Convert a hex string to an RGB tuple

    Return a tuple of red, green and blue components for the color
    given as #rrggbb.
    """
    if hex_string.startswith("#"):
        hex_string = hex_string[1:]

    if len(hex_string) != 6:
        raise IndexError(
            "hex string must have 6 characters starting with an optional # symbol"
        )

    rgb: list[int] = []
    for i in range(0, 6, 2):
        hex_part = hex_string[i : i + 2]
        hex_int = int(hex_part, 16)
        rgb.append(hex_int)

    return (rgb[0], rgb[1], rgb[2])


def colorscale(hexstr: str, scalefactor: float) -> str:
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.

    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    >>> colorscale("#52D24F", 1.6)
    #83FF7E
    >>> colorscale("#4F75D2", 1)
    #4F75D2
    """

    hexstr = hexstr.strip("#")

    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr

    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)

    r = int(clamp(r * scalefactor))
    g = int(clamp(g * scalefactor))
    b = int(clamp(b * scalefactor))

    return "#%02x%02x%02x" % (r, g, b)


def find_sink_yaml(dirname: str) -> str | None:
    project_file = "sink.yaml"
    try:
        names = os.listdir(dirname)
    except PermissionError:
        return None
    if project_file in names:
        return os.path.realpath(os.path.join(dirname, project_file))
    if dirname == "/":
        return None
    parent = os.path.realpath(os.path.join(dirname, ".."))
    return find_sink_yaml(parent)


def urlize(text: str, url: str) -> str:
    r"""Create a clickable link for the terminal

    Info for gnome-terminal clickable links:
    https://unix.stackexchange.com/a/437585
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda

    Adding the hostname to the url works but doesn't appear to matter.
    '\e]8;;file://{}{}\a{}\\e]8;;\a'.format(socket.gethostname(), url, text)
    """
    # return r'\e]8;;file://{}\a{}\e]8;;\a'.format(url, text)
    return r"\e]8;;{}\a{}\e]8;;\a".format(url, text)


def snip(string: str, length: int, sep: str, position: float = 0.5) -> tuple[str, str]:
    """Split a string at the position of a separator and return the two parts.

    :param string: The string to split.
    :param length: The length of the string to return.
    :param sep: The separator to use between the two parts of the string.
    :param position: The position of the separator.
    """
    if len(string) <= length:
        return (string, "")

    sep_length = len(sep)
    sep_position = int(length * position)
    sep_position = (
        sep_position - sep_length
        if sep_position + sep_length > length
        else sep_position
    )
    start = string[:sep_position]
    end = string[sep_position + sep_length - length :]
    # snipped = start + sep + end
    return start, end


class Chunks:
    HOME: str = os.environ.get("HOME", "")
    IS_SSH: str = os.environ.get("SSH_CLIENT", "")

    def __init__(self) -> None:
        ssh_location = "Remote" if self.IS_SSH else "Local"
        self.theme = self._get_theme(ssh_location)
        self.segment_lengths: list[int] = []
        _, self.columns = os.popen("stty size", "r").read().split()
        try:
            self.snip_char = self.theme["snip_char"]["char"]
        except KeyError:
            self.snip_char = Ellipses.large_square
        try:
            self.filler_char = self.theme["filler_char"]["char"]
        except KeyError:
            self.filler_char = Ellipses.hr

    def _get_theme(self, theme_name: str) -> dict[Any, Any]:
        theme = {}
        try:
            theme = themes[theme_name]
        except KeyError:
            error(f'Theme "{theme_name}" not found.')
        return theme

    def _add_length(self, chars: str) -> None:
        length = len(chars)
        self.segment_lengths.append(length)

    def _get_length(self, extra: str = "") -> int:
        """Get the leftover space on the terminal.

        get the number of elements in self.NON_PATH_LENGTH and the sum of the
        elements to account for a single space between elements.
        """
        # rows, columns = os.popen("stty size", "r").read().split()
        non_path_length = len(self.segment_lengths) + sum(self.segment_lengths)
        max_len = (int(self.columns)) - non_path_length - len(extra)
        return max_len

    def _theme(
        self,
        segment: Segment,
        chunks: tuple[str, ...],
        no_brackets: bool = False,
        split_char: str = "",
        extra: tuple[str, dict[str, Any]] | None = None,
    ) -> str:
        """Apply theming to a given segment and its chunks.

        This method styles the provided chunks based on the theme settings for the
        specified segment. It handles special cases for the SINK and PATH segment and
        applies additional styling if extra parameters are provided.

        Chunks always have a length of one except for the PATH segment which can
        be split in two and if so, a split_char is used to separate the two parts.

        Args:
            segment (Segment): The segment to be themed.
            chunks (tuple[str, ...]): The chunks of text to be styled.
            no_brackets (bool, optional): If True, brackets around the chunks will be
                omitted. Defaults to False.
            split_char (str, optional): A character to split the chunks. Defaults to "".
            extra (tuple[str, dict[str, Any]] | None, optional): Additional characters and
                their styling to be appended to the chunks. Defaults to None.

        Returns:
            str: The styled chunk as a string.
        """
        try:
            theme = self.theme[segment]
        except KeyError:
            theme = {}

        # If dollar is styled, it causes errors when text is
        # pasted or the user scrolls back through history.
        if segment == Segment.DOLLAR:
            return chunks[0]

        hide_brackets = True

        # hasattr(Segment, "SINK") and segment == Segment.SINK:
        if segment == Segment.SINK:
            project_name, project_bg, project_fg = self.get_sink_project()

            if not project_name:
                return ""  # not a project

            # get the length of the string before any styles are applied
            # self._add_length(template.format(project_name))
            self._add_length(f"[{project_name}]")

            if project_fg.startswith("#"):
                project_fg = hex_to_rgb(project_fg)
            if project_bg.startswith("#"):
                project_bg = hex_to_rgb(project_bg)

            rendered_chunks = self._style_chunk(
                project_name,
                fg=project_fg,
                bg=project_bg,
                bold=theme.get("bold", False),
                italic=theme.get("italic", False),
                ul=theme.get("underline", False),
                no_brackets=no_brackets,
                hide_brackets=hide_brackets,
            )
        else:
            bg = theme.get("bg", "")
            template = "[{}]"
            if no_brackets or not bg:
                no_brackets = True
                template = "{}"
            # get the length of the string before any styles are applied
            self._add_length(template.format("".join(chunks)))
            parts = []
            # for the path chunk since it might be split in two
            for chunk in chunks:
                rendered_chunk = self._style_chunk(
                    chunk,
                    fg=theme.get("fg", ""),
                    bg=bg,
                    bold=theme.get("bold", False),
                    italic=theme.get("italic", False),
                    ul=theme.get("underline", False),
                    no_brackets=no_brackets,
                    hide_brackets=hide_brackets,
                )
                if rendered_chunk:
                    parts.append(rendered_chunk)
            snip_theme = self.theme.get("snip_char", {})
            if split_char:
                fancy_char = self._style_chunk(
                    split_char,
                    fg=snip_theme.get("fg", ""),
                    bg=snip_theme.get(bg, ""),
                )
                rendered_chunks = "".join([parts[0], fancy_char, parts[1]])
            else:
                rendered_chunks = "".join(parts)

            # An extra can be somthing appended to a chunk like a colored dot to indicate git status
            if extra:
                extra_chars = extra[0]
                # minus one char to account for no space between the chunk and the extra
                self._add_length(extra_chars[1:])
                extra_chunk = self._style_chunk(
                    extra_chars,
                    fg=extra[1].get("fg", ""),
                    bg=extra[1].get("bg", ""),
                    bold=extra[1].get("bold", False),
                    italic=extra[1].get("italic", False),
                    ul=extra[1].get("underline", False),
                    no_brackets=no_brackets,
                    hide_brackets=hide_brackets,
                )
                rendered_chunks = "".join([rendered_chunks, extra_chunk])

        return rendered_chunks

    def _style_chunk(
        self,
        chunk: str,
        fg: str | tuple[int, int, int],
        bg: str | tuple[int, int, int],
        bold: bool = False,
        italic: bool = False,
        ul: bool = False,
        hide_brackets: bool = True,
        no_brackets: bool = False,
    ) -> str:
        bracket_fg = fg
        if hide_brackets:
            bracket_fg = bg
        formated_chunk: str = ""
        try:
            bracket_start = click.style(
                "[", fg=bracket_fg, bg=bg, bold=bold, underline=ul, italic=italic
            )
            bracket_end = click.style(
                "]", fg=bracket_fg, bg=bg, bold=bold, underline=ul, italic=italic
            )
            formated_chunk = click.style(
                chunk, fg=fg, bg=bg, bold=bold, underline=ul, italic=italic
            )
        except TypeError as e:
            bracket_start = "["
            bracket_end = "]"
            error(e)
        except NameError:
            bracket_start = "["
            bracket_end = "]"
        except AttributeError:
            bracket_start = "["
            bracket_end = "]"

        if no_brackets:
            complete = formated_chunk
        else:
            complete = "".join([bracket_start, formated_chunk, bracket_end])

        return complete

    @staticmethod
    def get_sink_project() -> tuple[str, str, str]:
        """Get the project name and color from ~/.sink-projects"""
        # TODO: optimize this method
        project_conf = Path("~/.sink-projects").expanduser()
        cur = Path(os.path.curdir).absolute()
        project_name = ""  # cur.name
        project_bg = "blue"
        project_fg = "white"
        try:
            with open(project_conf) as conf:
                reader = csv.reader(conf, delimiter="\t", quotechar='"')
                for row in reader:
                    if not row:
                        continue
                    if row[0].startswith("#"):
                        continue
                    if cur.is_relative_to(row[1]):
                        project_name = row[0]
                        # project_dir = row[1]
                        project_bg = row[2]
                        project_fg = colorscale(project_bg, 3)
                        break
        except FileNotFoundError:
            error("No sink-projects file found.", exit=False)

        # if os.environ.get("KITTY_PID"):
        #     set_kitty_tabs(project_name, project_bg, project_fg)
        # elif os.environ.get("ITERM_SESSION_ID"):
        #     set_item2_tabs(project_name, project_bg, project_fg)

        return (project_name, project_bg, project_fg)

    def get_chunk(self, segment: Segment) -> Any:
        method_name = f"_chunk_{segment.name.lower()}"
        method = getattr(self, method_name, None)
        if method is None:
            error(f"Invalid Chunk: {segment}")
            return None  # to satisfy mypy
        return method()

    def _chunk_invisible(self) -> str:
        # elif os.environ.get("ITERM_SESSION_ID"):
        #     set_item2_tabs(project_name, project_bg, project_fg)
        return "xxx"

    def _chunk_path(self) -> str:
        """Return the current path truncated to fit the leftover terminal width"""
        # find -type d | awk '{ print length, $0 }' | sort -n -s | cut -d" " -f2- | tail -n 10
        path = os.path.abspath(os.path.curdir)
        link_path = "file://{}".format(path)
        path = path.replace(self.HOME, "~")
        path = path.replace(" ", r"\ ")

        # ellipses = self.theme.get("snip_char", Ellipses.large_square)
        max_len = self._get_length(self.snip_char)

        if max_len > len(path):
            if len(path) != 1:
                pretty_path = urlize(self._theme(Segment.PATH, (path,)), link_path)
            else:
                self._add_length(path)
                pretty_path = path  # don't urlize a single character path, ie: ~ or / (it looks bad)
        else:
            self._add_length(path + self.snip_char)
            parts = snip(path, max_len, sep=self.snip_char, position=0.25)

            pretty_path = urlize(
                self._theme(Segment.PATH, parts, split_char=self.snip_char), link_path
            )
            # pretty_path = urlize(self._theme(Segment.PATH, snip_path), link_path)

        return pretty_path

    def _chunk_user(self) -> str:
        # This screws up the character count in _chunk_path when calculating
        # the length of path since it is expanded after the $PS1 is echoed.
        # >>> return r'\u@\H'
        # Use this instead:
        cur_user = os.environ["USER"]
        hostname = socket.gethostname()
        return self._theme(Segment.USER, ("{}@{}".format(cur_user, hostname),))

    def _chunk_sink(self) -> str:
        return self._theme(Segment.SINK, ("",), no_brackets=False)

    def _chunk_time(self) -> str:
        now = datetime.datetime.now()
        formated = now.strftime("%H:%M")
        return self._theme(Segment.TIME, (formated,))

    def _chunk_branch(self) -> str:
        try:
            git_status = subprocess.run(
                [
                    "git",
                    "status",
                    "--porcelain=v1",
                    "--branch",
                    "--untracked-files=no",
                ],
                universal_newlines=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return ""
        if not git_status:
            return ""
        if not git_status.stdout:
            return ""
        if git_status.stdout == "## No commits yet on main\n":
            return ""

        stdout = git_status.stdout
        lines = stdout.splitlines()
        # parse lines[0]: '## main...origin/main'
        branch = lines[0][3:].split("...")[0]

        clean = len(lines[1:]) == 0
        color = "green" if clean else "red"
        extra = (Ellipses.large_dot, {"fg": color})
        branch = self._theme(Segment.BRANCH, (branch,), extra=extra)

        return branch

    def _chunk_virtual(self) -> str:
        """Requires sudo to work"""
        # TODO: find a better way to detect virtualization
        return ""
        # virt = ""
        # try:
        #     out = subprocess.run(
        #         ["sudo", "virt-what"], universal_newlines=True, stdout=subprocess.PIPE
        #     )
        #     virt = " ".join(out.stdout.split())
        # except FileNotFoundError:
        #     pass
        # if virt == "virtualbox":
        #     virt = "vbox"
        # return self._theme(Segment.VIRTUAL, virt)

    def _chunk_venv(self) -> str:
        venv = os.getenv("VIRTUAL_ENV", "")
        poetry = os.getenv("POETRY_ACTIVE", "")
        chunk = ""
        if venv and not poetry:
            venv = os.path.basename(venv)
            venv = self._theme(Segment.VENV, (venv,))
            chunk = venv
        return chunk

    def _chunk_poetry(self) -> str:
        poetry = os.getenv("POETRY_ACTIVE", "")
        if poetry:
            poetry = self._theme(Segment.POETRY, ("Poetry",))
        return poetry

    def _chunk_nix(self) -> str:
        nix = os.getenv("NIX_STORE", "")
        if nix:
            nix = self._theme(Segment.NIX, ("Nix",))
        return nix

    def _chunk_ssh(self) -> str:
        ssh_envoment = os.getenv("SSH_CLIENT", "")
        if ssh_envoment:
            ssh_envoment = self._theme(Segment.SSH, ("ssh",))
        return ssh_envoment

    def _chunk_pipenv(self) -> str:
        pipenv = os.getenv("PIPENV_ACTIVE", "")
        if pipenv:
            pipenv = self._theme(Segment.PIPENV, (pipenv,))
        return pipenv

    # def _chunk_ddev(self) -> str:
    #     ddev = os.getenv("DDEV_SITENAME", "")
    #     if ddev:
    #         ddev = self._theme(Segment.DDEV, (ddev,))
    #     return ddev

    def _chunk_filler(self) -> str:
        # char = self.theme.get("filler_char", Ellipses.hr)  # Can be any number if chars
        count = (self._get_length() // len(self.filler_char)) - 1
        segment = self.filler_char * count
        if not segment:
            return ""
        return self._theme(Segment.FILLER, (segment,))

    def _chunk_dollar(self) -> str:
        dollar_sign = "\n❖ "
        return self._theme(Segment.DOLLAR, (dollar_sign,), no_brackets=True)


def set_item2_tabs(project_name: str, project_bg: str, project_fg: str) -> None:
    r"""Set the tab title.

    Make sure that:
    1. profiles > general > title, has everything unchecked.
    2. profiles > general > window > custom tab title, is unset.

    https://iterm2.com/documentation-escape-codes.html

    Test:
    echo -ne "\e]1;this is the title\a"
    """
    # print(r"\e]1;this is the title\a")
    template = r"\e]1;{}\a"
    if not project_name:
        project_name = os.path.abspath(os.path.curdir)
        print(template.format(project_name))
    else:
        print(template.format(project_name))
    # project_name = project_name[10:]
    # print(project_fg, project_bg)
    # project_name = "" # "\033]6;1;bg;red;brightness;255\a"
    # cmd = ["echo", "-ne", rf"\e]1;{project_name}\a"]
    # subprocess.Popen(cmd)


def set_kitty_tabs(project_name: str, project_bg: str, project_fg: str) -> None:
    """Set the kitty terminal tab colors and title"""

    # default no project tab colors
    base_color = "#ffffff"
    all_colors = [
        f"active_fg={base_color}",
        "active_bg=" + colorscale(base_color, 0.3),
        "inactive_fg=" + colorscale(base_color, 0.8),
        "inactive_bg=" + colorscale(base_color, 0.0),
    ]
    if project_name:
        colors = {
            "active_fg": colorscale(project_fg, 1.0),
            "active_bg": colorscale(project_bg, 1.0),
            "inactive_fg": colorscale(project_fg, 1.0),
            "inactive_bg": colorscale(project_bg, 0.0),
        }
        all_colors = [f"{k}={v}" for k, v in colors.items()]
    color_cmd = ["kitten", "@", "set-tab-color"] + all_colors
    title_cmd = ["kitten", "@", "set-tab-title", project_name]
    # use the blocking `call` instead of `popen` which doesn't wait for
    # the command to finish and that causes the terminal to get messed up.
    subprocess.call(title_cmd)
    subprocess.call(color_cmd)


def prompt_help() -> str:
    import textwrap

    help_text = """
    Add this to your .bashrc or .bash_profile:
    
    # load the bash prompt source
    function _prompt_command() {
        export PS1="$($HOME/bin/bashrc_prompt.py)"
    }
    export PROMPT_COMMAND=_prompt_command
    
    Find some long dirs for testing:
    find -type d | awk '{ print length, $0 }' | sort -n -s | cut -d" " -f2- | tail -n 10"""

    formated = textwrap.dedent(help_text)
    formated = textwrap.indent(formated, "  ")
    return formated


def ps1_prompt(info: bool = False) -> None:
    if info:
        print()
        click.secho("Info", fg="bright_yellow", bold=True)
        print(prompt_help())
        print()
        click.secho("Themes", fg="bright_yellow", bold=True)
        for theme in themes:
            print()
            click.secho(f"  {theme}", fg="bright_yellow")
            for k, v in themes[theme].items():
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
                print(f"    {colored}", v)
        print()
        this = os.path.basename(__file__)
        click.secho(f"{this} version: {__version__}", fg="bright_yellow")
        click.secho(__file__, fg="bright_yellow")
    else:
        c = Chunks()
        right_segments = left_segments = last_segments = []
        try:
            left_segments = [
                Segment.POETRY,
                Segment.PIPENV,
                Segment.SINK,
                Segment.BRANCH,
                Segment.USER,
                Segment.VENV,
                Segment.NIX,
                Segment.SSH,
                Segment.PATH,
                Segment.FILLER,
            ]
            right_segments = [
                Segment.TIME,
            ]
            last_segments = [
                Segment.DOLLAR,
            ]
        except AttributeError as e:
            error(e, exit=True)

        # the right segments need to be build first so their sizes are
        # added to the Chunks.segment_lengths list before the filler
        # segment calculates the leftover space.
        right = " ".join(filter(None, [c.get_chunk(i) for i in right_segments]))
        left = " ".join(filter(None, [c.get_chunk(i) for i in left_segments]))
        last = " ".join(filter(None, [c.get_chunk(i) for i in last_segments]))
        # invisible = c.get_chunk(Segment.INVISIBLE)
        # line = f"{invisible}{left} {right}{last}"
        line = f"{left} {right}{last}"
        print()
        print(line)


# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         main(True)
#     else:
#         main()