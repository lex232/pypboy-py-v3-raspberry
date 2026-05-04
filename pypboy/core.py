import pygame
import config
import game
import pypboy.ui

from pypboy.modules import stats

if config.GPIO_AVAILABLE:
	import RPi.GPIO as GPIO


class Pypboy(game.core.Engine):

	def __init__(self, *args, **kwargs):
		if hasattr(config, 'OUTPUT_WIDTH') and hasattr(config, 'OUTPUT_HEIGHT'):
			self.rescale = True
		super(Pypboy, self).__init__(*args, **kwargs)
		self.init_children()
		self.init_modules()
		
		self.gpio_actions = {}
		if config.GPIO_AVAILABLE:
			self.init_gpio_controls()

	def init_children(self):
		self.background = pygame.image.load('images/overlay.png')
		# border = pypboy.ui.Border()
		# self.root_children.add(border)
		self.header = pypboy.ui.Header()
		self.root_children.add(self.header)
		scanlines = pypboy.ui.Scanlines(config.WIDTH, config.HEIGHT, 3, 1, [(0, 13, 3, 50), (6, 42, 22, 100), (0, 13, 3, 50)])
		self.root_children.add(scanlines)
		scanlines2 = pypboy.ui.Scanlines(config.WIDTH, config.HEIGHT, 8, 40, [(0, 10, 1, 0), (21, 62, 42, 90), (61, 122, 82, 100), (21, 62, 42, 90)] + [(0, 10, 1, 0) for x in range(50)], True)
		self.root_children.add(scanlines2)

	def init_modules(self):
		self.modules = {
			"stats": stats.Module(self)
		}
		for module in self.modules.values():
			module.move(4, 40)
		self.switch_module("stats")

	# Lookup table for quadrature decoder:
	# index = (prev << 2) | cur, where state = (pin_a << 1) | pin_b
	# value: +1 = CW (dial_up), -1 = CCW (dial_down), 0 = no movement / invalid
	_ENCODER_TABLE = [0, 1, -1, 0, -1, 0, 0, 1, 1, 0, 0, -1, 0, -1, 1, 0]

	def init_gpio_controls(self):
		GPIO.setwarnings(False)
		self.gpio_state = {}
		for pin in config.GPIO_ACTIONS.keys():
			print("Intialising pin %s as action '%s'" % (pin, config.GPIO_ACTIONS[pin]))
			GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			self.gpio_actions[pin] = config.GPIO_ACTIONS[pin]
			self.gpio_state[pin] = GPIO.HIGH

		if hasattr(config, 'ENCODER_PINS'):
			pin_a, pin_b = config.ENCODER_PINS
			GPIO.setup(pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.setup(pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			self._encoder_state = (GPIO.input(pin_a) << 1) | GPIO.input(pin_b)
			self._encoder_delta = 0
			GPIO.add_event_detect(pin_a, GPIO.BOTH, callback=self._on_encoder)
			GPIO.add_event_detect(pin_b, GPIO.BOTH, callback=self._on_encoder)
			print("Encoder initialised on pins A=%d B=%d" % (pin_a, pin_b))

	def _on_encoder(self, channel):
		pin_a, pin_b = config.ENCODER_PINS
		cur = (GPIO.input(pin_a) << 1) | GPIO.input(pin_b)
		self._encoder_delta += self._ENCODER_TABLE[(self._encoder_state << 2) | cur]
		self._encoder_state = cur

	def check_gpio_input(self):
		if not config.GPIO_AVAILABLE:
			return
		for pin in self.gpio_actions.keys():
			current = GPIO.input(pin)
			if current == GPIO.LOW and self.gpio_state[pin] == GPIO.HIGH:
				self.handle_action(self.gpio_actions[pin])
			self.gpio_state[pin] = current

		if hasattr(config, 'ENCODER_PINS') and self._encoder_delta != 0:
			if self._encoder_delta > 0:
				self.handle_action("dial_up")
			else:
				self.handle_action("dial_down")
			self._encoder_delta = 0

	def update(self):
		if hasattr(self, 'active'):
			self.active.update()
		super(Pypboy, self).update()

	def render(self):
		interval = super(Pypboy, self).render()
		if hasattr(self, 'active'):
			self.active.render(interval)

	def switch_module(self, module):
		if module in self.modules:
			if hasattr(self, 'active'):
				self.active.handle_action("pause")
				self.remove(self.active)
			self.active = self.modules[module]
			self.active.parent = self
			self.active.handle_action("resume")
			self.add(self.active)
		else:
			print("Module '%s' not implemented." % module)

	def handle_action(self, action):
		if action.startswith('module_'):
			self.switch_module(action[7:])
		else:
			if hasattr(self, 'active'):
				self.active.handle_action(action)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN:
			if (event.key == pygame.K_ESCAPE):
				self.running = False
			else:
				if event.key in config.ACTIONS:
					self.handle_action(config.ACTIONS[event.key])
		elif event.type == pygame.QUIT:
			self.running = False
		elif event.type == config.EVENTS['SONG_END']:
			if hasattr(config, 'radio'):
				config.radio.handle_event(event)
		else:
			if hasattr(self, 'active'):
				self.active.handle_event(event)

	def run(self):
		self.running = True
		clock = pygame.time.Clock()
		while self.running:
			for event in pygame.event.get():
				self.handle_event(event)
			self.update()
			self.render()
			self.check_gpio_input()
			clock.tick(30)

		try:
			pygame.mixer.quit()
		except:
			pass

		if config.GPIO_AVAILABLE:
			GPIO.cleanup()
