import traceback  # noqa: F401
from nicegui import app, ui  # noqa: F401

from .prompt import colorscale
from .prompt import Chunks

from .projects import read_csv


ui.add_head_html("""
<style>
*{
  font-family: monospace;
}
</style>
""")


# @ui.page("/")
def test() -> None:
    # ui.label("Hello NiceGUI!")

    projects = read_csv()
    # print(projects)
    project = Chunks.get_sink_project()
    print(project)
    return

    dark = ui.dark_mode(True)
    # dark.enable

    with ui.grid(columns=3).style("grid-template-columns: repeat(3, auto)"):
        for name, values in projects.items():
            location = values[0]
            bg_color = values[1]
            # rgb = colorsys.hls_to_rgb(hue, value, saturation)
            # rgb = colorsys.hex_to_rgb(bg_color)
            # fg_color = [round(scale_to_255(i)) for i in rgb]
            fg_color = colorscale(bg_color, 3)

            with ui.label(name).style(
                f"background-color: {bg_color};color: {fg_color};padding: 4px 8px"
            ):
                ui.color_picker(on_pick=lambda e: button.classes(f"!bg-[{e.color}]"))

            ui.label(location)
            ui.label(bg_color)
            # ui.button("Edit", on_click=lambda: edit(name))

    # for url in app.urls:
    #     print(url)
    #     ui.link(url, target=url)

    # ui.run()
    # native=True
    native = False
    # show = True
    show = False
    ui.run(native=native, show=show, reload=False)
