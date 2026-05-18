# Stream Notify

Сервис следит за **Twitch** и **TikTok LIVE** и при старте стрима публикует пост в Telegram-канал **с вашего личного аккаунта** (не через бота).

## Структура

```
stream-notify-bot/
├── bot/
│   ├── main.py              # Мониторинг + отправка
│   ├── auth.py              # Первый вход в Telegram (один раз)
│   ├── config.py
│   ├── notifier.py
│   └── monitors/
│       ├── twitch.py
│       └── tiktok.py
├── data/                    # Сессия Telegram (после auth)
├── logs/
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── docker-entrypoint.sh     # Права на data/logs в Docker
```

## Требования

- **Docker** и **Docker Compose** (v2) — для сервера
- или **Python 3.12+** — для локального запуска

---

## Подготовка

### 1. Telegram API

1. Зайдите на [my.telegram.org/apps](https://my.telegram.org/apps) и создайте приложение.
2. Скопируйте `api_id` и `api_hash` в `.env`.

Ваш аккаунт должен иметь право **публиковать** в канале (`TELEGRAM_CHANNEL_ID`) — обычно вы админ канала.

### 2. Файл `.env`

Файл `.env` **не в репозитории** — его нужно создать вручную на каждой машине.

**Windows (PowerShell):**

```powershell
copy .env.example .env
notepad .env
```

**Linux / сервер:**

```bash
cp .env.example .env
nano .env   # или vim .env
```

| Переменная | Описание |
|---|---|
| `TELEGRAM_API_ID` | Числовой ID с my.telegram.org |
| `TELEGRAM_API_HASH` | Hash приложения |
| `TELEGRAM_CHANNEL_ID` | `@channel` или `-100…` |
| `TELEGRAM_PHONE` | `+380…` / `+7…` — **только для первого входа** |
| `TWITCH_USERNAME` | Логин Twitch (нижний регистр) |
| `TIKTOK_USERNAME` | Логин TikTok без `@` |
| `CHECK_INTERVAL` | Интервал опроса, сек (по умолчанию 30) |

Без `.env` Docker выдаст: `env file .../.env not found`.

---

## Установка на сервер (Docker)

Пошагово с нуля (Debian/Ubuntu и аналоги).

### 1. Клонировать репозиторий

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable --now docker

cd /opt
sudo git clone https://github.com/v2yv/stream-notify-bot.git
cd stream-notify-bot
```

### 2. Настроить окружение

```bash
cp .env.example .env
nano .env
mkdir -p data logs
```

Заполните все обязательные поля в `.env`, включая `TELEGRAM_PHONE` для первого входа.

### 3. Первый вход в Telegram (один раз)

Интерактивно: код из SMS/Telegram, при необходимости 2FA.

```bash
docker compose run --rm -it bot python bot/auth.py
```

> **Важно:** путь `bot/auth.py`, не `auth.py` — код лежит в каталоге `bot/` внутри образа.

При успехе появится файл `data/notify_session.session`. После этого `TELEGRAM_PHONE` в `.env` можно удалить или оставить пустым.

### 4. Запустить бота

```bash
docker compose up -d --build
docker compose logs -f
```

Остановить просмотр логов: `Ctrl+C` (контейнер продолжит работать).

Полезные команды:

```bash
docker compose ps              # статус
docker compose restart         # перезапуск
docker compose down            # остановить и убрать контейнер
docker compose logs --tail 50  # последние строки лога
```

---

## Обновление на сервере

Когда в репозитории появились новые коммиты (например, исправления Docker):

```bash
cd /opt/stream-notify-bot
git pull
docker compose up -d --build
docker compose logs -f
```

Сессия в `data/` и настройки в `.env` **сохраняются** — повторный `auth.py` не нужен, если `data/notify_session.session` на месте.

Если `git pull` ругается на локальные правки (вы правили файлы на сервере):

```bash
git stash
git pull
docker compose up -d --build
```

или сбросить только изменённые файлы из репо (осторожно — потеряете правки на сервере):

```bash
git checkout -- .
git pull
docker compose up -d --build
```

### Как выложить свои правки в GitHub (с ПК разработчика)

Если вы меняли проект локально и хотите, чтобы сервер мог сделать `git pull`:

```bash
cd d:\code\stream-notify-bot   # ваш путь к проекту
git add .
git commit -m "описание изменений"
git push origin main
```

После `git push` на сервере выполните блок «Обновление на сервере» выше.

---

## Запуск без Docker

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# отредактируйте .env

python bot/auth.py
python bot/main.py
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# отредактируйте .env

mkdir -p data logs
python bot/auth.py
python bot/main.py
```

---

## Уведомления

**Twitch:** заголовок стрима + ссылка  
**TikTok:** ссылка на live

Повторная отправка только при переходе offline → live.

## Как это работает

| Платформа | Источник | Интервал |
|---|---|---|
| Twitch | Публичный GQL API twitch.tv | `CHECK_INTERVAL` |
| TikTok | `webcast/room/info` | `CHECK_INTERVAL` |

Отдельные ключи Twitch/TikTok API **не нужны**.

---

## Частые проблемы

### `env file .../.env not found`

Создайте `.env` из примера: `cp .env.example .env` и заполните значения.

### `python: can't open file '/app/auth.py'`

Используйте правильную команду:

```bash
docker compose run --rm -it bot python bot/auth.py
```

### `sqlite3.OperationalError: unable to open database file`

или `PermissionError: ... '/app/logs/bot.log'`

Каталоги `data/` и `logs/` на хосте созданы от **root**, а контейнер пишет от пользователя **uid 1000**.

**Решение:**

```bash
sudo chown -R 1000:1000 data logs
```

В новых образах entrypoint сам выставляет права при старте; после `git pull` и пересборки это обычно не требуется. Если ошибка осталась — выполните `chown` вручную.

### Контейнер перезапускается без сессии

Сначала пройдите `docker compose run --rm -it bot python bot/auth.py`, затем `docker compose up -d --build`.

### Нет прав писать в канал

Проверьте, что ваш Telegram-аккаунт — админ канала с правом публикации, и `TELEGRAM_CHANNEL_ID` указан верно (`@имя` или числовой id `-100…`).
