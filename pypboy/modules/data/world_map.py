import pygame
import pypboy
import config

from pypboy.modules.data import entities

_RADIUS = 0.005


class Module(pypboy.SubModule):

	label = "World Map"

	def __init__(self, *args, **kwargs):
		super(Module, self).__init__(*args, **kwargs)
		self._city_keys = list(config.CITIES.keys())
		self._city_idx = 0

		self.mapgrid = entities.Map(480, pygame.Rect(4, 120, config.WIDTH - 8, config.HEIGHT - 80))
		self.mapgrid.rect[0] = 4
		self.mapgrid.rect[1] = 40
		self.add(self.mapgrid)
		self._fetch_current()

	def _fetch_current(self):
		city = self._city_keys[self._city_idx]
		self.mapgrid.fetch_map(config.CITIES[city][:2], _RADIUS)

	def handle_action(self, action, value=0):
		if action in ("dial_up", "dial_down"):
			self._city_idx = (self._city_idx + (-1 if action == "dial_up" else 1)) % len(self._city_keys)
			self._fetch_current()
			self.parent.pypboy.header.title = self._city_keys[self._city_idx]
		else:
			super(Module, self).handle_action(action, value)

	def handle_resume(self):
		self.parent.pypboy.header.headline = "STATS"
		self.parent.pypboy.header.title = self._city_keys[self._city_idx]
		super(Module, self).handle_resume()
