import glob
import webbrowser
import os
import os.path as path
import arxiv
import dearpygui.dearpygui as dpg

PAPER_PATH = path.abspath(path.join(path.dirname(__file__), os.pardir, 'papers'))

class ArxivClient:
	def __init__(self):
		self.inner = arxiv.Client()
		self.results = []
		with dpg.window(label="Arxiv Search", tag="arxiv-search", width=400, height=500, pos=[625,250]):
			dpg.add_input_text(label="Paper Title", tag="arxiv-title")
			dpg.add_input_text(label="Category (optional)", tag="arxiv-cat")
			dpg.add_button(label="See valid categories", callback=lambda:webbrowser.open('https://arxiv.org/category_taxonomy'))
			dpg.add_slider_int(label="Max results", tag="arxiv-max_results", min_value=1, max_value=25, default_value=10)
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
		query= f'ti:{title}+AND+cat:{cat}' if cat != "" else f'ti:{title}'
		print("ArXiv query:", query)
		for r in self.inner.results(arxiv.Search(query=query, max_results=dpg.get_value("arxiv-max_results"))):
			self.results.append(r.title)
			dpg.add_button(label=r.title+f' [{r.primary_category}]', tag=r.title, parent="arxiv-search", callback=self.button_callback, user_data=r)
			with dpg.tooltip(r.title): dpg.add_text(r.summary)
			# dpg.add_text(r.title, parent="arxiv-search")
		dpg.set_value("arxiv-result-status", f"Found {len(self.results)} papers")
		print(f"Found {len(self.results)} papers")

	def button_callback(self, sender, app_data, user_data):
		filepath = user_data.download_pdf(dirpath='./papers')
		filename = filepath.split('/')[-1]
		dpg.configure_item("paper-chooser", items=glob.glob(os.path.join(PAPER_PATH, '*.pdf')))
		dpg.set_value("paper-chooser", os.path.join(PAPER_PATH, filename))
