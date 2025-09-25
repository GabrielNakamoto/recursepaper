import dearpygui.dearpygui as dpg
import os
from entity import Entity
from paperclient import PaperClient
from arxivclient import ArxivClient

def main():
	if os.environ.get("DAND_TOKEN") == None:
		print("Dandelion API key required")
		print("Get one at https://dandelion.eu/ and set DAND_TOKEN env key")
		return

	dpg.create_context()

	dpg.create_viewport(title='Recurse Paper', width=1600, height=800)
	dpg.setup_dearpygui()
	dpg.show_viewport()

	PaperClient()
	ArxivClient()

	dpg.start_dearpygui()
	dpg.destroy_context()


if __name__ == "__main__":
    main()
