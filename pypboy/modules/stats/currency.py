import os
import threading
import time
import requests
import xmltodict
import pypboy
import pygame
import game
import config

_ASSETS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "images", "currency"))

# ── Cache & fetcher ────────────────────────────────────────────────────────────

_CACHE_TTL = 600  # 10 minutes

_cache = {"fiat": {}, "crypto": {}, "ts": 0, "loading": False}

_FIAT_CODES = ("USD", "EUR", "CNY")
_CRYPTO_IDS = {
	"bitcoin":          "BTC",
	"ethereum":         "ETH",
	"the-open-network": "TON",
}


def _fmt(val):
	if val is None:
		return "---"
	if val >= 1000:
		return "{:,.0f}".format(round(val)).replace(",", " ")
	return "%.2f" % val


def _fetch():
	if _cache["loading"]:
		return
	_cache["loading"] = True
	try:
		r = requests.get("https://www.cbr.ru/scripts/XML_daily.asp", timeout=10)
		for v in xmltodict.parse(r.content)["ValCurs"]["Valute"]:
			if v["CharCode"] in _FIAT_CODES:
				_cache["fiat"][v["CharCode"]] = float(v["VunitRate"].replace(",", "."))
	except Exception:
		pass
	try:
		r = requests.get(
			"https://api.coingecko.com/api/v3/simple/price",
			params={"ids": ",".join(_CRYPTO_IDS), "vs_currencies": "usd"},
			timeout=10,
		)
		for cg_id, ticker in _CRYPTO_IDS.items():
			_cache["crypto"][ticker] = r.json().get(cg_id, {}).get("usd")
	except Exception:
		pass
	_cache["ts"] = time.time()
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
	"USD": "dollar-green.png",
	"EUR": "euro-green.png",
	"CNY": "yuan-green.png",
	"BTC": "bitcoin-green.png",
	"ETH": "ethereum-green.png",
	"TON": "ton-green.png",
}

_icon_cache = {}


def _get_icon(ticker):
	if ticker in _icon_cache:
		return _icon_cache[ticker]
	filename = _ICON_FILES.get(ticker)
	if not filename:
		_icon_cache[ticker] = None
		return None
	path = os.path.join(_ASSETS, filename)
	try:
		_icon_cache[ticker] = pygame.image.load(path).convert()
	except Exception:
		_icon_cache[ticker] = None
	return _icon_cache[ticker]


# ── Rendering ──────────────────────────────────────────────────────────────────

_ROWS = [
	[("USD", "RUB"), ("EUR", "RUB"), ("CNY", "RUB")],
	[("BTC", "USD"), ("ETH", "USD"), ("TON", "USD")],
]
_SOURCES = ["fiat", "crypto"]
_COLORS  = [_B, _G]


def _draw_screen(s):
	s.fill((0, 0, 0))

	s.blit(config.FONTS[11].render("EXCHANGE RATES", True, _D, (0, 0, 0)), (6, 5))
	pygame.draw.line(s, _B, (6, 18), (config.WIDTH - 20, 18), 1)

	has_data = _cache["fiat"] or _cache["crypto"]
	if not has_data:
		msg = "FETCHING RATES..." if _cache["loading"] else "NO CONNECTION"
		surf = config.FONTS[16].render(msg, True, _D, (0, 0, 0))
		s.blit(surf, ((config.WIDTH - 8 - surf.get_width()) // 2, 95))
		return

	card_w = (config.WIDTH - 8) // 3   # 157 px

	for col in (1, 2):
		pygame.draw.line(s, _D, (col * card_w, 20), (col * card_w, 228), 1)
	pygame.draw.line(s, _D, (6, 124), (config.WIDTH - 20, 124), 1)

	for row_i, pairs in enumerate(_ROWS):
		ry  = 22 if row_i == 0 else 126
		src = _cache[_SOURCES[row_i]]
		col = _COLORS[row_i]

		for col_i, (base, quote) in enumerate(pairs):
			cx = col_i * card_w + card_w // 2

			icon = _get_icon(base)
			if icon is not None:
				s.blit(icon, icon.get_rect(center=(cx, ry + 32)))

			ps = config.FONTS[11].render("%s / %s" % (base, quote), True, _D, (0, 0, 0))
			s.blit(ps, (cx - ps.get_width() // 2, ry + 55))

			vs = config.FONTS[22].render(_fmt(src.get(base)), True, col, (0, 0, 0))
			s.blit(vs, (cx - vs.get_width() // 2, ry + 70))


# ── Module ─────────────────────────────────────────────────────────────────────

class Module(pypboy.SubModule):

	label = "Currency"

	def __init__(self, *args, **kwargs):
		super(Module, self).__init__(*args, **kwargs)
		_ensure_fresh()
		self.screen = CurrencyScreen()
		self.add(self.screen)

	def handle_resume(self):
		self.parent.pypboy.header.headline = "CURRENCY"
		self.parent.pypboy.header.title = "EXCHANGE RATES"
		_ensure_fresh()
		super(Module, self).handle_resume()


class CurrencyScreen(game.Entity):

	def __init__(self):
		super(CurrencyScreen, self).__init__((config.WIDTH - 8, 230))
		self.rect[0] = 4
		self.rect[1] = 42
		self._data_ts = 0
		_draw_screen(self.image)

	def render(self, interval=0, *args, **kwargs):
		if _cache["ts"] > self._data_ts:
			self._data_ts = _cache["ts"]
			_draw_screen(self.image)
			self.dirty = 2
