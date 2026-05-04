# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Что это

Эмулятор Pip-Boy 3000 на Python/Pygame, разработанный для Raspberry Pi с 2.8" ёмкостным сенсорным экраном и GPIO-кнопками. Отображает полноценный интерфейс в стиле Fallout с данными OpenStreetMap, анализом аудиоспектра и поддержкой физических кнопок.

## Запуск

```bash
pip install -r requirements.txt
python main.py
```

Сборка не нужна, тестов нет. На системах без Raspberry Pi импорт GPIO молча проваливается, и приложение работает только с клавиатурой.

## Архитектура

Приложение состоит из двух слоёв: универсального игрового движка (`game/`) и самого Pip-Boy (`pypboy/`).

**Слой движка** (`game/`):
- `game/core.py` — базовый класс `Engine`: инициализация Pygame, главный цикл, диспетчеризация событий, рендеринг спрайтов
- `game/entities.py` — `Entity` (обёртка над Pygame-спрайтом) и `EntityGroup` (упорядоченный контейнер спрайтов)

**Слой приложения** (`pypboy/`):
- `pypboy/core.py` — `Pypboy(Engine)`: корневой класс; содержит три главных модуля, header, footer, scanlines; маршрутизирует действия в активный модуль
- `pypboy/__init__.py` — `BaseModule` и `SubModule`: базовые классы модулей с навигацией по ручкам, управлением GPIO-светодиодами и звуковыми эффектами при переключениях
- `pypboy/ui.py` — общие виджеты: `Header`, `Footer`, `Menu`, `Scanlines`, `Border`, `Overlay`
- `pypboy/data.py` — `Maps` (загрузка и парсинг OSM), `SoundSpectrum`/`LogSpectrum` (FFT-анализ аудио)

**Модули** (`pypboy/modules/`):
- `stats/` — вкладка STATS: status, SPECIAL, skills, perks, general
- `items/` — вкладка ITEMS: weapons, apparel, aid, misc, ammo
- `data/` — вкладка DATA: local_map (рендер OSM), world_map, quests, misc, radio

**Ввод** (`config.py`):
- Клавиатура: F1/F2/F3 — переключение главных модулей; 1–5 — переключение субмодулей; стрелки — навигация по меню
- GPIO: привязка пинов в режиме BCM для физических кнопок/ручек (только Raspberry Pi)
- Оба источника ввода порождают одинаковые именованные действия (`knob_1`–`knob_5`, `dial_up`, `dial_down` и т.д.)

## Добавление субмодуля

1. Создать класс-наследник `SubModule` в нужном файле `pypboy/modules/<tab>/`
2. Задать `label` (отображается в footer), реализовать `handle_action(action)` и при необходимости `handle_resume()`
3. Добавить экземпляр в список `submodules` родительского модуля

## Ключевая конфигурация

`config.py` управляет размером экрана (480×320), центром карты по умолчанию (`MAP_FOCUS`), маппингом OSM-объектов на иконки и всеми размерами шрифтов. Шрифты загружаются из `monofonto.ttf` при старте.
