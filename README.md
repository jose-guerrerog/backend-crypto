# 🧠 Crypto Portfolio Tracker (Backend)

This is the Django backend API for the [Crypto Portfolio Tracker frontend](https://github.com/jose-guerrerog/frontend-crypto). It provides RESTful endpoints and WebSocket support for managing cryptocurrency portfolios, real-time price tracking via the CoinGecko API, and Redis-based caching to improve performance and reduce API load.

---

## 🚀 Features

- REST API for creating portfolios and submitting transactions
- Real-time WebSocket price updates using Django Channels
- Redis-powered caching for CoinGecko API responses
- CORS-enabled for frontend integration
- Health check endpoint for uptime monitoring

---

## 🛠️ Tech Stack

- **Framework:** Django
- **API:** Django REST Framework
- **WebSockets:** Django Channels (in-process)
- **Caching:** `django-redis`
- **Database:** PostgreSQL (hosted on [Neon](https://neon.tech))
- **External API:** CoinGecko
- **Hosting:** Render (backend) + Neon (PostgreSQL)
- **CORS:** `django-cors-headers`

---

## 📡 WebSocket Support

**Endpoint:** `/ws/crypto/`

### Supported Messages

**Subscribe to specific coins:**
```json
{
  "type": "subscribe",
  "coins": ["bitcoin", "ethereum"]
}
```

**Keep connection alive:**
```json
{
  "type": "ping",
  "timestamp": 123456789
}
```

### Behavior
- Sends price updates every 30 seconds
- Prices are fetched from CoinGecko or Redis cache
- WebSocket messages are handled using AsyncWebsocketConsumer

---

## 💰 CoinGecko Integration

Crypto prices are retrieved from the CoinGecko API with:

- Redis caching to avoid hitting the API too frequently
- Rate-limiting guard (1.3s between requests)
- CORS-safe proxy using https://api.allorigins.win
- If the API fails or rate-limits, cached prices are returned as fallback

---

## 🔁 Redis Usage

Redis is used solely for caching CoinGecko price responses, configured via django-redis.

**Example:**
- Cache key: `cached_crypto_prices`
- TTL: 60 seconds

---

## 🌍 CORS Configuration

Enabled via django-cors-headers:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://frontend-crypto-nine.vercel.app",
]
```

---

## 🧪 Health Check

Uptime monitoring endpoint:

```bash
GET /health/
→ { "status": "ok" }
```

Used by services like cron-job.org to keep the backend awake.

---

## ⚙️ Local Setup

```bash
git clone https://github.com/jose-guerrerog/backend-crypto.git
cd backend-crypto
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Make sure PostgreSQL and Redis are running.

---

## 🔐 Environment Variables

Create a `.env` file with:

```env
SECRET_KEY=your-django-secret
DEBUG=True
DATABASE_URL=postgres://<user>:<password>@<host>:<port>/<db>
REDIS_URL=redis://localhost:6379
```
