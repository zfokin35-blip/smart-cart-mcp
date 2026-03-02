# Smart Cart MCP (Python, microservices)

Headless REST-платформа для интеллектуального формирования продуктовой корзины через естественный язык.

## 1) Название и назначение сервиса
Система состоит из 3 Python-микросервисов:
- **Agent API** — принимает текст пользователя, оркестрирует вызовы MCP/LLM, формирует действие над корзиной.
- **Cart API** — управляет корзинами, позициями и расчетом итоговой суммы.
- **Telegram Bot** — клиентский адаптер, пересылающий пользовательские сообщения в Agent API.

## 2) Архитектура и зависимости
### Технологии
- Python 3.11, FastAPI, SQLAlchemy, Alembic-ready структура, Redis клиент, httpx.
- PostgreSQL (основное хранение), Redis (кэш), Docker / Docker Compose.
- Lint/Style: flake8 + black.
- Unit tests: pytest.
- Git hooks: `.githooks/pre-commit` + `.pre-commit-config.yaml`.

### Межсервисное взаимодействие
1. Telegram Bot -> `POST /api/v1/agent/intent` (Agent API)
2. Agent API -> MCP Retail (поиск товаров, есть mock-режим и режим реального провайдера)
3. Agent API -> DeepSeek API (Tool Calling / ReAct)
4. Agent API -> Cart API (`/api/v1/carts`, `/api/v1/carts/{id}/items`)
5. Cart API -> PostgreSQL/Redis

### Внешние сервисы
- DeepSeek API (LLM)
- PostgreSQL
- Redis

## 3) Способы запуска сервиса
### Вариант A: Docker Compose (рекомендуется)
```bash
docker compose up --build
```

Ожидаемые порты:
- Agent API: `http://localhost:8000`
- Cart API: `http://localhost:8001`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

### Вариант B: Локально без Docker
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$(pwd)/services/cart_api
uvicorn app.main:app --host 0.0.0.0 --port 8001
```
(для Agent API аналогично, с `PYTHONPATH=$(pwd)/services/agent_api`)

### Переменные окружения (.env)
1. Скопируйте шаблон: `cp .env.example .env`
2. Заполните секреты (`AGENT_DEEPSEEK_API_KEY`, `BOT_TOKEN`) и при необходимости измените URL'ы.

Поддерживаемые переменные:
- `AGENT_DEEPSEEK_API_KEY` — ключ DeepSeek.
- `AGENT_DEEPSEEK_BASE_URL` — базовый URL DeepSeek (`https://api.deepseek.com`).
- `AGENT_DEEPSEEK_MODEL` — модель (например, `deepseek-chat`).
- `AGENT_CART_API_URL` — URL Cart API.
- `AGENT_MCP_MOCK_ENABLED` — режим мок-каталога MCP (`true/false`).
- `AGENT_MCP_SEARCH_URL` — URL MCP интеграции: либо HTTP proxy/search endpoint, либо прямой MCP endpoint (`https://mcp001.vkusvill.ru/mcp`).
- `AGENT_MCP_API_KEY` — API ключ MCP провайдера (если требуется).
- `AGENT_MCP_TIMEOUT_SECONDS` — таймаут запроса в MCP в секундах.
- `CART_DATABASE_URL` — строка подключения PostgreSQL.
- `CART_REDIS_URL` — URL Redis.
- `BOT_TOKEN` — Telegram bot token.
- `BOT_AGENT_API_URL` — endpoint Agent API для бота.


### Подключение реального MCP (ВкусВилл)
1. Отключите mock: `AGENT_MCP_MOCK_ENABLED=false`.
2. Укажите `AGENT_MCP_SEARCH_URL`:
   - для прямого MCP ВкусВилл: `https://mcp001.vkusvill.ru/mcp` (используется тул `vkusvill_products_search` через MCP SDK),
   - либо proxy/search endpoint, если у вас есть HTTP-прокси поверх MCP.
3. Если endpoint требует токен — задайте `AGENT_MCP_API_KEY`.
4. Проверьте доступность endpoint перед запуском Agent API.

> Клиент MCP в Agent API нормализует ответ до `id,title,price` и поддерживает ответы вида `{"items": [...]}`, `{"products": [...]}` или просто `[...]`.

## 4) API документация
- Agent API Swagger: `http://localhost:8000/docs`
- Cart API Swagger: `http://localhost:8001/docs`

Основные эндпоинты:
- `POST /api/v1/agent/intent` — обработка пользовательского интента.
- `POST /api/v1/carts` — создание корзины.
- `POST /api/v1/carts/{cart_id}/items` — добавление товара.

## 5) Как тестировать
```bash
pytest -q
```

Проверки качества кода:
```bash
black --check .
python -m flake8
```

> На текущий момент в репозитории есть unit-тесты для ключевого happy-path в Agent API и для пересчета суммы в Cart API. Интеграционные/e2e тесты и проверки Telegram-потока пока не добавлены.

## 6) Контакты и поддержка
- **Рыхлинский К.А.** — Agent API, Telegram Bot, LLM/MCP интеграция.
- **Фокин Е.А.** — Cart API, PostgreSQL/Redis, транзакционная логика.
- Поддержка: GitHub Issues в этом репозитории.

---

## Подробный поэтапный план выполнения (кто и что делает)

### Этап 0. Инициация GitHub-репозитория и процесс разработки
**Ответственный: Рыхлинский К.А.**
1. Создать публичный репозиторий `smart-cart-mcp`.
2. Настроить ветвление:
   - `main` — стабильная ветка.
   - `develop` — интеграционная.
   - feature-ветки: `feature/agent-api`, `feature/cart-api`, `feature/bot`.
3. Добавить branch protection для `main`:
   - mandatory PR review (>=1);
   - required checks (`pytest`, `flake8`, `black --check`).
4. Подключить pre-commit:
   - `pre-commit install`;
   - запуск black/flake8/pytest до каждого коммита.
5. Добавить ISSUE_TEMPLATE и PR_TEMPLATE (по желанию курса).

### Этап 1. Лаба №2 — инфраструктура и API контракты
#### Рыхлинский К.А.
- Поднимает каркас `services/agent_api` и endpoint `POST /api/v1/agent/intent`.
- Описывает контракт запроса/ответа в Pydantic-схемах.
- Делает каркас Telegram-бота (`services/telegram_bot/bot.py`) для проброса текста в Agent API.
- Включает линтеры/formatter/hooks в репозиторий.

#### Фокин Е.А.
- Поднимает `services/cart_api`.
- Проектирует сущности БД: `Users`, `Sessions`, `Carts`, `CartItems`.
- Настраивает SQLAlchemy-модели и базовую миграционную структуру (Alembic-ready).
- Реализует базовые REST CRUD операции корзины.

### Этап 2. Лаба №3 — бизнес-логика и интеграция LLM/MCP
#### Рыхлинский К.А.
1. Интеграция DeepSeek:
   - получает API key в кабинете провайдера;
   - сохраняет ключ в `.env` (не коммитить);
   - подключает OpenAI-compatible endpoint `/chat/completions`.
2. Реализует ReAct/Tool Calling:
   - извлекает структурированное действие `add_to_cart`;
   - валидирует аргументы (id, qty, price).
3. Подключает MCP клиент ВкусВилл:
   - поиск товаров по запросу;
   - нормализация: оставить только `id,title,price` для экономии токенов.
4. Передает результат в Cart API.

#### Фокин Е.А.
1. Реализует транзакции:
   - добавление товара;
   - пересчет суммы (`qty * unit_price`) с округлением.
2. Сессии/контекст:
   - хранение связки user-session-cart;
   - хранение истории диалога для контекста LLM (в `sessions.context`).
3. Добавляет Redis caching:
   - кэш часто запрашиваемых корзин;
   - TTL, invalidation при изменении корзины.
4. Настраивает внутренний HTTP client для вызовов между сервисами.

### Этап 3. Лаба №4 — тесты и контейнеризация
#### Рыхлинский К.А.
- Пишет unit-тесты Agent API c моками (без реальных запросов в DeepSeek/MCP).
- Проверяет Swagger документацию и примеры ответов.
- Заполняет README разделы: «Архитектура», «API», «Контакты».

#### Фокин Е.А.
- Пишет unit-тесты Cart API (математика корзины, edge-cases).
- Пишет Dockerfile на каждый сервис + общий docker-compose.
- Заполняет README разделы: запуск, env, тестирование.

### Этап 4. Настройка DeepSeek API (детально)
1. Зарегистрироваться в кабинете DeepSeek.
2. Создать API key с ограничением по проекту.
3. Локально создать `.env`:
```env
AGENT_DEEPSEEK_API_KEY=...
AGENT_DEEPSEEK_BASE_URL=https://api.deepseek.com
AGENT_DEEPSEEK_MODEL=deepseek-chat
```
4. Проверить доступность вручную curl-запросом к `/chat/completions`.
5. В коде использовать таймауты + retry-policy (рекомендуется добавить в следующей итерации).
6. Логировать только метаданные (без утечки ключей и PII).

### Этап 5. Настройка Docker и GitHub Actions (рекомендуемый CI)
1. Добавить workflow `.github/workflows/ci.yml`:
   - install deps;
   - black --check;
   - flake8;
   - pytest.
2. Добавить workflow сборки docker-образов (опционально).
3. В README дать команду smoke-test после `docker compose up`:
```bash
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8001/health
```

### Этап 6. Подготовка к защите
- Демонстрация сценария: Telegram -> Agent -> MCP/DeepSeek -> Cart.
- Показ Swagger двух сервисов.
- Показ unit-тестов и pre-commit.
- Показ docker-compose «одной командой».
