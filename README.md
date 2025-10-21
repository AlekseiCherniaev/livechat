# LiveChat

A **real-time chat application** built with **FastAPI** and **WebSockets**, designed following **Hexagonal Architecture** principles.  
It provides real-time messaging, room management, and user analytics.

**Fully Deployed & Live**: The entire infrastructure is deployed on **Yandex Cloud** using Docker Compose. You can explore the live application at:  
**[https://living-chat.online](https://living-chat.online)**

**Frontend Repository**: The React-based frontend is available at:  
**[https://github.com/AlekseiCherniaev/livechat-frontend](https://github.com/AlekseiCherniaev/livechat-frontend)**

---

## Features

- **WebSocket-based real-time messaging** with room-based communication and with user presence tracking
- **Hexagonal Architecture (Ports & Adapters)** - strict separation of concerns
- **Outbox Pattern** for reliable message delivery and event processing
- **Repository Pattern** for abstracting data access
- **Dependency Injection** through interfaces and adapters
- **Domain-Driven Design (DDD)** with clear bounded contexts
- **Authentication & Security:** - session-based authentication
- **MongoDB** - primary storage for users, rooms, and active sessions
- **Cassandra** - scalable message history with time-series optimization
- **ClickHouse** - real-time analytics and aggregations
- **Memcached** - high-performance caching layer
- **Celery** with Redis broker for task processing
- **Notification delivery** and system maintenance tasks
- **Containerized environment** via Docker Compose

---

## Tech Stack

**Backend Framework:**
- FastAPI + WebSockets
- Uvicorn (ASGI server)

**Databases:**
- MongoDB (primary operational store)
- Cassandra (message history)
- ClickHouse (analytics and aggregations)

**Caching & Queueing:**
- Redis (pub/sub, Celery broker + session storage)
- Memcached (application caching)

**Background Processing:**
- Celery (analytics events, notifications and repair tasks)

**Development & Testing:**
- pytest + pytest-asyncio
- Testcontainers for integration testing
- Ruff (linting) + Mypy (type checking)
- Pre-commit hooks

---

## Development

### Setup

1. Configure `.env` (see `.env.example`):
2. Generate mongo key (needed for auth and replica set)
    ```bash
    mkdir -p docker/mongo
    openssl rand -base64 756 > docker/mongo/keyfile.pem
    chmod 400 docker/mongo/keyfile.pem
    sudo chown 999:999 docker/mongo/keyfile.pem
   ```
3. Start services:
    ```bash
    docker compose up -d --build
    ```

---

### Main Application Screens



