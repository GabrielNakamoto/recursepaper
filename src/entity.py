import requests
import webbrowser
import os
import dearpygui.dearpygui as dpg

class Entity:
	def __init__(self, name, url, abstract, parent=None, found=None, depth=0, children=None):
		self.paper = None
		self.name = name
		self.abstract = abstract
		self.url = url
		self.parent = parent
		self.depth = depth
		self.found = found
		self.children = children
		self.wtag = f"{self.name}_depth={self.depth}"

		self.width = 500 - 50*depth
		self.height = 700 - 50*depth
		self.pos = [1050-20*depth,50+20*depth]

	@staticmethod
	def dandelion_extract(buffer, parent, found=None, depth=1):
		print("Dandelion API call from parent:", parent)
		entities = set()
		refs = dict()

		payload = {"text":buffer, "token":os.environ['DAND_TOKEN'], "min_confidence":0.7, "include":"abstract"}
		url = "https://api.dandelion.eu/datatxt/nex/v1"
		response = requests.get(url, params=payload)

		# TODO: dataclass to display token info to user?
		print(f"Consumed {response.headers['X-DL-units']} tokens")
		print("Remaining tokens: ", response.headers['X-DL-units-left'])
		print("Token reset:", response.headers['X-DL-units-reset'])

		json = response.json()
		try:
			for x in json['annotations']:
				entities.add((x['label']))
				refs[x['label']]=(x['uri'], x['abstract'])
		except  KeyError as e:
			print("Key error", e)
			print(json)

		if found != None:
			for e in found: entities.discard(e)
			found |= entities
		else:
			found = entities

		return [Entity(e, refs[e][0], refs[e][1], parent, found=found, depth=depth) for e in entities]

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
		with dpg.window(label=self.name, tag=self.wtag, width=self.width, height=self.height, pos=self.pos):
			dpg.add_input_text(label="Search", tag=f"{self.name}_depth={self.depth}_search", callback=self.search)
			dpg.add_button(label="clear search", callback=self.clear)
			with dpg.filter_set(tag=self.wtag +"_filter_set"):
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
		dpg.set_value(self.wtag + "_filter_set", "")
		dpg.set_value(self.wtag + "_search", "")

	def search(self, sender, app_data):
		dpg.set_value(self.wtag + "_filter_set", app_data)

	def expand(self):
		print(f"Expanding entity: {self.name}, wtag: {self.wtag}")
		if self.children == None:
			self.children = Entity.dandelion_extract(self.abstract, self.name, found=self.found, depth=self.depth+1)
			self.propogate_paper_ptr(self.paper)
			# request serialization from top level paper
			self.paper.save()
		self.render_child_layer()
	
	def clicked(self):
		webbrowser.open(self.url)

