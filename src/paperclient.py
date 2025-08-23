import os
import os.path as path
import glob
import dearpygui.dearpygui as dpg
from entity import Entity
from paper import Paper 

PAPER_PATH = path.abspath(path.join(path.dirname(__file__), os.pardir, 'papers'))

class PaperClient:
	def __init__(self):
		self.current_paper = None
		self.selected_filename = None

		with dpg.window(label="Paper client", tag="paper-client", width=400, height=100, pos=[625,50]):
			dpg.add_text("Choose research paper:")
			dpg.add_combo(items=glob.glob(os.path.join(PAPER_PATH, '*.pdf')), tag="paper-chooser", callback=self.choose_paper)
			dpg.add_button(label="Load selected paper", callback=self.load_paper)

		dpg.add_window(label="Viewer", tag="viewer_window", width=600, height=800)
		with dpg.texture_registry():
			dpg.add_raw_texture(width=612, height=794, tag="texture_tag", default_value=[])
			dpg.add_image("texture_tag", parent="viewer_window")

	def choose_paper(self, sender, app_data):
		self.selected_filename = app_data.split('/')[-1]

	def cancel_choice(self):
		self.selected_filename = None
		self.current_paper = None

	def load_paper(self):
		if self.selected_filename == None:
			print("No paper currently selected")
			return
		dpg.set_value("paper-chooser", "")

		if self.current_paper != None:
			self.current_paper.save()
			self.current_paper.close()

		paper = Paper(self.selected_filename, self.cancel_choice)
		paper.update_entities()
		paper.update_texture()

		with dpg.handler_registry():
			dpg.add_key_press_handler(dpg.mvKey_J, callback=paper.base_move, user_data=1)
			dpg.add_key_press_handler(dpg.mvKey_K, callback=paper.base_move, user_data=0)
			dpg.add_key_press_handler(ord('='), callback=paper.base_zoom, user_data=1.0)
			dpg.add_key_press_handler(ord('-'), callback=paper.base_zoom, user_data=-1.0)
		self.current_paper = paper

