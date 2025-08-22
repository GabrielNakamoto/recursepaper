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

def dandelion_entity_extract(buffer):
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

	return (entities, refs)

@dataclass
class Entity:
		name: str
		abstract: str
		url: str

class Paper:
	def __init__(self, filename, id_="x1"):
		self.filename = filename
		self.filehead = ''.join(filename.split('.')[:-1])
		self.img_dir = os.path.join('papers', self.filehead + '_imgs')
		self.entity_filename = os.path.join("entities", self.filehead + ".entities")
		self.entity_refs_filename = os.path.join("entities", self.filehead + ".erefs")
		self.doc = pymupdf.open(os.path.join('papers', filename))
		self.id_ = id_
		self.pages = self.doc.page_count
		self.pn = 0

		self.cache_images()

		if os.path.exists(self.entity_filename) and os.path.exists(self.entity_refs_filename):
			print(f"Loading entities from {self.entity_filename} and {self.entity_refs_filename}...")
			self.entities = pickle.load(open(self.entity_filename, 'rb'))
			self.entity_refs = pickle.load(open(self.entity_refs_filename, 'rb'))
		else:
			print("Extracting entities...")
			self.entities = [set() for _ in range(self.pages)]
			self.entity_refs = [dict() for _ in range(self.pages)]
			self.extract_entities()
			print("Serializing entities...")
			pickle.dump(self.entities, open(self.entity_filename, 'wb'))
			pickle.dump(self.entity_refs, open(self.entity_refs_filename, 'wb'))

	def update_texture(self):
		_, _, _, data = dpg.load_image(os.path.join(self.img_dir, f"page-{self.pn}.png"))
		dpg.set_value("texture_tag", data)

	def update_entities(self):
		dpg.delete_item("entity_window", children_only=True)
		Paper.build_entity_window(self.entities[self.pn], self.entity_refs[self.pn], "entity_window")

	@staticmethod
	def search_callback(sender, app_data, user_data):
		dpg.set_value(user_data + "_filter_set", app_data)

	@staticmethod
	def clear_callback(sender, app_data, user_data):
		dpg.set_value(f"{user_data}_filter_set", "")
		dpg.set_value(f"{user_data}_search", "")

	@staticmethod
	def build_entity_window(entities, refs, parent, depth=0, found=None):
		if found == None:
			found = set(entities)
		dpg.add_input_text(label="Search", tag=f"{parent}_search", parent=parent, callback=Paper.search_callback, user_data=parent)
		dpg.add_button(label="clear search", parent=parent, callback=Paper.clear_callback, user_data=parent)
		with dpg.filter_set(tag=f"{parent}_filter_set", parent=parent):
			for entity in entities:
				url, abstract = refs[entity]
				with dpg.collapsing_header(label=entity, tag=f'{entity}_depth={depth}', filter_key=entity, parent=f"{parent}_filter_set"):
					dpg.add_text(abstract, wrap=350)
					dpg.add_button(label="Wiki page", callback=Paper.entity_callback, user_data=url)
					dpg.add_button(label="Recurse entity extract", callback=Paper.recurse_extraction, user_data=(depth+1, entity, abstract, found))

	@staticmethod
	def recurse_extraction(sender, app_data, user_data):
		depth, parent_entity, abstract, found = user_data
		entities, refs = dandelion_entity_extract(abstract)
		for e in found:
			entities.discard(e)
		found = found.union(entities)
		dpg.add_window(label=parent_entity, tag=f"{parent_entity}_depth={depth}")

		Paper.build_entity_window(entities, refs, f"{parent_entity}_depth={depth}", depth=depth+1, found=found)

	@staticmethod
	def entity_callback(sender, app_data, user_data):
		webbrowser.open(user_data)

	def down(self):
		if self.pn < self.pages-1: self.pn += 1
		self.update_texture()
		self.update_entities()

	def up(self):
		if self.pn > 0: self.pn -= 1
		self.update_texture()
		self.update_entities()

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
			for b in page:
				entities, refs = dandelion_entity_extract(b)
				self.entities[i] |= entities
				self.entity_refs[i] |= refs

class PaperClient:
	def __init__(self):
		self.current_paper = None
		self.selected_filename = None
		pdfs = 	glob.glob('papers/*.pdf')
		with dpg.window(label="Paper client", tag="paper-client", width=400, height=100, pos=[625,50]):
			dpg.add_text("Choose research paper:")
			dpg.add_combo(items=pdfs, callback=self.choose_paper)
			dpg.add_button(label="Load selected paper", callback=self.load_paper)

		dpg.add_window(label="Viewer", tag="viewer_window", width=600, height=800)
		dpg.add_window(label="Entities", tag="entity_window", width=500, height=700, pos=[1050,50])

		with dpg.texture_registry():
			dpg.add_dynamic_texture(width=612, height=792, tag="texture_tag", default_value=[])

	def choose_paper(self, sender, app_data):
		self.selected_filename = app_data.split('/')[-1]

	def load_paper(self):
		if self.selected_filename == None:
			print("No paper currently selected")
			return

		paper = Paper(self.selected_filename)
		paper.update_entities()
		# with dpg.texture_registry():
			# paper.init_texture()
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
			dpg.add_button(label=r.title, tag=r.title, parent="arxiv-search", callback=lambda a, b, c: c.download_pdf(), user_data=r)
			# dpg.add_text(r.title, parent="arxiv-search")
		dpg.set_value("arxiv-result-status", f"Found {len(self.results)} papers")

dpg.create_context()
pc = PaperClient()
ac = ArxivClient()

dpg.create_viewport(title='Recurse Paper', width=1600, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
