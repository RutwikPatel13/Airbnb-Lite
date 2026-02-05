# 🏠 AirbnbLite - Hotel Booking API

A full-featured hotel booking backend API built with **FastAPI** and **PostgreSQL**. This project replicates core Airbnb functionality including user authentication, hotel management, room booking, and payment processing.

## 🌐 Live Demo

- **API Base**: https://airbnblite-api.onrender.com
- **Swagger Docs**: https://airbnblite-api.onrender.com/api/v1/docs
- **ReDoc**: https://airbnblite-api.onrender.com/api/v1/redoc

## ✨ Features

### Authentication & Users
- JWT-based authentication (access + refresh tokens)
- User signup with role selection (Guest, Hotel Admin, Admin)
- Profile management

### Hotel Management (Admin)
- Create, update, delete hotels
- Activate/deactivate hotels for public visibility
- Manage hotel amenities and photos

### Room Management (Admin)
- Create rooms with different types (Standard, Deluxe, Suite, Presidential)
- Automatic 90-day inventory initialization
- Set pricing and capacity

### Inventory Management
- Date-based room availability tracking
- Bulk inventory updates
- Dynamic pricing per date

### Booking Flow
- Search available hotels by city, dates, guests
- Initialize bookings with availability validation
- Add guests to bookings
- Cancel bookings with automatic inventory release

### Payment Integration
- Mock payment gateway
- Payment session creation
- Webhook handling for payment confirmation

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Validation**: Pydantic v2
- **Deployment**: Render

## 📁 Project Structure

```
AirbnbLite/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/      # API route handlers
│   │   └── router.py       # Route aggregation
│   ├── core/
│   │   ├── config.py       # Settings & environment
│   │   ├── dependencies.py # Auth dependencies
│   │   └── security.py     # JWT & password utils
│   ├── db/
│   │   ├── base.py         # SQLAlchemy base
│   │   └── session.py      # Database session
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── main.py             # FastAPI application
├── alembic/                # Database migrations
├── render.yaml             # Render deployment config
└── requirements.txt
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/RutwikPatel13/Airbnb-Lite.git
   cd Airbnb-Lite
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Create database**
   ```bash
   createdb airbnblite
   ```

6. **Run migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

8. **Open API docs**: http://localhost:8000/api/v1/docs

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register new user |
| POST | `/api/v1/auth/login` | Login & get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |

### Users & Guests
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/profile` | Get user profile |
| PATCH | `/api/v1/users/profile` | Update profile |
| GET | `/api/v1/users/myBookings` | Get user's bookings |
| POST | `/api/v1/users/guests` | Add a guest |
| GET | `/api/v1/users/guests` | List all guests |

### Hotels (Public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/hotels/search` | Search hotels |
| GET | `/api/v1/hotels/{id}/info` | Get hotel details |

### Hotels (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/admin/hotels` | Create hotel |
| GET | `/api/v1/admin/hotels` | List my hotels |
| PATCH | `/api/v1/admin/hotels/{id}/activate` | Activate hotel |

### Bookings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/bookings/init` | Create booking |
| POST | `/api/v1/bookings/{id}/addGuests` | Add guests |
| GET | `/api/v1/bookings/{id}/status` | Check status |
| POST | `/api/v1/bookings/{id}/cancel` | Cancel booking |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/webhook/bookings/{id}/pay` | Initiate payment |
| POST | `/api/v1/webhook/payment/capture` | Payment webhook |

## 🔐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `SECRET_KEY` | JWT signing key | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | 7 |
| `CORS_ORIGINS` | Allowed origins | `["http://localhost:3000"]` |

## 🧪 Testing the API

### Create a Hotel Admin
```bash
curl -X POST https://airbnblite-api.onrender.com/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123", "name": "Hotel Admin", "role": "HOTEL_ADMIN"}'
```

### Login
```bash
curl -X POST https://airbnblite-api.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'
```

### Search Hotels
```bash
curl "https://airbnblite-api.onrender.com/api/v1/hotels/search?city=New%20York"
```

## 📊 Database Schema

```
users ──────────┬──────────── guests
                │
                ├──────────── hotels ──────── rooms ──────── inventories
                │                │
                └──────────── bookings ──────── payments
                                 │
                                 └──────── booking_guests (junction)
```

## 🚢 Deployment

This project is configured for deployment on **Render** using the `render.yaml` blueprint:

1. Fork this repository
2. Create a new Blueprint on Render
3. Connect your GitHub repo
4. Render will automatically create the database and web service

## 📝 License

MIT License - feel free to use this project for learning or as a starting point for your own projects.

---

Made with ❤️ using FastAPI
