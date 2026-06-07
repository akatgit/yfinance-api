# TradingAgents Market Data API

A lightweight **FastAPI** service providing free market data for the TradingAgents
multi-agent trading framework. Powered by **yfinance** (no API key required) and
the **ta** library for technical indicators.

Replaces restricted/paid endpoints for the **Technical Analyst** and
**Sentiment/News Analyst** agents.

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

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Verify services work before starting the server
python test_local.py

# 4. Run the server
uvicorn app.main:app --reload --port 8000

# 5. Test it
# Open http://localhost:8000/docs  (interactive Swagger UI)
# Or:  curl http://localhost:8000/quote/AAPL
```

---

## Deploy to Railway

Railway is the fastest path to a public URL — no Docker knowledge required.

### Prerequisites

- A [Railway account](https://railway.app) (free tier available)
- This repo pushed to GitHub

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "initial commit"
gh repo create tradingagents-api --public --push --source=.
# or: git remote add origin https://github.com/<you>/tradingagents-api.git && git push -u origin main
```

### Step 2 — Create a Railway project

1. Go to [railway.app](https://railway.app) and sign in.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Authorize Railway to access your GitHub account if prompted.
4. Select the `tradingagents-api` repository.
5. Railway detects `requirements.txt` and `railway.json` automatically and starts the build.

### Step 3 — Set environment variables (optional)

To enable API key protection:

1. In the Railway dashboard, open your project → **Variables** tab.
2. Click **New Variable** and add:
   - `API_KEY` = `your-secret-key`
3. Railway restarts the service automatically.

### Step 4 — Get your public URL

1. In the Railway dashboard, open the service → **Settings** tab.
2. Under **Networking**, click **Generate Domain**.
3. Railway assigns a URL like `https://tradingagents-api-production.up.railway.app`.
4. Test it: `curl https://<your-url>/health`

### Step 5 — Monitor and redeploy

- **Logs:** Railway dashboard → service → **Logs** tab shows live stdout.
- **Redeploy:** push a new commit to GitHub — Railway redeploys automatically.
- **Rollback:** Railway dashboard → **Deployments** tab → click any past deployment → **Rollback**.

### Deploy via Railway CLI (alternative)

```bash
# Install CLI
npm install -g @railway/cli          # or: brew install railway

# Login and deploy
railway login
railway init                         # link to existing project or create new
railway up                           # deploy current directory
railway open                         # open the live URL in browser
```

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
gcloud projects create tradingagents-api --name="TradingAgents API"

# Set it as the active project
gcloud config set project tradingagents-api

# Link billing account (required for Cloud Run)
# List your billing accounts:
gcloud billing accounts list
# Attach billing:
gcloud billing projects link tradingagents-api \
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
gcloud artifacts repositories create tradingagents-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="TradingAgents API Docker images"
```

### Step 4 — Build and push the Docker image

```bash
# Configure Docker to authenticate with GCP Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build the image (from the project root, where Dockerfile lives)
docker build -t us-central1-docker.pkg.dev/tradingagents-api/tradingagents-repo/tradingagents-api:latest .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/tradingagents-api/tradingagents-repo/tradingagents-api:latest
```

> **Tip:** Replace `us-central1` with your preferred region throughout
> (e.g. `europe-west1`, `asia-southeast1`).

### Step 5 — Deploy to Cloud Run

```bash
gcloud run deploy tradingagents-api \
  --image=us-central1-docker.pkg.dev/tradingagents-api/tradingagents-repo/tradingagents-api:latest \
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
Service URL: https://tradingagents-api-<hash>-uc.a.run.app
```

Test it:

```bash
curl https://tradingagents-api-<hash>-uc.a.run.app/health
```

### Step 6 — Set environment variables (optional)

To enable API key protection, pass it as a Cloud Run secret or plain env var:

```bash
# Plain env var (visible in console — fine for non-sensitive values)
gcloud run services update tradingagents-api \
  --region=us-central1 \
  --set-env-vars API_KEY=your-secret-key

# Recommended: use Secret Manager for sensitive values
echo -n "your-secret-key" | gcloud secrets create api-key --data-file=-
gcloud run services update tradingagents-api \
  --region=us-central1 \
  --set-secrets API_KEY=api-key:latest
```

### Step 7 — Redeploy after code changes

```bash
# Rebuild and push a new image
docker build -t us-central1-docker.pkg.dev/tradingagents-api/tradingagents-repo/tradingagents-api:latest .
docker push us-central1-docker.pkg.dev/tradingagents-api/tradingagents-repo/tradingagents-api:latest

# Update the Cloud Run service to use the new image
gcloud run services update tradingagents-api \
  --region=us-central1 \
  --image=us-central1-docker.pkg.dev/tradingagents-api/tradingagents-repo/tradingagents-api:latest
```

### Step 8 — Monitor and manage

```bash
# View live logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=tradingagents-api" \
  --limit=50 --format="table(timestamp,textPayload)"

# Stream logs in real time
gcloud beta run services logs tail tradingagents-api --region=us-central1

# List all revisions and traffic splits
gcloud run revisions list --service=tradingagents-api --region=us-central1

# Delete the service when no longer needed
gcloud run services delete tradingagents-api --region=us-central1
```

### Build with Cloud Build (CI/CD alternative)

Skip local Docker entirely — let GCP build and deploy from source:

```bash
gcloud run deploy tradingagents-api \
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
docker build -t tradingagents-api .
docker run -p 8000:8000 -e API_KEY=optional-key tradingagents-api
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

Once deployed, create these HTTP tools in Bodhi pointing to your Railway URL.

### Technical Analyst (3 tools)

| Tool name | URL |
|-----------|-----|
| `get_stock_quote` | `https://your-app.up.railway.app/quote/{{ticker}}` |
| `get_stock_candles` | `https://your-app.up.railway.app/candles/{{ticker}}?days=60` |
| `get_indicators` | `https://your-app.up.railway.app/indicators/{{ticker}}?tail=15` |

This replaces the 8 Finnhub indicator tools with just 3 — the `/indicators`
endpoint returns RSI, MACD, Bollinger, ADX, ATR, and SMA-50 in a single response.

### Sentiment Analyst (1 tool)

| Tool name | URL |
|-----------|-----|
| `get_company_news` | `https://your-app.up.railway.app/news/{{ticker}}?limit=30` |

The Sentiment Analyst's LLM classifies the returned headlines as
positive/negative/neutral — no sentiment library required.

---

## Project Structure

```
tradingagents-api/
├── app/
│   ├── main.py              # FastAPI app + routes
│   ├── models/
│   │   └── schemas.py       # Pydantic response models
│   └── services/
│       ├── market_data.py   # yfinance quote + candles
│       ├── indicators.py    # ta library indicator computation
│       └── news.py          # yfinance news headlines
├── requirements.txt
├── Procfile                 # Railway/Heroku start command
├── railway.json             # Railway build config
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
