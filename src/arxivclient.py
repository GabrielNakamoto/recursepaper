import glob
import arxiv
import dearpygui.dearpygui as dpg

class ArxivClient:
	def __init__(self):
		self.inner = arxiv.Client()
		self.results = []
		with dpg.window(label="Arxiv Search", tag="arxiv-search", width=400, height=500, pos=[625,200]):
			dpg.add_input_text(label="Paper Title", tag="arxiv-title")
			dpg.add_input_text(label="Category", tag="arxiv-cat")
			dpg.add_button(label="Search", callback=self.search)
			dpg.add_separator()
			dpg.add_text("Results:")
			dpg.add_text("", tag="arxiv-result-status")

	def search(self):
		title = dpg.get_value("arxiv-title")
		cat = dpg.get_value("arxiv-cat")
		for x in self.results:
			dpg.delete_item(x)
		self.results = []
		for r in self.inner.results(arxiv.Search(query=f'ti:{title}+AND+cat:{cat}', max_results=5)):
			self.results.append(r.title)
			dpg.add_button(label=r.title, tag=r.title, parent="arxiv-search", callback=self.button_callback, user_data=r)
			# dpg.add_text(r.title, parent="arxiv-search")
		dpg.set_value("arxiv-result-status", f"Found {len(self.results)} papers")

	def button_callback(self, sender, app_data, user_data):
		user_data.download_pdf(dirpath='./papers')
		dpg.configure_item("paper-chooser", items=glob.glob('../papers/*.pdf'))

