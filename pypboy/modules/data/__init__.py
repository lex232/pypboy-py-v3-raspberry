from pypboy import BaseModule
from pypboy.modules.data import local_map
from pypboy.modules.data import quests
from pypboy.modules.data import misc
from pypboy.modules.data import radio
from pypboy.modules.stats import general


class Module(BaseModule):

	label = "DATA"
	GPIO_LED_ID = 28 #GPIO 23 #23

	def __init__(self, *args, **kwargs):
		self.submodules = [
			local_map.Module(self),
			general.Module(self),
			quests.Module(self),
			misc.Module(self),
			radio.Module(self)
		]
		super(Module, self).__init__(*args, **kwargs)
