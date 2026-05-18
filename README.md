# Stream Notify

Сервис следит за **Twitch** и **TikTok LIVE** и при старте стрима публикует пост в Telegram-канал **с вашего личного аккаунта** (не через бота).

## Структура

```
tgk-send-steam/
├── bot/
│   ├── main.py           # Мониторинг + отправка
│   ├── auth.py           # Первый вход в Telegram (один раз)
│   ├── config.py
│   ├── notifier.py
│   └── monitors/
│       ├── twitch.py
│       └── tiktok.py
├── data/                 # Сессия Telegram (создаётся после auth)
├── logs/
├── .env.example
└── docker-compose.yml
```

## Подготовка

### 1. Telegram API

1. Зайдите на [my.telegram.org/apps](https://my.telegram.org/apps) и создайте приложение.
2. Скопируйте `api_id` и `api_hash` в `.env`.

Ваш аккаунт должен иметь право **публиковать** в канале (`TELEGRAM_CHANNEL_ID`) — обычно вы админ канала.

### 2. Файл `.env`

```bash
copy .env.example .env
```

| Переменная | Описание |
|---|---|
| `TELEGRAM_API_ID` | Числовой ID с my.telegram.org |
| `TELEGRAM_API_HASH` | Hash приложения |
| `TELEGRAM_CHANNEL_ID` | `@channel` или `-100…` |
| `TELEGRAM_PHONE` | `+7…` — только для первого входа |
| `TWITCH_USERNAME` | Логин Twitch (нижний регистр) |
| `TIKTOK_USERNAME` | Логин TikTok без `@` |
| `CHECK_INTERVAL` | Интервал опроса, сек (по умолчанию 30) |

### 3. Первый вход в Telegram

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python bot/auth.py
```

Введите код из Telegram. После успеха файл `data/notify_session.session` сохраняется — `TELEGRAM_PHONE` из `.env` можно убрать.

## Запуск

### Локально

```bash
python bot/main.py
```

### Docker

```bash
# Первый вход (интерактивно)
docker compose run --rm -it bot python auth.py

# Рабочий режим
docker compose up -d --build
docker compose logs -f
```

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
