/**
 * Shared wording. The Help page and the tooltips on the result screens read from here,
 * so one description is never written twice.
 */

export const SEGMENTS = [
  { name: "Champions", text: "Bought recently, buy often and spend the most." },
  { name: "Loyal Customers", text: "Buy regularly and spend well." },
  { name: "Promising Customers", text: "Bought recently, with fewer orders or lower spend so far." },
  { name: "At Risk", text: "Used to buy often or spend well, with a long gap since their last purchase." },
  { name: "Hibernating", text: "Low spend and a long gap since their last purchase." },
];

export const SEGMENT_TEXT = Object.fromEntries(SEGMENTS.map((s) => [s.name, s.text]));

/** Terms: short name, full form, meaning. The meaning is also the tooltip. */
export const TERMS = {
  rfm: {
    term: "RFM",
    full: "Recency, Frequency, Monetary value",
    meaning: "Recency is the days since the last purchase. Frequency is the number of orders. Monetary value is the total spend.",
  },
  score: {
    term: "Score",
    full: "RFM score",
    meaning: "Recency, Frequency and Monetary value, each from 1 (lowest) to 5 (highest). For example, 5-4-3 means Recency 5, Frequency 4 and Monetary value 3.",
  },
  avgLifetimeValue: {
    term: "Average lifetime value",
    full: "Average lifetime value",
    meaning: "The average amount a customer has spent so far.",
  },
  avgOrderValue: {
    term: "Average order value",
    full: "Average order value",
    meaning: "The average value of one order.",
  },
  match: {
    term: "Match",
    full: "Similarity score",
    meaning: "A score from 0 to 100 for how closely a product fits what the customer already buys.",
  },
  popular: {
    term: "Popular",
    full: "Most purchased",
    meaning: "A product many customers buy, shown when the customer has little history.",
  },
  hitRate: {
    term: "Hit rate",
    full: "Share of hidden purchases found",
    meaning: "The share of customers whose hidden purchase appears in their top 5 suggestions.",
  },
  support: {
    term: "Support",
    full: "Share of orders",
    meaning: "The share of all orders that contain both products.",
  },
  confidence: {
    term: "A then B",
    full: "Confidence",
    meaning: "The share of orders containing product A that also contain product B.",
  },
  lift: {
    term: "Lift",
    full: "Strength of the link",
    meaning: "How many times more often the two products are bought together than by chance. A lift above 1 shows a real link.",
  },
  holtWinters: {
    term: "Holt-Winters",
    full: "Exponential smoothing with trend and yearly pattern",
    meaning: "A forecasting method that gives the most weight to the latest months, follows their direction and repeats the yearly pattern.",
  },
  wape: {
    term: "Forecast error",
    full: "Weighted absolute percentage error (WAPE)",
    meaning: "Total forecast error as a share of total sales, measured on past months. Lower is better.",
  },
  bias: {
    term: "Bias",
    full: "Average direction of the error",
    meaning: "Positive means the forecast ran high. Negative means it ran low. Close to zero is best.",
  },
  benchmark: {
    term: "Comparison with last year",
    full: "Error of repeating the same month of last year",
    meaning: "The forecast error if each month were simply predicted to equal the same month of last year. The forecast error should be lower than this.",
  },
  forecastAccuracy: {
    term: "Forecast accuracy",
    full: "Forecast accuracy",
    meaning: "100% minus the forecast error, measured on past months. A higher value is better.",
  },
  likelyRange: {
    term: "Likely range",
    full: "Likely range",
    meaning: "Low and high estimates around each forecast month. Real sales are expected to fall inside the range about 8 times out of 10. The width is based on the errors seen when the method was tested on past months.",
  },
};

/** Blocks on the result screens. */
export const BLOCK_TEXT = {
  segments: "Based on how recently, how often and how much customers buy.",
  revenueShare: "Share of customers compared with share of revenue.",
  matchColumn: "A score from 0 to 100 for how closely a product fits what the customer already buys. Popular marks a product many customers buy, shown when the customer has little history.",
  confidenceBToA: "The share of orders containing product B that also contain product A.",
  reliability: "A purchase is hidden for each customer and checked against the top 5 suggestions, then compared with the most popular products.",
};

/** The forecasting method, in one place. Used by the Help page and the tooltip on the forecast chart. */
export const FORECAST_METHOD =
  "The forecast uses the Holt-Winters method. It gives the most weight to recent months and follows their direction without assuming sales will keep rising or falling forever. With 24 months of history or more, it also repeats the yearly pattern, such as a busy December.";

export const TERM_GROUPS = {
  clv: ["rfm"],
  recommendation: ["match", "hitRate"],
  basket: ["support", "confidence", "lift"],
  forecast: ["holtWinters", "forecastAccuracy", "wape", "bias", "benchmark", "likelyRange"],
};

/** Customer Lifetime Value: how scores are explained and how groups are assigned. */
export const SCORE_ROWS = [
  ["Recency (R)", "Days since the customer's last purchase", "Bought most recently", "Bought longest ago"],
  ["Frequency (F)", "Number of orders", "Most orders", "Fewest orders"],
  ["Monetary value (M)", "Total spend", "Highest spend", "Lowest spend"],
];

/** Each row is a band of the F and M average. Each column is an R score from 1 to 5. */
export const GROUP_GRID = {
  bands: ["4 to 5", "3 to 3.5", "1 to 2.5"],
  rows: [
    ["At Risk", "At Risk", "Loyal Customers", "Champions", "Champions"],
    ["At Risk", "At Risk", "Loyal Customers", "Loyal Customers", "Loyal Customers"],
    ["Hibernating", "Hibernating", "Promising Customers", "Promising Customers", "Promising Customers"],
  ],
};

export const SEGMENT_COLORS = {
  Champions: "#1e3a5f",
  "Loyal Customers": "#6384ab",
  "Promising Customers": "#4a8f8a",
  "At Risk": "#b7791f",
  Hibernating: "#98a3b0",
};
