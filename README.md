# Python Hexagonal Architecture Example

Практический пример сервиса обработки платежей, построенного на принципах Clean Architecture (Hexagonal Architecture).

Сервис написан как живой код к статье о том, почему инфраструктурные детали не должны протекать в бизнес-логику, и как это решается через контракты, адаптеры и правильное разделение слоёв.

Статья: https://habr.com/ru/articles/1034758/

## Что внутри

### Стек

- **FastAPI** — REST API
- **FastStream + RabbitMQ** — асинхронная обработка сообщений (worker)
- **APScheduler** — планировщик задач (scheduler)
- **SQLAlchemy CORE (async) + PostgreSQL** — хранение данных
- **Alembic** — миграции
- **Dishka** — dependency injection container

### Структура проекта

```
src/
├── domain/          # Доменные сущности и их локальные правила (статусы, исключения, допустимые инварианты и т.д)
├── ports/           # Контракты: интерфейсы репозиториев, UoW, gateway, publisher
├── usecases/        # Бизнес-сценарии: create, get, process, dispatch
├── adapters/        # Реализации контрактов: SQLAlchemy, RabbitMQ, HTTP, payment gateway
├── handlers/        # Точки входа: REST routes, FastStream tasks, cron jobs
└── boot/
    ├── dev/         # DI-контейнер и entrypoint'ы для разработки (внешние Stub-реализации)
    └── test/        # DI-контейнер и entrypoint'ы для тестов (внешние Fake-реализации)
```

### Полный flow платежа

```
POST /api/v1/payments
        │
        ▼
  CreatePaymentUseCase
  ├── сохраняет Payment в Postgres
  └── сохраняет запись в Outbox
        │
        ▼ (каждые N секунд)
  Scheduler → DispatchPaymentEventsUseCase
  └── публикует событие payment.created → RabbitMQ
        │
        ▼
  Worker → ProcessPaymentUseCase
  ├── списывает средства через IPaymentGateway
  ├── обновляет статус Payment (SUCCEEDED / FAILED)
  └── доставляет webhook на webhook_url
```

Outbox pattern гарантирует доставку событий в RabbitMQ даже при падении сервиса между созданием платежа и публикацией.

---

## Запуск для разработки

```bash
docker compose -f docker-compose.dev.yml up --build
```

API будет доступен на `http://localhost:9090`.

Пример запроса:

```bash
curl -X POST http://localhost:9090/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-api-key" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "amount": "100.00",
    "currency": "RUB",
    "description": "Order #1",
    "metadata": {"order_id": 1},
    "webhook_url": "https://example.com/webhook"
  }'
```

---

## Тесты

### Юнит-тесты (необходимо настроить локальное окружение)

Тестируют use cases в полной изоляции — без базы данных, без брокера, без HTTP. Все зависимости заменены hand-rolled mock'ами.

```bash
make unit
```

### E2E-тесты

Поднимают полный стек в контейнерах: реальный PostgreSQL, реальный RabbitMQ, web + worker + scheduler на Fake-реализациях внешних вызовов.

Тест создаёт платёж через REST API, ждёт пока scheduler опубликует событие в RabbitMQ, worker его обработает и обновит статус в базе, затем проверяет финальное состояние через GET.

```bash
make e2e
```

---
