# InsightPulse

A web app that turns a sales CSV file into business insights. Download a sample dataset or use your own CSV file, upload it, check the column matches, and click Analyze. One uploaded file is used by all four analyses and is shown in a scrolling table.

Front end: React, Vite and Recharts. Back end: FastAPI with pandas, scipy and statsmodels.

## Analyses

| Analysis | Question answered | Columns |
|---|---|---|
| Customer Lifetime Value | Which customers matter most? | Customer, Date, Sales, Order (optional) |
| Product Recommendation | Which products should each customer be offered next? | Customer, Product |
| Market Basket Analysis | Which products are bought together? | Product, Order |
| Forecasting | What will monthly sales be over the next 1 to 36 months? | Sales, Date, Group (optional) |

The Help page has a step by step worked example for each analysis, a scoring and customer group guide for Customer Lifetime Value, and a table of every abbreviation.

## Methods

**Customer Lifetime Value.** Customers are ranked on Recency (days since last purchase), Frequency (number of orders) and Monetary value (total spend), known together as RFM. Each rank becomes a score from 1 to 5 (rank divided by the number of customers, times 5, rounded up). The Recency score (R) and the average of the Frequency and Monetary value scores (F and M average) place every customer in exactly one of five groups: Champions (R 4 or 5, F and M average 4 or more), Loyal Customers (R 3 or more, F and M average 3 or more), Promising Customers (R 3 or more, F and M average below 3), At Risk (R below 3, F and M average 3 or more) and Hibernating (R below 3, F and M average below 3), checked in that order. Headline measures are total revenue, average lifetime value to date and average order value.

**Product Recommendation.** Item based collaborative filtering. Two products are similar when the same customers buy both (cosine similarity), and a product's score for a customer is its average similarity to the products the customer bought. A most popular products fallback is used for customers with little history. Products a customer already bought are not recommended. Reliability is tested by hiding one purchase per customer and checking whether it appears in the top 5 suggestions (hit rate), compared with recommending the most popular products.

**Market Basket Analysis.** Exact pair counting on a sparse basket matrix. A basket is one order. Pairs are shown with support, confidence in both directions and lift (minimum 1.1).

**Forecasting.** Sales are totaled by month. Two models are compared: exponential smoothing (ETS, Error, Trend, Seasonal), fitted with and without a damped trend and keeping the better fit, and the same model applied after removing the yearly seasonal pattern with STL (Seasonal and Trend decomposition using Loess). The seasonal model needs at least 30 months of history and is used only when it clearly lowers the error. The likely range is a 95% interval and never goes below zero.

Accuracy comes from a rolling origin back test: from up to 12 starting points in the history, the following months are hidden, forecast and compared with actual sales. Reported measures:

- Weighted absolute percentage error (WAPE). Forecast accuracy is 100% minus WAPE.
- Mean absolute percentage error (MAPE)
- Mean absolute error (MAE)
- Root mean squared error (RMSE)
- Bias
- Benchmark error: repeating the same month of last year

## Sample data

Five generated datasets can be downloaded from the Sample Datasets page (also in `backend/data/samples`). They use different column names, date formats and layouts, and each works in all four analyses.

- `sample_office_home_retail.csv`
- `sample_grocery_supermarket.csv`
- `sample_online_electronics.csv`
- `sample_online_fashion.csv`
- `sample_wholesale_cafe_supplies.csv`

## Deploy to Render

1. Push this folder to a GitHub repository.
2. In Render choose New, then Blueprint, and select the repository. `render.yaml` and `Dockerfile` do the rest.
3. The free plan sleeps when idle. The first request after a pause can take up to a minute.

Limits: CSV files up to 25 MB and 300,000 rows.
