# RFP Scout

Micro-SaaS that monitors SAM.gov for active RFPs and matches them to consulting boutique capabilities.

## What It Does

- **Scans SAM.gov** every day for new/active opportunities
- **Scores** each RFP by "boutique fit" (set-aside, NAICS, contract size, deadline)
- **Emails** a daily digest of the top 5-10 opportunities
- **Premium tier** generates an AI compliance matrix + proposal outline via OpenRouter/Kimi K2.6

## Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Get API Keys

**SAM.gov API Key**
1. Register/Login at https://sam.gov
2. Profile → API Key
3. Copy your Public API Key

**OpenRouter API Key** (Premium tier only)
1. Sign up at https://openrouter.ai
2. Create an API key

### 3. Configure Environment

Create a `.env` file:
```bash
SAM_API_KEY=your_sam_api_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=moonshotai/kimi-k2.6
TIER=premium
RESULTS_FILE=rfps.json
OUTPUT_DIR=output
TOP_N=10
```

### 4. Run Manually

```bash
python3 sam_gov_scanner.py
python3 alert_generator.py
```

### 5. Automate with Cron

```cron
0 6 * * * cd /Users/sam/rfp-scout && /usr/bin/python3 sam_gov_scanner.py >> scanner.log 2>&1
30 6 * * * cd /Users/sam/rfp-scout && /usr/bin/python3 alert_generator.py >> alert.log 2>&1
```

## Deployment

### Render (Recommended)

1. Fork or connect this repo to [Render](https://render.com)
2. Use the included `render.yaml` for Blueprint deployment:
   - **Web Service**: Flask API at `/rfps`, `/scan`, `/digest`
   - **Cron Job**: Daily scan at 06:00 UTC
3. Set environment variables in Render Dashboard:
   - `SAM_API_KEY`
   - `OPENROUTER_API_KEY` (optional, for Premium)
   - `TIER` (`basic` or `premium`)

### Railway

1. Connect repo to [Railway](https://railway.app)
2. Add a Python service using the `Procfile`:
   ```
   web: gunicorn app:app --bind 0.0.0.0:$PORT
   ```
3. Set environment variables in Railway Dashboard
4. Add a Railway Cron job or scheduler to run `python sam_gov_scanner.py && python alert_generator.py` daily

### Docker

```bash
docker build -t rfp-scout .
docker run -e SAM_API_KEY=xxx -e PORT=5000 -p 5000:5000 rfp-scout
```

### GitHub Pages (Landing Page)

The static landing page is deployed automatically from the `/docs` folder on the `master` branch:
- **URL**: https://swmeyer1979.github.io/rfp-scout/

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /rfps` | Latest scored RFPs as JSON |
| `GET /scan` | Trigger a manual scan |
| `GET /digest` | Latest HTML email digest |

## Pricing

- **Basic ($79/mo):** Daily email digest, top 10 scored RFPs
- **Premium ($199/mo):** Adds AI compliance matrix + proposal outline
