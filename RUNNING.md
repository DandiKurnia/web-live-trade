# Cara Running Ulang Setelah Laptop Mati / Restart

## Urutan Start (Harus Berurutan)

### 1. Buka MetaTrader 5

- Buka aplikasi MetaTrader 5
- Pastikan sudah login ke akun JustMarkets-Demo2
- Pastikan di Market Watch terlihat harga bergerak (XAUUSD.m, EURUSD.m, dll)
- **MT5 harus running sebelum backend dijalankan**

### 2. Start Database (Docker)

Buka terminal, masuk ke folder project:

```bash
cd D:\mySelf\project\web-live-trade
docker compose -f docker-compose.db.yml up -d
```

Tunggu sampai muncul "Healthy". Cek:

```bash
docker compose -f docker-compose.db.yml ps
```

Pastikan `tradebot_postgres` statusnya `healthy`.

### 3. Start Backend (Python)

Buka terminal baru:

```bash
cd D:\mySelf\project\web-live-trade\backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tunggu sampai muncul:
```
INFO:     Application startup complete.
```

Cek health:
```bash
curl http://localhost:8000/health
```

Harus muncul: `{"status":"ok","mt5_connected":true,"ai_available":true}`

### 4. Start Frontend (Next.js)

Buka terminal baru:

```bash
cd D:\mySelf\project\web-live-trade
npm run dev
```

Buka browser: http://localhost:3000

---

## Urutan Stop (Kalau Mau Matikan)

```bash
# 1. Stop frontend: Ctrl+C di terminal frontend
# 2. Stop backend: Ctrl+C di terminal backend
# 3. Stop database:
docker compose -f docker-compose.db.yml down
# 4. Tutup MetaTrader 5
```

**Catatan:** Jangan pakai `down -v` kecuali mau reset database. Flag `-v` menghapus semua data.

---

## Troubleshooting Setelah Restart

### Backend error: "MT5 initialize failed"
- MT5 belum dibuka atau belum login
- Solusi: Buka MT5, login, tunggu harga muncul, lalu restart backend

### Backend error: "connection refused" ke database
- Docker belum start atau postgres belum healthy
- Solusi: `docker compose -f docker-compose.db.yml up -d` dan tunggu

### Backend error: "column does not exist"
- Database schema berubah (ada update code)
- Solusi: Reset database:
  ```bash
  docker compose -f docker-compose.db.yml down -v
  docker compose -f docker-compose.db.yml up -d
  ```
  Lalu restart backend

### Frontend error: "fetch failed"
- Backend belum running
- Solusi: Start backend dulu, baru buka frontend

### WebSocket terus disconnect
- Backend belum ready atau MT5 belum connect
- Solusi: Pastikan `curl http://localhost:8000/health` return `mt5_connected: true`

---

## Quick Start (Copy-Paste)

Buka 3 terminal:

**Terminal 1 — Database:**
```bash
cd D:\mySelf\project\web-live-trade
docker compose -f docker-compose.db.yml up -d
```

**Terminal 2 — Backend:**
```bash
cd D:\mySelf\project\web-live-trade\backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 — Frontend:**
```bash
cd D:\mySelf\project\web-live-trade
npm run dev
```

---

## Port yang Digunakan

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5433 | localhost:5433 |
| pgAdmin | 5050 | http://localhost:5050 |
| Backend API | 8000 | http://localhost:8000 |
| Frontend | 3000 | http://localhost:3000 |

---

## Cek Semua Berjalan

```bash
# Database
docker compose -f docker-compose.db.yml ps

# Backend
curl http://localhost:8000/health

# Frontend
# Buka http://localhost:3000 di browser
```
