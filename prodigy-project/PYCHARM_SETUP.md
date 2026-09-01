# Настройка в PyCharm

Пошаговая инструкция, чтобы открыть и просмотреть этот проект в PyCharm.
Полноценный запуск с реальным Prodigy здесь не описан как «сделай раз-два-три»
— он зависит от лицензии, которой у нас нет в этом окружении (см. ниже).

## 1. Версия Python

Prodigy исторически поддерживал примерно диапазон **Python 3.8–3.11** —
точный список зависит от конкретной версии Prodigy (1.11.x, 1.12.x и т.д.).
**Не считайте эту цифру точной** — уточните у команды, какую версию Prodigy
покрывает лицензия Kaspi, и сверьтесь с её документацией
(https://prodi.gy/docs/install). Для этого каркаса (FastAPI/peewee/jiwer часть)
подойдёт любой Python 3.10–3.11.

## 2. Создать venv в PyCharm

`File → Settings → Project → Python Interpreter → Add Interpreter →
Add Local Interpreter → Virtualenv Environment → New`. Указать базовый
интерпретатор нужной версии, окружение — внутри `prodigy-project/venv`
(добавить `venv/` в `.gitignore`, если ещё не добавлено на уровне репозитория).

## 3. Установить зависимости

```bash
pip install -r requirements.txt
```

Это установит FastAPI, uvicorn, jiwer, peewee, python-dotenv — всё с
публичного PyPI. **Prodigy в этот список НЕ входит.**

## 4. Установка самого Prodigy

Prodigy — платный, лицензируемый пакет. Он не публикуется в публичном PyPI;
устанавливается по приватной wheel-ссылке или через `pip install prodigy
-f <url-с-лицензионным-токеном>`, которую выдаёт сам Prodigy при покупке
лицензии. У команды Kaspi эта ссылка/wheel уже должны быть — они используют
Prodigy в проде. **Спросите у команды точную команду установки или файл
wheel, который они используют**, не пытайтесь угадать URL или версию — это
единственный шаг, который нельзя выполнить в текущем окружении (нет ключа
лицензии, нет доступа к приватному индексу).

## 5. Настроить `.env`

Скопировать `.env.example` в `.env` и заполнить реальными значениями
(лицензионный ключ и URL БД возьмите у команды/из существующей продовой
конфигурации Prodigy). **Никогда не коммитьте реальный `.env`.**

```bash
cp .env.example .env
```

## 6. Run Configurations в PyCharm

### (a) Запуск рецепта разметки

`Run → Edit Configurations → + → Python`:

- **Script path / Module**: выбрать "Module name", указать `prodigy`
- **Parameters**:
  ```
  audio-markup <dataset-name> <path-to-audio-folder-or-manifest> -F recipes/audio_markup.py
  ```
  (имя рецепта `audio-markup` и порядок аргументов — то, что задаёт декоратор
  `@prodigy.recipe(...)` в `recipes/audio_markup.py`; если имя рецепта в файле
  изменится, поменяйте и здесь — сверьтесь с `python -m prodigy --help` на
  установленной версии).
- **Working directory**: корень `prodigy-project/`
- **Environment variables**: подтянуть из `.env` (плагин EnvFile для PyCharm
  либо вручную).

Требует установленного `prodigy` — то есть работает только после шага 4.

### (b) Запуск дашборда

`Run → Edit Configurations → + → Python`:

- **Module name**: `uvicorn`
- **Parameters**: `dashboard.app:app --reload --port 8001`
- **Working directory**: корень `prodigy-project/`

Не требует Prodigy — только зависимости из `requirements.txt`. Перед первым
запуском один раз выполните `python db/init_db.py`, чтобы создать локальный
sqlite-файл с таблицей `MarkupSession` (иначе дашборд по проектам будет
показывать пустые данные, но не упадёт — см. комментарии в `dashboard/app.py`
про ленивое подключение к БД).

После запуска дашборд доступен на `http://localhost:8001/` (статика из
`dashboard/static/index.html`) и его JSON API — на `http://localhost:8001/api/...`.
