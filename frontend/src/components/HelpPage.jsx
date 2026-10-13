import { useEffect } from "react";
import { Link } from "react-router-dom";
import { MODES } from "../modes/config.js";

const QUESTIONS = {
  clv: {
    question: "Who are my best customers?",
    needs: "Customer, Date, Sales",
  },
  recommendation: {
    question: "Which products should I offer each customer next?",
    needs: "Customer, Product",
  },
  basket: {
    question: "Which products are bought together?",
    needs: "Product, Order",
  },
  forecast: {
    question: "What will my sales be over the coming months?",
    needs: "Sales, Date",
  },
};

const SECTIONS = [
  {
    id: "clv",
    title: "Customer Lifetime Value",
    text: [
      "Customer Lifetime Value shows how much each customer has spent with your business and which customers matter most.",
      "Each customer is scored from 1 to 5 on three measures: how recently they bought, how often they buy and how much they spend. Together these measures are known as RFM analysis. The scores place every customer in one of five groups.",
    ],
    list: [
      ["Champions", "Bought recently, buy often and spend the most."],
      ["Loyal Customers", "Buy regularly and spend well."],
      ["Promising Customers", "Bought recently, with fewer orders or lower spend so far."],
      ["At Risk", "Used to buy often or spend well, with a long gap since their last purchase."],
      ["Hibernating", "Low spend and a long gap since their last purchase."],
    ],
    terms: [
      ["RFM", "Recency, Frequency, Monetary value", "Recency is the days since the last purchase. Frequency is the number of orders. Monetary value is the total spend."],
    ],
  },
  {
    id: "recommendation",
    title: "Product Recommendation",
    text: [
      "Product Recommendation suggests up to five products to offer each customer next.",
      "Suggestions come from the purchases of similar customers. Products that customers with a similar buying history have bought rank highest, and products the customer already bought are left out.",
      "A reliability check hides one purchase for each customer and measures how often it appears in the top 5 suggestions. The result is compared with offering everyone the most popular products.",
    ],
    terms: [
      ["Match", "Similarity score", "A score from 0 to 100 for how closely a product fits what the customer already buys."],
      ["Hit rate", "Share of hidden purchases found", "The share of customers whose hidden purchase appears in their top 5 suggestions."],
    ],
  },
  {
    id: "basket",
    title: "Market Basket Analysis",
    text: [
      "Market Basket Analysis shows which products are often bought together in the same order.",
      "Use it to plan bundles, promotions and \"frequently bought together\" prompts. Each pair of products is described by three measures.",
    ],
    terms: [
      ["Support", "Share of orders", "The share of all orders that contain both products."],
      ["A then B", "Confidence", "The share of orders containing product A that also contain product B."],
      ["Lift", "Strength of the link", "How many times more often the two products are bought together than by chance. A lift above 1 shows a real link."],
    ],
  },
  {
    id: "forecast",
    title: "Forecasting",
    text: [
      "Forecasting predicts monthly sales for the coming months, with a likely range around each month.",
      "Sales are totaled by month. Two standard methods are compared on your recent history, exponential smoothing with and without a yearly seasonal adjustment, and the more accurate one is used. The seasonal method needs about 30 months of history.",
      "Accuracy is measured on past data. From up to 12 starting points in the history, the following months are hidden, forecast and compared with actual sales. Forecast accuracy is 100% minus the weighted absolute percentage error.",
    ],
    terms: [
      ["ETS", "Error, Trend, Seasonal", "Exponential smoothing, a method that gives the most weight to the latest months."],
      ["STL", "Seasonal and Trend decomposition using Loess", "Separates the yearly seasonal pattern from the underlying trend."],
      ["WAPE", "Weighted Absolute Percentage Error", "Total forecast error as a share of total sales."],
      ["MAPE", "Mean Absolute Percentage Error", "The average of each month's error as a share of that month's sales."],
      ["MAE", "Mean Absolute Error", "The average error per month, in sales units."],
      ["RMSE", "Root Mean Squared Error", "Like MAE, with larger errors weighted more."],
      ["Bias", "Average direction of the error", "Positive means the forecast ran high. Negative means it ran low."],
      ["Benchmark", "Same month last year", "The error of repeating last year's sales for the same month."],
    ],
  },
];

export default function HelpPage() {
  useEffect(() => {
    document.title = "Help | InsightPulse";
  }, []);

  return (
    <div className="mode-page help-page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Help</h1>
          <p className="page-subtitle">Four analyses for a sales file.</p>
        </div>
      </div>

      <section className="card help-card">
        <h2>Analyses</h2>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th>Analysis</th>
                <th>Question answered</th>
                <th>Columns needed</th>
              </tr>
            </thead>
            <tbody>
              {MODES.map((mode) => (
                <tr key={mode.id}>
                  <td>
                    <Link to={mode.path}>
                      <strong>{mode.title}</strong>
                    </Link>
                  </td>
                  <td>{QUESTIONS[mode.id].question}</td>
                  <td className="muted">{QUESTIONS[mode.id].needs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card help-card">
        <h2>How to use it</h2>
        <ol className="help-steps">
          <li>Choose an analysis in the menu.</li>
          <li>Upload a CSV (Comma-Separated Values) file. Sample files can be downloaded from Sample Datasets.</li>
          <li>Check the column matches.</li>
          <li>Click Analyze.</li>
        </ol>
      </section>

      {SECTIONS.map((section) => (
        <section className="card help-card" key={section.id}>
          <h2>{section.title}</h2>
          {section.text.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
          {section.list && (
            <ul>
              {section.list.map(([name, meaning]) => (
                <li key={name}>
                  <strong>{name}.</strong> {meaning}
                </li>
              ))}
            </ul>
          )}
          <h3>Abbreviations and terms</h3>
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Term</th>
                  <th>Full form</th>
                  <th>Meaning</th>
                </tr>
              </thead>
              <tbody>
                {section.terms.map(([term, full, meaning]) => (
                  <tr key={term}>
                    <td>
                      <strong>{term}</strong>
                    </td>
                    <td>{full}</td>
                    <td className="muted">{meaning}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
