# Running Guide — Web Live Trade

Dokumen ini menjelaskan kebutuhan dan langkah running project di **server Ubuntu** dan **Windows PC MT5**.

---

## 1. Arsitektur Server

Project ini tidak bisa 100% jalan di Ubuntu tanpa bantuan Windows, karena **MetaTrader 5 hanya reliable di Windows**.

Arsitektur yang dipakai:

```text
Ubuntu Server
- Frontend Next.js       : port 3010 -> container 3000
- Backend FastAPI        : port 8010 -> container 8000
- PostgreSQL             : port 5434 -> container 5432
- pgAdmin                : port 5051 -> container 80
- AI Provider / 9router  : port 20128

Windows PC
- MetaTrader 5 terminal
- MT5 Bridge FastAPI     : port 8001

Network
- Ubuntu dan Windows harus bisa saling akses via Tailscale.
```

---

## 2. Yang Dibutuhkan di Ubuntu Server

### Software wajib

- Docker
- Docker Compose plugin
- Git
- Tailscale, jika MT5 Bridge hanya bisa diakses lewat Tailnet

Cek:

```bash
docker --version
docker compose version
git --version
tailscale version
```

### Port yang dipakai di server

| Service | Host Port | Container Port | URL |
|---|---:|---:|---|
| Frontend | 3010 | 3000 | `http://10.254.200.211:3010` |
| Backend | 8010 | 8000 | `http://10.254.200.211:8010` |
| PostgreSQL | 5434 | 5432 | internal DB / optional external |
| pgAdmin | 5051 | 80 | `http://10.254.200.211:5051` |
| AI / 9router | 20128 | 20128 | `http://10.254.200.211:20128/v1` |

Catatan: port ini dipilih karena server sudah punya app lain di port `3001`, `5050`, `5432`, `5433`, dan `8000`.

---

## 3. Yang Dibutuhkan di Windows PC

### Software wajib

- MetaTrader 5 terminal
- Python
- Package Python:

```bat
pip install fastapi uvicorn MetaTrader5
```

### MT5 wajib

- MT5 terminal harus terbuka
- Akun harus login
- Market Watch harus punya symbol:
  - `XAUUSD.m`
  - `EURUSD.m`
  - `GBPUSD.m`
  - `BTCUSD.m`

### Windows firewall

Buka PowerShell **as Administrator**:

```powershell
New-NetFirewallRule -DisplayName "MT5 Bridge 8001" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow
```

---

## 4. Start MT5 Bridge di Windows

Di Windows CMD:

```bat
cd D:\mySelf\project\web-live-trade\backend
set MT5_LOGIN=ISI_LOGIN_MT5
set MT5_PASSWORD=ISI_PASSWORD_MT5
set MT5_SERVER=JustMarkets-Demo2
python mt5_bridge.py
```

Terminal harus tetap terbuka.

Cek dari Windows:

```bat
curl http://localhost:8001/health
curl http://localhost:8001/tick/XAUUSD.m
```

Hasil health yang benar:

```json
{"status":"ok","mt5_connected":true}
```

Cek IP Tailscale Windows:

```bat
tailscale ip -4
```

Contoh IP Windows sekarang:

```text
100.65.56.80
```

---

## 5. Setup Tailscale di Ubuntu

Jika Ubuntu belum bisa akses `100.65.56.80`, install Tailscale:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```

Login lewat link yang muncul.

Cek:

```bash
tailscale ip -4
tailscale ping 100.65.56.80
curl --max-time 5 http://100.65.56.80:8001/health
```

Jika curl ke bridge sukses, lanjut deploy Docker.

---

## 6. Environment Server Ubuntu

File `.env` di folder project server `/opt/web-live-trade/.env` harus berisi minimal:

```env
# Backend reads MT5 data from Windows MT5 Bridge
MT5_BRIDGE_URL=http://100.65.56.80:8001

# AI Provider / 9router
ANTHROPIC_BASE_URL=http://10.254.200.211:20128/v1
ANTHROPIC_AUTH_TOKEN=sk_9router
ANTHROPIC_MODEL=claude

# Frontend public API URL — must be server IP + backend port
NEXT_PUBLIC_API_URL=http://10.254.200.211:8010
NEXT_PUBLIC_WS_URL=ws://10.254.200.211:8010

# CORS allowed frontend origin
ALLOWED_ORIGINS=http://10.254.200.211:3010,http://localhost:3010

# Optional Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Symbols
SYMBOLS=XAUUSD.m,EURUSD.m,GBPUSD.m,BTCUSD.m
```

Penting: `NEXT_PUBLIC_API_URL` dan `NEXT_PUBLIC_WS_URL` harus benar saat **build frontend**, bukan hanya runtime.

---

## 7. Docker Compose Frontend Build Args

Pastikan `Dockerfile` frontend punya build args:

```dockerfile
FROM node:20-alpine

WORKDIR /app

ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_WS_URL

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

Pastikan service frontend di `docker-compose.yml` punya args:

```yaml
frontend:
  build:
    context: .
    dockerfile: Dockerfile
    args:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
      NEXT_PUBLIC_WS_URL: ${NEXT_PUBLIC_WS_URL}
  container_name: tradebot_frontend
  ports:
    - "3010:3000"
  environment:
    - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
    - NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL}
  depends_on:
    - backend
  restart: unless-stopped
```

Kalau frontend masih request ke `http://localhost:8000`, berarti frontend belum rebuild dengan env yang benar.

---

## 8. Start Project di Ubuntu

Masuk folder project:

```bash
cd /opt/web-live-trade
```

Build dan start:

```bash
docker compose up -d --build
```

Jika mengubah `NEXT_PUBLIC_*`, rebuild frontend no-cache:

```bash
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend backend
```

Cek container:

```bash
docker ps
```

Container yang harus jalan:

```text
tradebot_frontend
tradebot_backend
tradebot_postgres
tradebot_pgadmin
```

---

## 9. Database Migration

Jalankan sekali setelah deploy/update schema:

```bash
docker exec -it tradebot_postgres psql -U tradebot -d tradebot
```

Paste SQL:

```sql
ALTER TABLE ai_market_summaries ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'INACTIVE';
ALTER TABLE ai_market_summaries ADD COLUMN IF NOT EXISTS exit_price FLOAT;
ALTER TABLE ai_market_summaries ADD COLUMN IF NOT EXISTS exit_reason VARCHAR(20);
ALTER TABLE ai_market_summaries ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP;
ALTER TABLE ai_market_summaries ADD COLUMN IF NOT EXISTS profit_loss FLOAT;
ALTER TABLE signals ADD COLUMN IF NOT EXISTS m30_trend VARCHAR(30);
```

Keluar:

```sql
\q
```

---

## 10. Health Check

### Backend health

```bash
curl http://localhost:8010/health
```

Harus:

```json
{
  "status": "ok",
  "mt5_connected": true,
  "ai_available": true
}
```

Jika `status: degraded` dan `mt5_connected: false`, cek MT5 Bridge Windows dan Tailscale.

### MT5 bridge dari Ubuntu

```bash
curl --max-time 5 http://100.65.56.80:8001/health
curl --max-time 5 http://100.65.56.80:8001/tick/XAUUSD.m
curl --max-time 5 "http://100.65.56.80:8001/candles/XAUUSD.m?timeframe=M5&limit=10"
```

### API data

```bash
curl http://localhost:8010/api/symbols
curl http://localhost:8010/api/price/XAUUSD.m
curl http://localhost:8010/api/analysis/XAUUSD.m
curl http://localhost:8010/api/signals/XAUUSD.m
```

### AI status dan manual analysis

```bash
curl http://localhost:8010/api/ai/status
curl -X POST http://localhost:8010/api/ai/analyze/XAUUSD.m
```

---

## 11. Akses Web

Buka browser:

```text
http://10.254.200.211:3010
```

Pastikan di DevTools Network request API mengarah ke:

```text
http://10.254.200.211:8010/api/...
```

Bukan:

```text
http://localhost:8000/api/...
```

Jika masih `localhost:8000`, rebuild frontend no-cache.

---

## 12. Logs dan Troubleshooting

### Lihat logs

```bash
docker logs tradebot_backend --tail=100
docker logs tradebot_frontend --tail=100
docker logs tradebot_postgres --tail=50
```

### Restart service tertentu

```bash
docker compose up -d --force-recreate backend
docker compose up -d --force-recreate frontend
```

### Restart semua

```bash
docker compose down
docker compose up -d --build
```

### Cek env yang dibaca docker compose

```bash
docker compose config | grep -n "NEXT_PUBLIC_API_URL\|NEXT_PUBLIC_WS_URL\|ALLOWED_ORIGINS\|MT5_BRIDGE_URL"
```

---

## 13. Masalah Umum

### Frontend CORS ke `localhost:8000`

Penyebab: frontend dibuild dengan env lama.

Fix:

```bash
docker compose build --no-cache frontend
docker compose up -d --force-recreate frontend backend
```

Pastikan `.env`:

```env
NEXT_PUBLIC_API_URL=http://10.254.200.211:8010
NEXT_PUBLIC_WS_URL=ws://10.254.200.211:8010
```

### Backend degraded: `mt5_connected: false`

Cek:

```bash
curl --max-time 5 http://100.65.56.80:8001/health
```

Jika gagal:

- MT5 Bridge belum jalan di Windows
- MT5 terminal belum login
- Windows Firewall belum allow port 8001
- Ubuntu belum join Tailscale

### Port already allocated

Cek port yang sedang dipakai:

```bash
docker ps
```

Gunakan port project ini:

```text
frontend 3010
backend 8010
postgres 5434
pgadmin 5051
```

### `/history` 404

Route `/history` belum ada page khusus. Signal history saat ini tampil di halaman Signals, bukan `/history`.

---

## 14. Quick Checklist Setelah Server Restart

1. Start MT5 di Windows dan pastikan login.
2. Start MT5 Bridge di Windows:

```bat
cd D:\mySelf\project\web-live-trade\backend
python mt5_bridge.py
```

3. Di Ubuntu:

```bash
cd /opt/web-live-trade
docker compose up -d
curl http://localhost:8010/health
```

4. Buka:

```text
http://10.254.200.211:3010
```

5. Run AI Analysis dan cek active alert tetap muncul setelah refresh.
