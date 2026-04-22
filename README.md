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
pip3 install requests jinja2 openai python-dotenv
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
SAM_API_KEY=your_sam_gov_key_here
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

## Pricing

- **Basic ($79/mo):** Daily email digest, top 10 scored RFPs
- **Premium ($199/mo):** Adds AI compliance matrix + proposal outline
