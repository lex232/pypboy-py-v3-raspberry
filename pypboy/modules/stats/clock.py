import pypboy
import pygame
import game
import config
import datetime


_FONT_HOUR = pygame.font.Font('monofonto.ttf', 70)
_FONT_HOUR.set_bold(True)
_FONT_MIN  = pygame.font.Font('monofonto.ttf', 56)
_FONT_MIN.set_bold(True)


def _draw_outline_text(surface, font, text, pos, fg, bg=(0, 0, 0)):
    x, y = pos
    glyph = font.render(text, True, fg)
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            if ox == 0 and oy == 0:
                continue
            surface.blit(glyph, (x + ox, y + oy))
    surface.blit(font.render(text, True, bg), (x, y))


class ClockDisplay(game.Entity):

    def __init__(self):
        w = config.WIDTH - 8
        h = 220
        super(ClockDisplay, self).__init__((w, h))

        self.cities = list(config.CITIES.keys())
        self.city_index = 0
        self._cache_key = None

        raw = pygame.image.load('images/nucacola-green.png').convert()
        ratio = raw.get_width() / raw.get_height()
        nuka_h = min(h - 60, 160)
        nuka_w = int(nuka_h * ratio)
        if nuka_w > 160:
            nuka_w = 160
            nuka_h = int(nuka_w / ratio)
        self.nuka = pygame.transform.smoothscale(raw, (nuka_w, nuka_h))
        self.nuka_x = 250
        self.nuka_y = 30
        self.clock_w = self.nuka_x - 8

    def scroll(self, direction):
        self.city_index = (self.city_index + direction) % len(self.cities)
        self._cache_key = None

    def _current_time(self):
        city = self.cities[self.city_index]
        offset = config.CITIES[city][2]
        local = datetime.datetime.utcnow() + datetime.timedelta(hours=offset)
        return local, city, offset

    def render(self, interval=0, *args, **kwargs):
        local, city, offset = self._current_time()
        key = (local.hour, local.minute, local.second, self.city_index)
        if key == self._cache_key:
            return
        self._cache_key = key

        col = (95, 255, 177)
        self.image.fill((0, 0, 0))
        self.image.blit(self.nuka, (self.nuka_x, self.nuka_y))

        # City + GMT header
        sign = "+" if offset >= 0 else ""
        header = "%s  GMT%s%d" % (city, sign, offset)
        city_surf = config.FONTS[14].render(header, True, col, (0, 0, 0))
        self.image.blit(city_surf, (5, 8))

        y_top = 8 + city_surf.get_height() + 6
        pygame.draw.line(self.image, col, (5, y_top - 2), (self.clock_w, y_top - 2), 2)

        # Left column: day-of-week box + date
        day_str  = local.strftime("%a").upper()
        date_str = "%02d" % local.day

        date_surf = config.FONTS[22].render(date_str, True, col, (0, 0, 0))

        pad = 4
        box_x = 5
        box_y = y_top + 4
        day_w, day_h = config.FONTS[16].size(day_str)
        box_w = day_w + pad * 2
        box_h = day_h + pad * 2
        pygame.draw.rect(self.image, col, (box_x, box_y, box_w, box_h), 1)
        _draw_outline_text(self.image, config.FONTS[16], day_str, (box_x + pad, box_y + pad), col)

        self.image.blit(date_surf, (box_x, box_y + box_h + 6))

        # Digits area: starts after day column
        dx = box_x + box_w + 14

        # Hours (large)
        hour_surf = _FONT_HOUR.render("%02d" % local.hour, True, col, (0, 0, 0))
        self.image.blit(hour_surf, (dx, y_top + 2))

        # Dash between hours and minutes
        dash_y = y_top + 2 + hour_surf.get_height() + 3
        pygame.draw.line(self.image, col, (dx, dash_y), (dx + hour_surf.get_width(), dash_y), 1)

        # Minutes (large)
        min_surf = _FONT_MIN.render("%02d" % local.minute, True, col, (0, 0, 0))
        min_y = dash_y + 5
        self.image.blit(min_surf, (dx, min_y))

        # Dash below minutes
        pygame.draw.line(self.image, col,
                         (dx, min_y + min_surf.get_height() + 3),
                         (dx + min_surf.get_width(), min_y + min_surf.get_height() + 3), 1)

        # Seconds (small, bottom-right of minutes)
        sec_surf = config.FONTS[20].render("%02d" % local.second, True, col, (0, 0, 0))
        sec_x = dx + min_surf.get_width() + 5
        sec_y = min_y + min_surf.get_height() - sec_surf.get_height()
        self.image.blit(sec_surf, (sec_x, sec_y))


class Module(pypboy.SubModule):

    label = "CLOCK"

    def __init__(self, *args, **kwargs):
        super(Module, self).__init__(*args, **kwargs)
        self.clock = ClockDisplay()
        self.clock.rect[0] = 40
        self.clock.rect[1] = 60
        self.add(self.clock)

    def handle_action(self, action, value=0):
        if action == "dial_up":
            self.clock.scroll(-1)
        elif action == "dial_down":
            self.clock.scroll(1)
        else:
            super(Module, self).handle_action(action, value)

    def handle_resume(self):
        self.parent.pypboy.header.headline = "STATS"
        self.parent.pypboy.header.title = "WORLD CLOCK"
        super(Module, self).handle_resume()
