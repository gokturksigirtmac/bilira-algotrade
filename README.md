# 🧠 Bilira Case - Algotrading Backend (FastAPI + WebSocket + MongoDB + Redis)

This is a Python-based algorithmic trading app uses:

- **FastAPI** for the API and WebSocket interface
- **MongoDB** to store kline (candlestick) and crossover data
- **Redis** to publish crossover buy/sell signals via Pub/Sub
- **Binance WebSocket** for real-time market data
- **Docker** for containerized deployment

---

## 🚀 Features

- ⏱ Real-time kline (candlestick) price tracking via Binance
- 🧠 SMA crossover strategy with `SMA_50` and `SMA_200`
- 💾 Stores price data in MongoDB
- 📡 Publishes buy/sell signals via Redis Pub/Sub
- 🔌 WebSocket server for pushing live signals to clients

---

## 🐳 Run with Docker Compose

### 🔧 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

### 🛠 Setup

1. Clone the repo:

```bash
git clone https://github.com/your-username/algotrading.git
cd algotrading
```

You can modify credentials, also, you can find default credentials in .env file. Also, the app uses some values such as SMA, request endpoints etc. from .env file

```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://redis:6379

MONGO_HOST=mongo
MONGO_PORT=27017
MONGO_DB=algotrading
MONGO_USER=
MONGO_PASS=
```

### 🏎️ How To Run

After provided pre-requisite run the command:

```bash
docker-compose up --build
```

### 🔗 Endpoints

```bash
ws://localhost:8000/ws/signal
ws://localhost:8000/ws/orderbook
```
