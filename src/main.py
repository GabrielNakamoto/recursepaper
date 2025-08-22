import dearpygui.dearpygui as dpg
from entity import Entity
from paperclient import PaperClient
from arxivclient import ArxivClient

# TODO: images from wikipedia?, tree visualization, pdf zooming

def main():
	dpg.create_context()

	PaperClient()
	ArxivClient()

	dpg.create_viewport(title='Recurse Paper', width=1600, height=800)
	dpg.setup_dearpygui()
	dpg.show_viewport()
	dpg.start_dearpygui()
	dpg.destroy_context()


if __name__ == "__main__":
    main()
