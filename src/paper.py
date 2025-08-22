import os
import pymupdf
from entity import Entity
import dearpygui.dearpygui as dpg
import pickle

PAPER_PATH = '../papers'
ENTITY_PATH = '../entities'

class Paper:
	def __init__(self, filename, id_="x1"):
		self.filename = filename
		self.filehead = ''.join(filename.split('.')[:-1])
		self.img_dir = os.path.join(PAPER_PATH, self.filehead + '_imgs')
		self.entpath = os.path.join(ENTITY_PATH, self.filehead + ".entities")
		self.doc = pymupdf.open(os.path.join(PAPER_PATH, filename))
		self.id_ = id_
		self.pages = self.doc.page_count
		self.pn = 0

		self.root_entities = []

		if not os.path.exists(self.img_dir):
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
		if lpn != None: dpg.delete_item(self.root_entities[lpn].wtag)
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
		buffers = 0.0
		for page in self.doc:
			text = page.get_text()
			sb = []
			if len(text) <= 3000:
				sb.append(text)
			else:
				while len(text) > 3000:
					sb.append(text[:3000])
					text = text[3000:]
			buffers += len(sb)
			pages.append(sb)
		
		with dpg.window(label="Paper Load Progress", tag="pbar_window", width=300, height=10, pos=[1300,0]):
			dpg.add_progress_bar(tag="pbar", default_value=0.0, width=250, indent=25)
		j = 0.0
		for i, page in enumerate(pages):
			children = []
			for b in page:
				j += 1.0
				children += Entity.dandelion_extract(b, f"Page-{i} Root Entity")
				dpg.set_value("pbar", j / buffers)
			root = Entity(f"Page-{i} Root Entity", "", "", children=children)
			root.propogate_paper_ptr(self)
			self.root_entities.append(root)
		dpg.delete_item("pbar_window")

	def save(self):
		print(f"Requested entity cache to {self.entpath}...")
		pickle.dump(self.root_entities, open(self.entpath, 'wb'))


