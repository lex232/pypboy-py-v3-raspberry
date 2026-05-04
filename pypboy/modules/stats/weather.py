import os
import datetime
import threading
import time
import requests
import pypboy
import pygame
import game
import config

_ASSETS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "images", "weather"))

# ── Cache & fetcher ────────────────────────────────────────────────────────────

_CACHE_TTL = 600  # seconds

_cache = {"current": None, "forecast": None, "ts": 0, "loading": False}

_DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def _wmo(code):
	if code == 0:                        return "CLEAR",    "sun"
	if code in (1, 2):                   return "PT CLOUD", "partly_cloudy"
	if code == 3:                        return "CLOUDY",   "cloud"
	if code in (45, 48):                 return "FOG",      "fog"
	if code in (51, 53, 55, 56, 57):     return "DRIZZLE",  "rain"
	if code in (61, 63, 65, 66, 67):     return "RAIN",     "rain"
	if code in (71, 73, 75, 77):         return "SNOW",     "snow"
	if code in (80, 81, 82):             return "RAINY",    "rain"
	if code in (85, 86):                 return "SNOW",     "snow"
	if code in (95, 96, 99):             return "STORM",    "rain"
	return "N/A", "sun"


def _compass(deg):
	return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((deg + 22.5) / 45) % 8]


def _fetch():
	if _cache["loading"]:
		return
	_cache["loading"] = True
	try:
		lat, lon = config.CITIES[config.WEATHER_CITY][:2]
		r = requests.get(
			"https://api.open-meteo.com/v1/forecast",
			params={
				"latitude":      lat,
				"longitude":     lon,
				"current":       ("temperature_2m,apparent_temperature,windspeed_10m,"
				                  "winddirection_10m,weathercode,"
				                  "pressure_msl,relativehumidity_2m"),
				"daily":         "weathercode,temperature_2m_max,temperature_2m_min",
				"timezone":        "Europe/Moscow",
				"wind_speed_unit": "ms",
				"forecast_days":   5,
			},
			timeout=10,
		)
		r.raise_for_status()
		data = r.json()

		cur = data["current"]
		cond, icon = _wmo(cur["weathercode"])
		_cache["current"] = {
			"temp":       round(cur["temperature_2m"]),
			"feels_like": round(cur["apparent_temperature"]),
			"condition":  cond,
			"icon":       icon,
			"wind":       "%.1f M/S  %s" % (cur["windspeed_10m"], _compass(cur["winddirection_10m"])),
			"pressure":   "%d MMHG" % round(cur["pressure_msl"] * 0.75006),
			"humidity":   "%d%%"   % round(cur["relativehumidity_2m"]),
			}

		daily = data["daily"]
		forecast = []
		for i in range(min(5, len(daily["time"]))):
			dt = datetime.date.fromisoformat(daily["time"][i])
			cond_d, icon_d = _wmo(daily["weathercode"][i])
			forecast.append({
				"day":  _DAYS[dt.weekday()],
				"icon": icon_d,
				"cond": cond_d,
				"hi":   round(daily["temperature_2m_max"][i]),
				"lo":   round(daily["temperature_2m_min"][i]),
			})
		_cache["forecast"] = forecast
		_cache["ts"] = time.time()
	except Exception:
		pass
	finally:
		_cache["loading"] = False


def _ensure_fresh():
	if time.time() - _cache["ts"] > _CACHE_TTL:
		threading.Thread(target=_fetch, daemon=True).start()


# ── Colors ─────────────────────────────────────────────────────────────────────

_G = (105, 251, 187)
_B = (95,  255, 177)
_D = (40,  120,  80)


# ── Icons ──────────────────────────────────────────────────────────────────────

_ICON_FILES = {
	"sun":           "sun.png",
	"partly_cloudy": "partly_cloud.png",
	"cloud":         "cloud.png",
	"rain":          "rainy.png",
	"snow":          "snow.png",
	"fog":           "fog.png",
}

_icon_cache = {}


def _get_icon(name, big):
	key = (name, big)
	if key in _icon_cache:
		return _icon_cache[key]
	filename = _ICON_FILES.get(name)
	if not filename:
		_icon_cache[key] = None
		return None
	path = os.path.join(_ASSETS, filename)
	try:
		size = (64, 64) if big else (40, 40)
		raw = pygame.image.load(path).convert()
		_icon_cache[key] = pygame.transform.smoothscale(raw, size)
	except Exception:
		_icon_cache[key] = None
	return _icon_cache[key]


def _icon(s, cx, cy, name, big):
	surf = _get_icon(name, big)
	if surf is not None:
		s.blit(surf, surf.get_rect(center=(cx, cy)))


# ── Rendering ──────────────────────────────────────────────────────────────────

def _draw_loading(s):
	msg = "FETCHING DATA..." if _cache["loading"] else "NO CONNECTION"
	surf = config.FONTS[16].render(msg, True, _D, (0, 0, 0))
	s.blit(surf, ((config.WIDTH - 8 - surf.get_width()) // 2, 95))


def _draw_weather(s, c, forecast):
	_icon(s, 52, 60, c["icon"], big=True)

	s.blit(config.FONTS[27].render("%+d C" % c["temp"],                   True, _G, (0, 0, 0)), (100,  4))
	s.blit(config.FONTS[15].render(c["condition"],                         True, _B, (0, 0, 0)), (102, 40))
	s.blit(config.FONTS[11].render("FEELS LIKE  %+d C" % c["feels_like"], True, _D, (0, 0, 0)), (102, 62))

	def metric(x, y, label, value):
		lbl = config.FONTS[11].render(label + "  ", True, _D, (0, 0, 0))
		s.blit(lbl, (x, y))
		s.blit(config.FONTS[11].render(value, True, _G, (0, 0, 0)), (x + lbl.get_width(), y))

	metric(100, 80, "WIND",     c["wind"])
	metric(100, 97, "HUMIDITY", c["humidity"])
	metric(285, 80, "PRESSURE", c["pressure"])

	s.blit(config.FONTS[10].render("5-DAY OUTLOOK", True, _D, (0, 0, 0)), (6, 115))
	pygame.draw.line(s, _B, (6, 128), (config.WIDTH - 20, 128), 1)

	if not forecast:
		return
	card_w = (config.WIDTH - 8) // 5
	for i, day in enumerate(forecast[:5]):
		cx   = i * card_w + card_w // 2
		base = 132

		ds = config.FONTS[12].render(day["day"], True, _B, (0, 0, 0))
		s.blit(ds, (cx - ds.get_width() // 2, base))

		_icon(s, cx, base + 36, day["icon"], big=False)

		cs = config.FONTS[10].render(day["cond"], True, _D, (0, 0, 0))
		s.blit(cs, (cx - cs.get_width() // 2, base + 57))

		ts = config.FONTS[14].render("%+d/%+d" % (day["hi"], day["lo"]), True, _G, (0, 0, 0))
		s.blit(ts, (cx - ts.get_width() // 2, base + 70))

		if i > 0:
			pygame.draw.line(s, _D, (i * card_w, 130), (i * card_w, 228), 1)


# ── Module ─────────────────────────────────────────────────────────────────────

class Module(pypboy.SubModule):

	label = "Weather"

	def __init__(self, *args, **kwargs):
		super(Module, self).__init__(*args, **kwargs)
		_ensure_fresh()
		self.screen = WeatherScreen()
		self.add(self.screen)

	def handle_action(self, action, value=0):
		if action in ("dial_up", "dial_down"):
			cities = list(config.CITIES.keys())
			idx = cities.index(config.WEATHER_CITY)
			idx = (idx + (-1 if action == "dial_up" else 1)) % len(cities)
			config.WEATHER_CITY = cities[idx]
			_cache["ts"] = 0
			self.parent.pypboy.header.title = config.WEATHER_CITY
			_ensure_fresh()
		else:
			super(Module, self).handle_action(action, value)

	def handle_resume(self):
		self.parent.pypboy.header.headline = "WEATHER"
		self.parent.pypboy.header.title = config.WEATHER_CITY
		_ensure_fresh()
		super(Module, self).handle_resume()


class WeatherScreen(game.Entity):

	def __init__(self):
		super(WeatherScreen, self).__init__((config.WIDTH - 8, 230))
		self.rect[0] = 4
		self.rect[1] = 42
		self._data_ts = 0
		self._draw()

	def render(self, interval=0, *args, **kwargs):
		if _cache["ts"] > self._data_ts:
			self._data_ts = _cache["ts"]
			self._draw()
			self.dirty = 2

	def _draw(self):
		s = self.image
		s.fill((0, 0, 0))
		if _cache["current"] is None:
			_draw_loading(s)
		else:
			_draw_weather(s, _cache["current"], _cache["forecast"])
