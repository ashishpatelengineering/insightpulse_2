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

const GLOSSARY = [
  ["CSV", "Comma-Separated Values", "A plain text file with one row per line and columns separated by commas."],
  ["RFM", "Recency, Frequency, Monetary value", "How recently, how often and how much a customer buys. Each is scored from 1 to 5."],
  ["ETS", "Error, Trend, Seasonal (exponential smoothing)", "A forecasting method that gives the most weight to the latest months."],
  ["STL", "Seasonal and Trend decomposition using Loess", "Separates the yearly seasonal pattern from the underlying trend."],
  ["WAPE", "Weighted Absolute Percentage Error", "Total forecast error as a share of total sales. Forecast accuracy is 100% minus WAPE."],
  ["MAPE", "Mean Absolute Percentage Error", "Average of each month's error as a share of that month's sales."],
  ["MAE", "Mean Absolute Error", "Average error per month, in sales units."],
  ["RMSE", "Root Mean Squared Error", "Like MAE, with larger errors weighted more."],
  ["Bias", "Average forecast direction", "Positive means the forecast ran high. Negative means it ran low."],
  ["Benchmark", "Same month last year", "The error of repeating last year's sales for the same month."],
  ["Hit rate", "Share of hidden purchases found", "Share of customers whose hidden purchase appears in their top 5 suggestions."],
  ["Lift", "Association strength", "How many times more often two products are bought together than by chance."],
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
          <li>Upload a CSV file, or pick a sample dataset.</li>
          <li>Check the column matches.</li>
          <li>Click Analyze.</li>
        </ol>
      </section>

      <section className="card help-card">
        <h2>Forecasting method</h2>
        <p>
          Sales are totaled by month. Exponential smoothing, with and without seasonal adjustment, is tested on recent history and the more accurate version is used. Accuracy is measured on past data: from up to 12 starting points in the history, the following months are hidden, forecast and compared with actual sales.
        </p>
      </section>

      <section className="card help-card">
        <h2>Abbreviations and terms</h2>
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
              {GLOSSARY.map(([term, full, meaning]) => (
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
    </div>
  );
}
