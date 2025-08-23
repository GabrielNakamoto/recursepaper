import pymupdf
from entity import Entity
import dearpygui.dearpygui as dpg
import pickle
import os
import os.path as path

PAPER_PATH = path.abspath(path.join(path.dirname(__file__), os.pardir, 'papers'))
ENTITY_PATH = path.abspath(path.join(path.dirname(__file__), os.pardir, 'entities'))

class Paper:
	def __init__(self, filename, cancel_callback):
		self.cancel_callback = cancel_callback
		self.filename = filename
		self.filehead = ''.join(filename.split('.')[:-1])
		self.img_dir = os.path.join(PAPER_PATH, self.filehead + '_imgs')
		self.entpath = os.path.join(ENTITY_PATH, self.filehead + ".entities")
		self.doc = pymupdf.open(os.path.join(PAPER_PATH, filename))
		self.pages = self.doc.page_count
		self.pn = 0
		self.viewmat = pymupdf.Matrix(1.0,  1.0)

		self.root_entities = []

		for i in range(self.pages): self.save_pixmap(i)

		if not os.path.exists(PAPER_PATH):
			os.mkdir(PAPER_PATH)
		if not os.path.exists(ENTITY_PATH):
			os.mkdir(ENTITY_PATH)

		if os.path.exists(self.entpath):
			print(f"Loading entities from {self.entpath}...")
			self.root_entities = pickle.load(open(self.entpath, 'rb'))
			for e in self.root_entities:
				e.propogate_paper_ptr(self)
		else:
			_, nbuffers = self.bufferize()

			with dpg.window(label="Paper Load API Confirmation", tag="api-confirm"):
				dpg.add_text(f"Paper will require {nbuffers} API tokens")
				dpg.add_button(label="Confirm", callback=self.extract_entities)
				dpg.add_button(label="Cancel", callback=self.close)

	def update_texture(self):
		filepath = os.path.join(self.img_dir, f"page-{self.pn}.png")
		w, h, _, data = dpg.load_image(filepath)
		# print("Loaded pxmap:", filepath, f" {w} * {h}")

		dpg.delete_item("viewer_window", children_only=True)
		dpg.delete_item("texture_tag")
		with dpg.texture_registry():
			dpg.add_raw_texture(width=w, height=h, tag="texture_tag", default_value=data)
			dpg.add_image("texture_tag", parent="viewer_window")
		dpg.configure_item("viewer_window", width=w, height=h)

	def update_entities(self, lpn=None):
		if len(self.root_entities) == 0: return
		if lpn != None:
			self.root_entities[lpn].close()
		self.root_entities[self.pn].render_child_layer()

	def base_zoom(self, sender, app_data, delta):
		a = self.viewmat.a
		b = self.viewmat.d

		self.viewmat = pymupdf.Matrix(a+(delta*0.1), b+(delta*0.1))

		self.save_pixmap()
		self.update_texture()

	def base_move(self, sender, app_data, delta):
		lpn = self.pn
		
		if delta: # move down
			if self.pn < self.pages-1: self.pn += 1
		else: # move up
			if self.pn > 0: self.pn -= 1

		self.save_pixmap()
		self.update_texture()
		self.update_entities(lpn)

	def save_pixmap(self, pn=None):
		if pn == None: pn = self.pn
		if not os.path.exists(self.img_dir):
			os.mkdir(self.img_dir)
		page = self.doc[pn]
		pmap = page.get_pixmap(matrix=self.viewmat)
		filepath = os.path.join(self.img_dir, f"page-{page.number}.png")
		# print("Saving pxmap to:", filepath)
		pmap.save(filepath)

	def bufferize(self):
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

		return (pages, buffers)

	def loaded(self):
		return len(self.root_entities)
	
	def extract_entities(self):
		dpg.delete_item("api-confirm")

		pages, buffers = self.bufferize()

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

		print("Serializing entities...")
		pickle.dump(self.root_entities, open(self.entpath, 'wb'))

		self.update_entities()

	def close(self):
		if dpg.does_item_exist("api-confirm"):
			dpg.delete_item("api-confirm")
			self.cancel_callback()
		dpg.delete_item("viewer_window", children_only=True)
		dpg.delete_item("texture_tag")
		# propogate window closes through entity tree
		for r in self.root_entities:
			r.close()

	def save(self):
		print(f"Requested entity cache to {self.entpath}...")
		pickle.dump(self.root_entities, open(self.entpath, 'wb'))


