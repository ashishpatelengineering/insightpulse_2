# InsightPulse

A web app that turns a simple CSV file into business insights. It has four modes:

| Mode | What it answers |
| --- | --- |
| Customer Lifetime Value | Which customers are worth the most? Groups customers into Low, Medium and High Value. |
| Product Recommendation | Which five products should each customer be offered next? |
| Market Basket Analysis | Which products are bought together? |
| Forecasting | What will monthly sales look like over the next 1 to 36 months? |

Front end: React, Vite and Recharts. Back end: FastAPI with pandas, scikit-learn, statsmodels and mlxtend.

## Methods used

- **Customer Lifetime Value**: K-Means (3 groups) on log scaled total spend. Returns and zero or negative rows are excluded with a note.
- **Product Recommendation**: item based collaborative filtering with cosine similarity. A popularity fallback covers customers with little history. Products a customer already bought are never recommended.
- **Market Basket Analysis**: Apriori with association rules (lift of at least 1.1). A basket is one member on one date. Support is lowered step by step if needed so small datasets still return results.
- **Forecasting**: monthly totals. Two standard models compete on a back test of the most recent months: ETS (Holt-Winters family, damped trend, chosen by AICc) and STL plus ETS for seasonality. The seasonal model is used only with 30 or more months of history and only if it clearly beats the simple one. The 95% range is based on back test errors and never goes below zero.

## Sample data

Three datasets in `backend/data/samples`, each working in all four modes and each with different column names and date formats:

- `sample_office_home_retail.csv`
- `sample_grocery_supermarket.csv`
- `sample_online_electronics.csv`

Regenerate them with `python tools/generate_samples.py`.

## Run locally

```bash
# back end
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000

# front end (second terminal)
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api to port 8000
```

To serve everything from one process: `npm run build` in `frontend`, then start uvicorn. The API serves `frontend/dist` automatically.

## Tests

```bash
cd backend && python -m pytest -q
cd frontend && npm test
```

## Deploy to Render

1. Push this folder to a GitHub repository.
2. In Render choose New, then Blueprint, and select the repository. `render.yaml` and `Dockerfile` do the rest.
3. The free plan sleeps when idle. The first request after a pause can take up to a minute, and the app shows a waiting message and retries automatically.

Limits: CSV files up to 25 MB and 300,000 rows.
