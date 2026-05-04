from pypboy import BaseModule
from pypboy.modules.stats import status
from pypboy.modules.stats import clock
from pypboy.modules.stats import currency
from pypboy.modules.stats import weather
from pypboy.modules.data import world_map


class Module(BaseModule):

	label = "STATS"
	GPIO_LED_ID = 30 #GPIO 22 #19

	def __init__(self, *args, **kwargs):
		self.submodules = [
			status.Module(self),
			clock.Module(self),
			currency.Module(self),
			weather.Module(self),
			world_map.Module(self)
		]
		super(Module, self).__init__(*args, **kwargs)
