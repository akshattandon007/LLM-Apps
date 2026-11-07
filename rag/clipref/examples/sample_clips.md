# Sample Clippings

A collection of imaginary bookmarks and highlights for testing ClipRef.

---

## Article: The Rise of Serverless in 2026

Serverless computing has evolved beyond simple function-as-a-service. The new
wave includes persistent state, longer runtimes, and better development
experience. AWS Lambda now supports up to 30-minute execution durations, and
custom runtimes are first-class citizens.

Key takeaways:
- Cold starts are mostly solved with tiered instance pooling
- Serverless Postgres (Neon, PlanetScale) pairs naturally with Lambda
- Cost can be lower than VMs for bursty workloads up to 1000 req/s
- Observability is still catching up — OpenTelemetry-based tracing is essential

---

## Book Highlight: Atomic Habits — James Clear

The four laws of habit change:
1. Make it obvious — design your environment
2. Make it attractive — pair habits with things you enjoy
3. Make it easy — reduce friction to two minutes
4. Make it satisfying — immediate reward > delayed reward

Habit stacking: "After I [current habit], I will [new habit]."

---

## Tutorial: Docker Compose for Local Development

```yaml
version: '3.8'
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

Best practice: never use `:latest` in production. Pin to specific versions.

---

## Clipping: Microservices Communication Patterns

Three main patterns for service-to-service communication:

1. **Synchronous (REST/gRPC):** Simple, but creates temporal coupling.
   Good for queries. Bad for commands that change state across services.

2. **Async messaging (RabbitMQ/Redis pub-sub):** Loose coupling, eventual
   consistency. Good for commands and events. Add an outbox pattern to
   guarantee delivery.

3. **Event sourcing + CQRS:** Full audit trail, separate read/write models.
   Overkill for most apps. Only needed when you need to rebuild state from
   events (financial systems, compliance).

Rule of thumb: start with synchronous calls, extract to async messaging when
you hit pain.

---

## Clipping: Python Project Structure

Recommended structure for a Python CLI project:

```
my-project/
├── pyproject.toml
├── requirements.txt
├── README.md
├── my_project/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   └── core.py
└── tests/
    ├── test_cli.py
    └── test_core.py
```

Use `python -m my_project` as the entry point. argparse for CLI parsing.
Keep business logic out of CLI handlers — they should just parse args and
call functions.

---

## Clipping: API Design — Best Practices

- Use nouns for resources, verbs is a smell: `POST /orders` not `POST /createOrder`
- Version your API from day one: `/v1/orders` not `/orders`
- Pagination: cursor-based > offset-based for production
- Error responses should have a machine-readable code AND human-readable message
- Rate limiting: 429 with Retry-After header
- Idempotency keys for mutation endpoints (at least POST/PATCH)
- Return meaningful HTTP codes: 201 for creation, 204 for deletion, 422 for validation