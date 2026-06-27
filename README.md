# Payments Service

An async payments processing microservice built with Python, demonstrating production-grade distributed systems patterns: transactional outbox, distributed lease locking, idempotent APIs, and webhook delivery with exponential backoff.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Pydantic v2 |
| Database | PostgreSQL, SQLAlchemy (async), asyncpg |
| Messaging | RabbitMQ, FastStream |
| Migrations | Alembic |
| HTTP client | httpx (async) |

## Architecture

```
┌─────────────┐     POST /payments          ┌──────────────────────────────────────────┐
│   Client    │  ─────────────────────────► │              FastAPI App                 │
│             │  Idempotency-Key: <key>      │                                          │
│             │ ◄─────────────────────────  │  PaymentService.create_payment()         │
│             │     202 Accepted             │   ├─ INSERT payments  ─┐ one transaction │
└─────────────┘                             │   └─ INSERT outbox    ─┘                 │
                                            └──────────────────────────────────────────┘
                                                           │
                                            ┌──────────────▼──────────────┐
                                            │       OutboxPublisher        │
                                            │  (polls every 1s)           │
                                            │                             │
                                            │  SELECT FOR UPDATE          │
                                            │    SKIP LOCKED              │
                                            └──────────────┬──────────────┘
                                                           │ publish
                                            ┌──────────────▼──────────────┐
                                            │         RabbitMQ            │
                                            │   payments.new              │
                                            │   payments.retry            │
                                            │   payments.dlq              │
                                            └──────────────┬──────────────┘
                                                           │ consume
                                            ┌──────────────▼──────────────┐
                                            │      Payment Consumer        │
                                            │                             │
                                            │  1. claim_for_processing()  │
                                            │     UPDATE WHERE            │
                                            │       status=PENDING        │
                                            │  2. FakePaymentGateway      │
                                            │  3. mark_succeeded/failed() │
                                            │  4. send webhook ───────────┼──► Client webhook_url
                                            └─────────────────────────────┘
                                                    │ on failure
                                            ┌───────▼───────┐   max retries  ┌─────────┐
                                            │ payments.retry │ ─────────────► │   DLQ   │
                                            │ (exp backoff)  │                └─────────┘
                                            └───────────────┘
```

## Key Design Decisions

### 1. Transactional Outbox Pattern

The service never publishes directly to RabbitMQ from the API handler. Instead, a payment creation atomically writes both the `payments` and `outbox` rows in a single database transaction:

```python
await self.payment_repo.create(payment)
await self.outbox_repo.create(outbox_event)
await self.session.commit()  # atomic: both or neither
```

A separate `OutboxPublisher` process polls the outbox table and publishes to RabbitMQ. This eliminates the dual-write problem — if RabbitMQ is down or the process crashes mid-flight, the event is never lost; it stays in the outbox and gets retried.

### 2. Distributed Lease Locking with SKIP LOCKED

Multiple `OutboxPublisher` instances can run concurrently without conflicts or duplicate publishing. The outbox poller uses PostgreSQL's `SELECT FOR UPDATE SKIP LOCKED`:

```python
select(Outbox)
    .where(...)
    .with_for_update(skip_locked=True)
```

Each instance locks its own batch of rows. Other instances skip already-locked rows and take the next available ones. No application-level mutex, no Redis, no coordination overhead.

### 3. Stale Lease Recovery

Events that get stuck in `PROCESSING` (e.g., the publisher crashed mid-batch) are automatically re-claimed after a 2-minute lease timeout:

```python
LEASE_TIMEOUT = timedelta(minutes=2)

or_(
    Outbox.status == OutboxStatus.PENDING,
    (Outbox.status == OutboxStatus.PROCESSING)
    & (Outbox.processing_started_at < datetime.now(timezone.utc) - LEASE_TIMEOUT),
)
```

No manual intervention, no stuck events, no ops toil.

### 4. Atomic Payment Claiming (Exactly-Once Processing)

RabbitMQ delivers messages at least once, so the same payment event may arrive at multiple consumers. The consumer uses an atomic `UPDATE ... WHERE status = PENDING RETURNING` to claim a payment:

```python
update(Payment)
    .where(Payment.id == payment_id, Payment.status == PaymentStatus.PENDING)
    .values(status=PaymentStatus.PROCESSING)
    .returning(Payment)
```

If two consumers race, exactly one gets the row back. The other gets `None` and exits immediately. No distributed lock needed — the database is the authority.

### 5. Idempotent Payment Creation

Clients send an `Idempotency-Key` header. The key is stored with a `UNIQUE` constraint and index. Duplicate requests hit an `IntegrityError`, trigger a rollback, and return the original payment — safe to retry without creating duplicates:

```python
except IntegrityError:
    await self.session.rollback()
    existing = await self.payment_repo.get_by_idempotency_key(idempotency_key)
    if existing is None:
        raise  # different constraint violated — re-raise
    return existing
```

### 6. Webhook Delivery with Exponential Backoff and DLQ

Failed webhook deliveries follow a three-tier retry strategy:

```
payments.new ──(fail)──► payments.retry ──(max retries)──► payments.dlq
                         delay = 2 ** retry_count
                         (1s → 2s → 4s)
```

The retry consumer tracks `retry_count` on each message. After `MAX_RETRIES = 3` attempts the message moves to the dead-letter queue for manual inspection or alerting. The backoff is implemented without a scheduler — the consumer sleeps inline before retrying, keeping the architecture simple.

## Payment State Machine

```
PENDING ──► PROCESSING ──► SUCCEEDED
                       └──► FAILED
```

State transitions are enforced at the database level via conditional updates. No invalid transitions are possible regardless of race conditions.

## Project Structure

```
app/
├── api/v1/          # FastAPI route handlers
├── core/            # Config, database, migrations, security
├── messaging/       # RabbitMQ consumers (payments, retry, DLQ) + broker + schemas
├── models/          # SQLAlchemy ORM models
├── repositories/    # Data access layer (PaymentRepository, OutboxRepository)
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic (PaymentService, WebhookService, FakePaymentGateway)
└── workers/         # Entrypoints for background processes (consumer, outbox publisher)
```

Two separate processes run alongside the API:
- **`workers/consumer.py`** — FastStream app subscribing to RabbitMQ queues
- **`workers/outbox_publisher.py`** — polling loop that drains the outbox table

## API

Authentication is via `X-Api-Key` header on all endpoints.

### Create Payment

```http
POST /api/v1/payments
X-Api-Key: <key>
Idempotency-Key: <uuid>
Content-Type: application/json

{
  "amount": "99.99",
  "currency": "USD",
  "description": "Order #1234",
  "webhook_url": "https://example.com/webhook",
  "extra_data": {}
}
```

Returns `202 Accepted` — processing is async.

### Get Payment

```http
GET /api/v1/payments/{payment_id}
X-Api-Key: <key>
```

## Running Locally

**Prerequisites:** Python 3.12+, PostgreSQL, RabbitMQ.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in credentials
```

```bash
# API server (runs migrations on startup)
uvicorn app.main:app --reload

# RabbitMQ consumer
faststream run app.workers.consumer:app

# Outbox publisher
python -m app.workers.outbox_publisher
```

## Environment Variables

| Variable | Description |
|---|---|
| `POSTGRES_HOST` | PostgreSQL host |
| `POSTGRES_PORT` | PostgreSQL port |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `RABBITMQ_HOST` | RabbitMQ host |
| `RABBITMQ_PORT` | RabbitMQ port |
| `RABBITMQ_USER` | RabbitMQ user |
| `RABBITMQ_PASSWORD` | RabbitMQ password |
| `API_KEY` | Static API key for authentication |
