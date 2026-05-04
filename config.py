import pygame

WIDTH = 480
HEIGHT = 320

# OUTPUT_WIDTH = 320
# OUTPUT_HEIGHT = 240

# City: lat, lon, gmt
CITIES = {
    "ROSTOV-ON-DON":    (47.204235,  39.733716,   3),
    "SAINT-PETERSBURG": (59.9386300, 30.3141300,  3),
    "NOVOROSSIYSK":     (44.7233000, 37.7688000,  3),
    "SOCHI":            (43.5809670, 39.7124260,  3),
    "DOMBAY":           (43.2896170, 41.6235200,  3),
    "KRASNODAR":        (45.0355000, 38.9753000,  3),
    "NORDKAPP":         (71.1690000, 25.7847000,  1),
    "CASABLANCA":       (33.5731000, -7.5898000,  1),
    "ANTALYA":          (36.8969000, 30.7133000,  3),
}

WEATHER_CITY = "ROSTOV-ON-DON"

EVENTS = {
	'SONG_END': pygame.USEREVENT + 1
}

ACTIONS = {
	pygame.K_F1: "module_stats",
	pygame.K_F2: "module_items",
	pygame.K_F3: "module_data",
	pygame.K_1:	"knob_1",
	pygame.K_2: "knob_2",
	pygame.K_3: "knob_3",
	pygame.K_4: "knob_4",
	pygame.K_5: "knob_5",
	pygame.K_UP: "dial_up",
	pygame.K_DOWN: "dial_down"
}

# Using GPIO.BCM as mode
# raspi-gpio get 4,17,27,22,23
GPIO_ACTIONS = {
#    18: "module_stats", #GPIO 4
#	14: "module_items", #GPIO 14
#	15: "module_data", #GPIO 15
	4:	"knob_1",
	18: "knob_2",
	27: "knob_3",
	22: "knob_4",
	23: "knob_5",
}

# Rotary encoder pins (BCM): A=15, B=14
# CW rotation → "dial_up", CCW → "dial_down"
ENCODER_PINS = (15, 14)


MAP_ICONS = {
	"camp": 		pygame.image.load('images/map_icons/camp.png'),
	"factory": 		pygame.image.load('images/map_icons/factory.png'),
	"metro": 		pygame.image.load('images/map_icons/metro.png'),
	"misc": 		pygame.image.load('images/map_icons/misc.png'),
	"monument": 	pygame.image.load('images/map_icons/monument.png'),
	"vault": 		pygame.image.load('images/map_icons/vault.png'),
	"settlement": 	pygame.image.load('images/map_icons/settlement.png'),
	"ruin": 		pygame.image.load('images/map_icons/ruin.png'),
	"cave": 		pygame.image.load('images/map_icons/cave.png'),
	"landmark": 	pygame.image.load('images/map_icons/landmark.png'),
	"city": 		pygame.image.load('images/map_icons/city.png'),
	"office": 		pygame.image.load('images/map_icons/office.png'),
	"sewer": 		pygame.image.load('images/map_icons/sewer.png'),
}

AMENITIES = {
	'pub': 				MAP_ICONS['vault'],
	'nightclub': 		MAP_ICONS['vault'],
	'bar': 				MAP_ICONS['vault'],
	'fast_food': 		MAP_ICONS['sewer'],
	'cafe': 			MAP_ICONS['sewer'],
	'drinking_water': 	MAP_ICONS['sewer'],
	'restaurant': 		MAP_ICONS['settlement'],
	'cinema': 			MAP_ICONS['office'],
	'pharmacy': 		MAP_ICONS['office'],
	'school': 			MAP_ICONS['office'],
	'bank': 			MAP_ICONS['monument'],
	'townhall': 		MAP_ICONS['monument'],
	'bicycle_parking': 	MAP_ICONS['misc'],
	'place_of_worship': MAP_ICONS['misc'],
	'theatre': 			MAP_ICONS['misc'],
	'bus_station': 		MAP_ICONS['misc'],
	'parking': 			MAP_ICONS['misc'],
	'fountain': 		MAP_ICONS['misc'],
	'marketplace': 		MAP_ICONS['misc'],
	'atm': 				MAP_ICONS['misc'],
}

pygame.font.init()
FONTS = {}
for x in range(10, 28):
	FONTS[x] = pygame.font.Font('monofonto.ttf', x)

_cyrillic_candidates = ['dejavusansmono', 'dejavusans', 'liberationmono', 'arial', 'couriernew']
MAP_FONT = None
for _f in _cyrillic_candidates:
	_path = pygame.font.match_font(_f)
	if _path:
		MAP_FONT = pygame.font.Font(_path, 11)
		break
if MAP_FONT is None:
	MAP_FONT = pygame.font.Font(None, 11)
