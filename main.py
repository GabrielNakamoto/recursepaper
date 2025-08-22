import os
import glob
from dataclasses import dataclass
import pickle
import requests
import webbrowser
import pymupdf
import dearpygui.dearpygui as dpg
import arxiv

# Recursive entity extraction??, extract entities from expanded abstracts in new window
# TODO: Entity class, arxiv search, file system to organize all file types, llm integration, images from wikipedia?, tree visualization, pdf zooming, recursive serialization


# serialize paper when opening a new one or closing the whole application

def dandelion_entity_extract(buffer, parent, found=None, depth=0):
	print("Dandelion API call from parent:", parent)
	entities = set()
	refs = dict()

	payload = {"text":buffer, "token":os.environ['DAND_TOKEN'], "min_confidence":0.7, "include":"abstract"}
	url = "https://api.dandelion.eu/datatxt/nex/v1"
	response = requests.get(url, params=payload)
	json = response.json()
	try:
		for x in json['annotations']:
			entities.add((x['label']))
			refs[x['label']]=(x['uri'], x['abstract'])
	except  KeyError as e:
		print("Key error", e)
		print(json)

	if found != None:
		for e in found:
			entities.discard(e)
		found |= entities

	return [Entity(e, refs[e][0], refs[e][1], parent, found=found, depth=depth) for e in entities]

class Entity:
	def __init__(self, name, url, abstract, paper=None, parent=None, found=None, depth=0, children=None):
		self.paper = paper if paper else parent.paper
		self.name = name
		self.abstract = abstract
		self.url = url
		self.parent = parent
		self.depth = depth
		self.found = found
		self.children = children
		self.wtag = f"{self.name}_depth={self.depth}"

	def __getstate__(self):
		state = {
			attr: getattr(self, attr)
			for attr in self.__dict__
			if attr != 'paper'
		}
		return state

	def __setstate__(self, state):
		# When unpickling, restore the state based on the 'state' dictionary
		self.__dict__.update(state)
		# Handle the excluded attribute if needed (e.g., set a default value)
		if 'paper' not in self.__dict__:
			self.paper = None # Or any other default value

	def propogate_paper_ptr(self, paper):
		self.paper = paper
		if self.children == None:
			return
		for c in self.children:
			c.propogate_paper_ptr(paper)

	def render_child_layer(self):
		with dpg.window(label=self.name, tag=self.wtag):
			dpg.add_input_text(label="Search", tag=f"{self.name}_depth={self.depth}_search", callback=self.search)
			dpg.add_button(label="clear search", callback=self.clear)
			with dpg.filter_set(tag=f"{self.name}_depth={self.depth}_filter_set"):
				for e in self.children:
					e.render_summary()

	def render_summary(self):
		with dpg.collapsing_header(
			label=self.name,
			tag=self.wtag + "_summary",
			filter_key=self.name,
			parent=f"{self.parent}_depth={self.depth-1}_filter_set"
		):
			dpg.add_text(self.abstract, wrap=350)
			dpg.add_button(label="Wiki page", callback=self.clicked)
			dpg.add_button(label="Recurse entity extract", callback=self.expand)

	def clear(self):
		dpg.set_value(f"{self.name}_depth={self.depth}_filter_set", "")
		dpg.set_value(f"{self.name}_depth={self.depth}_search", "")

	def search(self, sender, app_data):
		dpg.set_value(self.name + "_filter_set", app_data)

	def expand(self):
		print(f"Expanding entity: {self.name}, wtag: {self.wtag}")
		if self.children == None:
			self.children = dandelion_entity_extract(self.abstract, self.name, found=self.found, depth=self.depth+1)
			# request serialization from top level paper
			self.paper.save()
		self.render_child_layer()
	
	def clicked(self):
		webbrowser.open(self.url)

class Paper:
	def __init__(self, filename, id_="x1"):
		self.filename = filename
		self.filehead = ''.join(filename.split('.')[:-1])
		self.img_dir = os.path.join('papers', self.filehead + '_imgs')
		self.entpath = os.path.join("entities", self.filehead + ".entities")
		self.doc = pymupdf.open(os.path.join('papers', filename))
		self.id_ = id_
		self.pages = self.doc.page_count
		self.pn = 0

		self.root_entities = []
		self.cache_images()

		if os.path.exists(self.entpath):
			print(f"Loading entities from {self.entpath}...")
			self.root_entities = pickle.load(open(self.entpath, 'rb'))
			for e in self.root_entities:
				e.propogate_paper_ptr(self)
		else:
			print("Extracting entities...")
			self.extract_entities()
			print("Serializing entities...")
			pickle.dump(self.root_entities, open(self.entpath, 'wb'))

	def update_texture(self):
		_, _, _, data = dpg.load_image(os.path.join(self.img_dir, f"page-{self.pn}.png"))
		dpg.set_value("texture_tag", data)

	def update_entities(self, lpn=None):
		if lpn != None:
			dpg.delete_item(self.root_entities[lpn].wtag)
		self.root_entities[self.pn].render_child_layer()

	def down(self):
		lpn = self.pn
		if self.pn < self.pages-1: self.pn += 1
		self.update_texture()
		self.update_entities(lpn)

	def up(self):
		lpn = self.pn
		if self.pn > 0: self.pn -= 1
		self.update_texture()
		self.update_entities(lpn)

	def cache_images(self):
		if not os.path.exists(self.img_dir):
			os.mkdir(self.img_dir)
			for page in self.doc:
				pmap = page.get_pixmap()
				pmap.save(os.path.join(self.img_dir, f"page-{page.number}.png"))
	
	def extract_entities(self):
		pages = []
		for page in self.doc:
			text = page.get_text()
			sb = []
			if len(text) <= 3000:
				sb.append(text)
			else:
				while len(text) > 3000:
					sb.append(text[:3000])
					text = text[3000:]
			pages.append(sb)

		for i, page in enumerate(pages):
			children = []
			for b in page: children += dandelion_entity_extract(b, f"Page-{i} Root Entity")
			self.root_entities.append(Entity(f"Page-{i} Root Entity", "", "", children=children, paper=self))

	def save(self):
		print(f"Requested entity cache to {self.entpath}...")
		pickle.dump(self.root_entities, open(self.entpath, 'wb'))

class PaperClient:
	def __init__(self):
		self.current_paper = None
		self.selected_filename = None
		with dpg.window(label="Paper client", tag="paper-client", width=400, height=100, pos=[625,50]):
			dpg.add_text("Choose research paper:")
			dpg.add_combo(items=glob.glob('papers/*.pdf'), tag="paper-chooser", callback=self.choose_paper)
			dpg.add_button(label="Load selected paper", callback=self.load_paper)

		dpg.add_window(label="Viewer", tag="viewer_window", width=600, height=800)
		# dpg.add_window(label="Entities", tag="entity_window", width=500, height=700, pos=[1050,50])

		with dpg.texture_registry():
			dpg.add_dynamic_texture(width=612, height=792, tag="texture_tag", default_value=[])

	def choose_paper(self, sender, app_data):
		self.selected_filename = app_data.split('/')[-1]

	def load_paper(self):
		if self.selected_filename == None:
			print("No paper currently selected")
			return
		if self.current_paper != None:
			self.current_paper.save()

		paper = Paper(self.selected_filename)
		paper.update_entities()
		paper.update_texture()
		with dpg.handler_registry():
			dpg.add_key_press_handler(dpg.mvKey_J, callback=paper.down)
			dpg.add_key_press_handler(dpg.mvKey_K, callback=paper.up)
		self.current_paper = paper
		dpg.add_image("texture_tag", parent="viewer_window")

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
		dpg.configure_item("paper-chooser", items=glob.glob('papers/*.pdf'))

dpg.create_context()
pc = PaperClient()
ac = ArxivClient()

dpg.create_viewport(title='Recurse Paper', width=1600, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
