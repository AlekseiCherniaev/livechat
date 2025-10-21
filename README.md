# LiveChat

A **real-time chat application** built with **FastAPI** and **WebSockets**, designed following **Hexagonal Architecture** principles.  
It provides real-time messaging, room management, and user analytics.

**Fully Deployed & Live**: The entire infrastructure is deployed on **Yandex Cloud** using Docker Compose. You can explore the live application at:  
**[https://living-chat.online](https://living-chat.online)**

**Frontend Repository**: The React-based frontend is available at:  
**[https://github.com/AlekseiCherniaev/livechat-frontend](https://github.com/AlekseiCherniaev/livechat-frontend)**

---

**Key Features:**
- **Public & Private Rooms** with join request system
- **Real-time Notifications** for join requests and room activities  
- **Message Management** - edit and delete messages in real-time
- **Admin Controls** - remove users from groups with instant updates
- **Room Search** - discover chat rooms by name, topic, or description
- **Top Rooms** - explore popular chat rooms based on activity
- **User & Service Analytics** - comprehensive insights and metrics

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

<img width="1920" height="862" alt="image" src="https://github.com/user-attachments/assets/29fa3590-02dd-4732-9c7f-d47a496c3307" />

---

<img width="1920" height="862" alt="image" src="https://github.com/user-attachments/assets/4c5b4dc7-3320-4ca9-acb3-4e513c528473" />

---

<img width="1920" height="862" alt="image" src="https://github.com/user-attachments/assets/3275207f-de21-452a-9b92-4791ff8a7de3" />

---

<img width="1920" height="862" alt="image" src="https://github.com/user-attachments/assets/143b5c78-2836-4ea0-aac4-b51debf96666" />

