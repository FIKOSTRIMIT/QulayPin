# QulayPin Telegram Mini App V2

Готовый стартовый проект цифрового магазина в Telegram Mini App.

## Что уже есть

- тёмный мобильный интерфейс;
- каталог игр;
- пакеты пополнений;
- ввод Player ID / UID;
- создание заказа;
- SQLite;
- история заказов;
- Telegram-профиль;
- бот с кнопкой открытия WebApp;
- API для дальнейшего подключения оплаты и поставщика.

> Реальные платежи и автоматическая выдача товара не подключены. Их нужно подключать через ваши официальные аккаунты/API провайдера и поставщика.

---

## 1. Установи Python

Рекомендуется Python 3.11–3.13.

Проверь в терминале VS Code:

```powershell
python --version
```

## 2. Открой проект в VS Code

Распакуй ZIP → VS Code → **File → Open Folder** → выбери папку `QulayPin_MiniApp_V2`.

## 3. Создай виртуальное окружение

В терминале VS Code:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Запусти WebApp локально

```powershell
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Открой:

```text
http://127.0.0.1:8000
```

В браузере уже можно тестировать каталог и заказы.

## 5. Создай Telegram-бота

1. Открой `@BotFather`.
2. `/newbot`
3. Задай имя.
4. Получи токен.

Скопируй `.env.example` в файл `.env` и вставь токен:

```env
APP_ENV=production
BOT_TOKEN=твой_токен
BOT_USERNAME=имя_бота_без_@
MINI_APP_URL=https://твой_https_адрес
ADMIN_KEY=случайный_секрет_не_короче_16_символов
TELEGRAM_INITDATA_MAX_AGE=86400
```

Для production обязательно укажите `APP_ENV=production`, настоящий `BOT_TOKEN` только на сервере и случайный `ADMIN_KEY` длиной не менее 16 символов. Backend проверяет подпись и срок жизни Telegram WebApp `initData`; переданный браузером `telegram_id` не используется. В development без Telegram доступен отдельный пользователь `demo`.

Frontend отправляет `initData` в заголовке `X-Telegram-Init-Data`. Заказы создаются по серверным ID игры и пакета, а цена всегда берётся из SQLite.

Базовые защищённые endpoint-ы админки находятся под `/api/admin`: каталог, игры, пакеты, заказы, статусы заказов и пользователи. Все они требуют заголовок `X-Admin-Key`; скрытый URL сам по себе доступ не даёт.

## 6. Чтобы открыть Mini App внутри Telegram

Telegram WebApp должен быть доступен по **HTTPS**.

Для разработки можно использовать HTTPS-туннель (например Cloudflare Tunnel/ngrok) или разместить сайт на Render/Railway/VPS.

Когда у тебя появится HTTPS URL, вставь его в:

```env
MINI_APP_URL=https://...
```

## 7. Запусти бота

Открой второй терминал VS Code:

```powershell
.venv\Scripts\activate
python bot.py
```

Теперь `/start` в Telegram покажет кнопку **🛍 Открыть QulayPin**. Параметр `/start ref_QPXXXXXX` безопасно применяется только при первой регистрации.

## Production

Запуск web-процесса:

```text
uvicorn app:app --host 0.0.0.0 --port ${PORT}
```

Health check доступен по `GET /health`. В production `MINI_APP_URL` обязан использовать HTTPS.

---

## AUTO fulfillment

Пакеты поддерживают режимы `manual` и `auto`. AUTO запускается только backend-функцией `process_paid_order()` после подтверждённого платежа. Создание заказа во frontend никогда не устанавливает `completed`.

Для Roblox и Brawl Stars задайте URL официального/разрешённого provider endpoint и API key только в серверном `.env`:

```env
QULAYPIN_PROVIDER_ROBLOX_URL=https://provider.example/orders
QULAYPIN_PROVIDER_ROBLOX_API_KEY=server-secret
QULAYPIN_PROVIDER_BRAWLSTARS_URL=https://provider.example/orders
QULAYPIN_PROVIDER_BRAWLSTARS_API_KEY=server-secret
```

Админ-панель управляет включением провайдера и mapping продуктов, но никогда не получает API key. При ошибке provider заказ переводится в `manual_review`, а сообщение сохраняется в fulfillment-записи и admin audit log.

Backend отправляет `POST` с `merchant_order_id`, `product_id`, `quantity`, `expected_price` и разрешённым идентификатором аккаунта. Адаптер ожидает JSON с `provider_order_id` (также принимаются `order_id` или `id`) и `status`. Значение `completed` принимается только из подтверждённого ответа provider; `failed`, `error`, `rejected` и `cancelled` переводят заказ в `manual_review`. Для конкретного официального provider при необходимости адаптируйте только `_send_provider_request()` в `fulfillment.py` под его документированный контракт.
