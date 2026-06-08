# yFinance Market Data API

A lightweight **FastAPI** service providing free market data powered by **yfinance**
(no API key required) and the **ta** library for technical indicators.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check + endpoint directory |
| GET | `/health` | Simple health check |
| GET | `/quote/{symbol}` | Latest price quote |
| GET | `/candles/{symbol}?days=60` | Daily OHLCV candles |
| GET | `/indicators/{symbol}?tail=15` | RSI, MACD, Bollinger, ADX, ATR, SMA-50 — all in one call |
| GET | `/news/{symbol}?limit=30` | Recent news headlines |

Example: `GET /indicators/AAPL?tail=15`

---

## Run Locally

> **Python version:** Python 3.12 is recommended (matches the production runtime).
> Python 3.13 also works. Python 3.14+ is not yet supported — several dependencies
> lack prebuilt wheels for it and will fail to install.

### Step 1 — Clone and set up the environment

```bash
git clone https://github.com/<you>/yfinance-api.git
cd yfinance-api

# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows (Command Prompt)
venv/Scripts/activate           # Windows (Git Bash / WSL)

# Install dependencies
pip install -r requirements.txt
```

### Step 2 — (Optional) Configure environment variables

```bash
cp .env.example .env
# Open .env and set API_KEY if you want endpoint protection.
# Leave API_KEY blank for open access during development.
```

### Step 3 — Start the server

```bash
# Development mode — auto-reloads on code changes
uvicorn app.main:app --reload --port 8000

# Production mode (no reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Step 4 — Test the endpoints

**Interactive docs (recommended for first-time exploration):**

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser — FastAPI serves a full Swagger UI where you can call every endpoint interactively.

**curl — quick smoke tests:**

```bash
# Health check
curl http://localhost:8000/health

# Root — lists all endpoints
curl http://localhost:8000/

# Latest price quote
curl http://localhost:8000/quote/AAPL

# OHLCV candles — last 10 trading days
curl "http://localhost:8000/candles/AAPL?days=10"

# All technical indicators — last 5 data points each
curl "http://localhost:8000/indicators/AAPL?tail=5"

# Recent news headlines — up to 5 articles
curl "http://localhost:8000/news/AAPL?limit=5"
```

**With API key protection enabled:**

```bash
curl "http://localhost:8000/quote/AAPL?api_key=YOUR_KEY"
```

**Edge-case checks:**

```bash
# Invalid ticker — expect HTTP 404
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/quote/INVALIDTICKER

# Out-of-range days parameter — expect HTTP 422
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/candles/AAPL?days=999"
```

### Step 5 — Stop the server

Press `Ctrl+C` in the terminal where uvicorn is running.

If you started it in the background:

```bash
# Find the PID
lsof -ti :8000          # macOS / Linux
netstat -ano | findstr :8000   # Windows — note the PID in the last column

# Kill it
kill <PID>              # macOS / Linux
taskkill /F /PID <PID>  # Windows
```

---

## Deploy to Render

Render offers a free tier with automatic GitHub deploys — no Docker knowledge required.

### Prerequisites

- A [Render account](https://render.com) (free tier available)
- This repo pushed to GitHub

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "initial commit"
gh repo create yfinance-api --public --push --source=.
# or: git remote add origin https://github.com/<you>/yfinance-api.git && git push -u origin main
```

### Step 2 — Create a Web Service on Render

**Option A — via Blueprint (recommended):**

1. Go to [render.com](https://render.com) and sign in.
2. Click **New** → **Blueprint**.
3. Connect your GitHub account and select the `yfinance-api` repository.
4. Render reads `render.yaml` and configures the service automatically.
5. Click **Apply**.

**Option B — manual setup:**

1. Click **New** → **Web Service**.
2. Connect your GitHub account and select the `yfinance-api` repository.
3. Configure:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click **Create Web Service**.

### Step 3 — Set environment variables (optional)

To enable API key protection:

1. In the Render dashboard, open your service → **Environment** tab.
2. Click **Add Environment Variable**:
   - Key: `API_KEY`, Value: `your-secret-key`
3. Render restarts the service automatically.

### Step 4 — Get your public URL

Render assigns a URL like `https://yfinance-api.onrender.com`.

Test it: `curl https://yfinance-api.onrender.com/health`

> **Note (free tier):** Render's free tier spins down the service after 15 minutes of
> inactivity. The first request after idle takes ~30 seconds to cold-start. Upgrade to
> a paid plan to keep the service always on.

### Step 5 — Monitor and redeploy

- **Logs:** Render dashboard → service → **Logs** tab shows live stdout.
- **Redeploy:** push a new commit to GitHub — Render redeploys automatically.
- **Rollback:** Render dashboard → **Events** tab → select a past deploy → **Rollback to this deploy**.

---

## Deploy to GCP Cloud Run

Cloud Run runs the Docker container serverlessly — it scales to zero when idle
(no cost) and scales out automatically under load.

### Prerequisites

- A [Google Cloud account](https://cloud.google.com) with billing enabled
- [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and initialised
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### Step 1 — Create and configure a GCP project

```bash
# Create a new project (skip if you already have one)
gcloud projects create yfinance-api --name="yFinance API"

# Set it as the active project
gcloud config set project yfinance-api

# Link billing account (required for Cloud Run)
# List your billing accounts:
gcloud billing accounts list
# Attach billing:
gcloud billing projects link yfinance-api \
  --billing-account=<BILLING_ACCOUNT_ID>
```

### Step 2 — Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### Step 3 — Create an Artifact Registry repository

```bash
gcloud artifacts repositories create yfinance-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="yFinance API Docker images"
```

### Step 4 — Build and push the Docker image

```bash
# Configure Docker to authenticate with GCP Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build the image (from the project root, where Dockerfile lives)
docker build -t us-central1-docker.pkg.dev/yfinance-api/yfinance-repo/yfinance-api:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/yfinance-api/yfinance-repo/yfinance-api:latest
```

> **Tip:** Replace `us-central1` with your preferred region throughout
> (e.g. `europe-west1`, `asia-southeast1`).

### Step 5 — Deploy to Cloud Run

```bash
gcloud run deploy yfinance-api \
  --image=us-central1-docker.pkg.dev/yfinance-api/yfinance-repo/yfinance-api:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8000 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10
```

Cloud Run will print the service URL when deployment completes:

```
Service URL: https://yfinance-api-<hash>-uc.a.run.app
```

Test it:

```bash
curl https://yfinance-api-<hash>-uc.a.run.app/health
```

### Step 6 — Set environment variables (optional)

To enable API key protection, pass it as a Cloud Run secret or plain env var:

```bash
# Plain env var (visible in console — fine for non-sensitive values)
gcloud run services update yfinance-api \
  --region=us-central1 \
  --set-env-vars API_KEY=your-secret-key

# Recommended: use Secret Manager for sensitive values
echo -n "your-secret-key" | gcloud secrets create api-key --data-file=-
gcloud run services update yfinance-api \
  --region=us-central1 \
  --set-secrets API_KEY=api-key:latest
```

### Step 7 — Redeploy after code changes

```bash
# Rebuild and push a new image
docker build -t us-central1-docker.pkg.dev/yfinance-api/yfinance-repo/yfinance-api:latest .
docker push us-central1-docker.pkg.dev/yfinance-api/yfinance-repo/yfinance-api:latest

# Update the Cloud Run service to use the new image
gcloud run services update yfinance-api \
  --region=us-central1 \
  --image=us-central1-docker.pkg.dev/yfinance-api/yfinance-repo/yfinance-api:latest
```

### Step 8 — Monitor and manage

```bash
# View live logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=yfinance-api" \
  --limit=50 --format="table(timestamp,textPayload)"

# Stream logs in real time
gcloud beta run services logs tail yfinance-api --region=us-central1

# List all revisions and traffic splits
gcloud run revisions list --service=yfinance-api --region=us-central1

# Delete the service when no longer needed
gcloud run services delete yfinance-api --region=us-central1
```

### Build with Cloud Build (CI/CD alternative)

Skip local Docker entirely — let GCP build and deploy from source:

```bash
gcloud run deploy yfinance-api \
  --source=. \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8000 \
  --memory=512Mi
```

This uses Cloud Build to build the image from the `Dockerfile` automatically,
then deploys it — no local Docker required.

---

### Deploy with Docker locally (any platform)

```bash
docker build -t yfinance-api .
docker run -p 8000:8000 -e API_KEY=optional-key yfinance-api
```

---

## Optional API Key Protection

Set the `API_KEY` environment variable. When set, every request must include
`?api_key=YOUR_KEY`:

```
GET /quote/AAPL?api_key=YOUR_KEY
```

Leave it unset for open access (fine for testing).

---

## Connecting to Bodhi

Once deployed, create these HTTP tools in Bodhi pointing to your Render URL.

### Technical Analyst (3 tools)

| Tool name | URL |
|-----------|-----|
| `get_stock_quote` | `https://your-app.onrender.com/quote/{{ticker}}` |
| `get_stock_candles` | `https://your-app.onrender.com/candles/{{ticker}}?days=60` |
| `get_indicators` | `https://your-app.onrender.com/indicators/{{ticker}}?tail=15` |

This replaces the 8 Finnhub indicator tools with just 3 — the `/indicators`
endpoint returns RSI, MACD, Bollinger, ADX, ATR, and SMA-50 in a single response.

### Sentiment Analyst (1 tool)

| Tool name | URL |
|-----------|-----|
| `get_company_news` | `https://your-app.onrender.com/news/{{ticker}}?limit=30` |

The Sentiment Analyst's LLM classifies the returned headlines as
positive/negative/neutral — no sentiment library required.

---

## Project Structure

```
yfinance-api/
├── app/
│   ├── main.py              # FastAPI app + routes
│   ├── models/
│   │   └── schemas.py       # Pydantic response models
│   └── services/
│       ├── market_data.py   # yfinance quote + candles
│       ├── indicators.py    # ta library indicator computation
│       └── news.py          # yfinance news headlines
├── requirements.txt
├── Procfile                 # Render/Heroku start command
├── render.yaml              # Render Blueprint config
├── runtime.txt              # Python version
├── Dockerfile               # Container deployment option
├── .env.example             # Environment variable template
├── .gitignore
└── README.md
```

---

## Customizing

- **Add an indicator:** edit `app/services/indicators.py`, import from `ta`,
  compute it, add it to the returned dict, and add a field in `schemas.py`.
- **Change indicator periods:** edit the `window=` arguments in `indicators.py`.
- **Add a data source:** create a new file in `app/services/`, then add a route
  in `app/main.py`.
- **Change candle lookback:** adjust the `days` query parameter or its default.

---

## Notes

- yfinance pulls from Yahoo Finance public endpoints. It's free but unofficial —
  occasionally Yahoo changes its format. The news parser handles both legacy and
  current yfinance news structures.
- For production reliability under heavy load, consider adding response caching
  (e.g., `fastapi-cache2`) to avoid repeated yfinance calls for the same symbol.
- Indicator warm-up: the service fetches ~120 days of history so that SMA-50 and
  ADX-14 have enough data to produce valid recent values.
