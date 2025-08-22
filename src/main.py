import dearpygui.dearpygui as dpg
from entity import Entity
from paperclient import PaperClient
from arxivclient import ArxivClient

# TODO: images from wikipedia?, tree visualization
# comments for description, dandelion API configuration?, API usage status

# pdf zooming: https://pymupdf.readthedocs.io/en/latest/recipes-images.html#how-to-increase-image-resolution
# pdf term highlighting: https://pymupdf.readthedocs.io/en/latest/page.html#Page.add_highlight_annot

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
