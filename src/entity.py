import requests
from dataclasses import dataclass
import webbrowser
import os
import dearpygui.dearpygui as dpg


class Entity:
	def __init__(self, name, url, abstract, parent=None, found=None, depth=0, children=[]):
		self.paper = None
		self.name = name
		self.abstract = abstract
		self.url = url
		self.parent = parent
		self.depth = depth
		self.found = found
		self.children = children
		self.suffix = ""
		self.wtag = f"ent:{self.name}_depth={self.depth}"

		self.width = 500 - 50*depth
		self.height = 700 - 50*depth
		self.pos = [1050-20*depth,50+20*depth]

	@staticmethod
	def dandelion_status(response_headers):
		used = float(response_headers['X-DL-units'])
		total_used = used
		remaining = float(response_headers['X-DL-units-left'])
		reset = response_headers['X-DL-units-reset']

		if dpg.does_item_exist("dandelion_status"):
			total_used += float(dpg.get_value("dandelion_total").split(':')[-1])
			dpg.delete_item("dandelion_status")
		with dpg.window(label="Dandelion API Status", tag="dandelion_status"):
			dpg.add_text(f"Tokens consumed: {used}")
			dpg.add_text(f"Total tokens used: {total_used}", tag="dandelion_total")
			dpg.add_text(f"Tokens remaining: {remaining}")
			dpg.add_text("Next reset: "+reset)

	@staticmethod
	def dandelion_extract(buffer, parent, found=None, depth=1):
		print("Dandelion API call from parent:", parent)
		entities = set()
		refs = dict()

		payload = {"text":buffer, "token":os.environ['DAND_TOKEN'], "min_confidence":0.7, "include":"abstract"}
		url = "https://api.dandelion.eu/datatxt/nex/v1"
		response = requests.get(url, params=payload)

		Entity.dandelion_status(response.headers)

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
		if len(self.children) == 0:
			return
		for c in self.children:
			c.propogate_paper_ptr(paper)

	def render_child_layer(self):
		with dpg.window(label=self.name, tag=self.wtag+self.suffix, width=self.width, height=self.height, pos=self.pos):
			dpg.add_input_text(label="Search", tag=self.wtag+self.suffix+"_search", callback=self.search)
			dpg.add_button(label="clear search", callback=self.clear)
			with dpg.filter_set(tag=self.wtag+self.suffix+"_filter_set"):
				for e in self.children:
					e.render_summary()
					if e.cached(): e.render_child_layer()

	def render_summary(self):
		with dpg.collapsing_header(
			label=self.name,
			filter_key=self.name,
			parent=self.parent
		):
			dpg.add_text(self.abstract, wrap=350)
			dpg.add_button(label="Wiki page", callback=self.clicked)
			dpg.add_button(label="Recurse entity extract", callback=self.expand)

	def close(self):
		#  close children first
		for e in self.children:
			e.close()
		if dpg.does_item_exist(self.wtag+self.suffix):
			dpg.delete_item(self.wtag+self.suffix)
			# hacky tag fix to give dpg time for cleanup
			self.suffix += "x"
			# if self.suffix == "x" * 10: self.suffix = ""

	def clear(self):
		dpg.set_value(self.wtag+self.suffix+"_filter_set", "")
		dpg.set_value(self.wtag+self.suffix+"_search", "")

	def search(self, sender, app_data):
		dpg.set_value(self.wtag+self.suffix+"_filter_set", app_data)

	def cached(self):
		return len(self.children)

	def expand(self):
		print(f"Expanding entity: {self.name}, wtag: {self.wtag}")
		if len(self.children) == 0:
			self.children = Entity.dandelion_extract(self.abstract, self.wtag+self.suffix, found=self.found, depth=self.depth+1)
			self.propogate_paper_ptr(self.paper)
			# request serialization from top level paper
			self.paper.save()
		self.render_child_layer()
	
	def clicked(self):
		webbrowser.open(self.url)

