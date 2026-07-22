# Peace of Mind — Net Worth Tracker

Personal finance tracker: accounts, expenses, income, budgets, and rental
properties — now with two additions:

1. **Chat assistant** (Ask the Assistant tab) — ask questions like "how's my
   net worth trending?" or "what's my biggest expense category?" and get
   answers grounded in your actual data.
2. **Automated property valuation** (Properties tab) — a "🔄 Refresh
   valuation" button pulls a current value estimate and rent estimate from
   RentCast for that property's address, on demand.

## Run locally
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# fill in your API keys
streamlit run app.py
```

## API keys you'll need
| Key | Purpose | Cost |
|---|---|---|
| `ANTHROPIC_API_KEY` *(or `GROQ_API_KEY`)* | Powers the chat assistant | Anthropic: fractions of a cent/question. Groq: free tier, no card. |
| `RENTCAST_API_KEY` | Powers the "Refresh valuation" button | Free Developer tier: 50 calls/month, no card required |

Set `PROVIDER = "groq"` in secrets if you'd rather not attach a card anywhere.

## Deploy for free — Streamlit Community Cloud
1. Push this folder to a GitHub repo:
   ```bash
   git init && git add . && git commit -m "Peace of Mind v2"
   git remote add origin https://github.com/<you>/peace-of-mind.git
   git push -u origin main
   ```
2. https://share.streamlit.io → New app → pick the repo, `main`, `app.py`.
3. In **Settings → Secrets**, paste your filled-in `secrets.toml.example`.
4. Deploy.

## How the valuation refresh works
Click "🔄 Refresh valuation" on any property card. It calls RentCast's
`/avm/value` and `/avm/rent/long-term` endpoints for that property's address,
stores the results in a `rentcast_estimate` and `suggested_rent` column, and
updates `last_updated`. Your net worth calculation averages whichever
estimates you have (Zillow/Redfin/Homes.com manual entries + RentCast) —
missing ones are just skipped, not treated as zero.

If a refresh fails, it's almost always an address-formatting issue — RentCast
wants `Street, City, State, Zip` exactly.

## Persistence caveat (important)
Streamlit Community Cloud's filesystem resets on redeploys and after long
inactivity — so the CSV files under `data/` can get wiped. This matches how
the original app worked, so nothing's changed, but it's worth knowing before
you rely on it day to day. If you want this solved properly, the next step
is swapping the CSV layer in `data_store.py` for a free-tier hosted Postgres
(Supabase or Neon) — that module already isolates all the storage logic, so
it's a contained change whenever you're ready for it. Just ask.
