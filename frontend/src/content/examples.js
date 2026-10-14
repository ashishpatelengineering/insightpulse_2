/**
 * Worked examples for the Help page. Each example is a list of steps: a title, optional text,
 * an optional table and optional closing text. **Text between double asterisks** is shown in bold.
 * The Customer Lifetime Value figures are calculated here from the example data.
 */

// ---------------------------------------------------------------------------
// Customer Lifetime Value
// ---------------------------------------------------------------------------
export const CLV_CUSTOMERS = [
  { name: "Emily", days: 1, orders: 24, spend: 4800 },
  { name: "James", days: 8, orders: 18, spend: 4500 },
  { name: "Jessica", days: 20, orders: 2, spend: 150 },
  { name: "Michael", days: 35, orders: 8, spend: 2400 },
  { name: "Jennifer", days: 60, orders: 9, spend: 1700 },
  { name: "Robert", days: 90, orders: 7, spend: 1300 },
  { name: "Daniel", days: 150, orders: 3, spend: 380 },
  { name: "David", days: 200, orders: 22, spend: 4100 },
  { name: "Ashley", days: 260, orders: 4, spend: 500 },
  { name: "Brian", days: 320, orders: 1, spend: 90 },
];

const money = (n) => `$${n.toLocaleString("en-US")}`;

/** Rank 1 is the weakest customer. Score is the rank turned into 1 to 5, rounded up. */
export function clvScores(customers = CLV_CUSTOMERS) {
  const n = customers.length;
  const rankBy = (value, higherIsBetter) => {
    const order = [...customers].sort((a, b) => (higherIsBetter ? value(a) - value(b) : value(b) - value(a)));
    return new Map(order.map((c, i) => [c.name, i + 1]));
  };
  const recency = rankBy((c) => c.days, false);
  const frequency = rankBy((c) => c.orders, true);
  const monetary = rankBy((c) => c.spend, true);
  const score = (rank) => Math.ceil((rank * 5) / n);
  return customers.map((c) => {
    const r = score(recency.get(c.name));
    const f = score(frequency.get(c.name));
    const m = score(monetary.get(c.name));
    const fm = (f + m) / 2;
    let segment = "Hibernating";
    let rule = 5;
    if (r >= 4 && fm >= 4) {
      segment = "Champions";
      rule = 1;
    } else if (r >= 3 && fm >= 3) {
      segment = "Loyal Customers";
      rule = 2;
    } else if (r >= 3) {
      segment = "Promising Customers";
      rule = 3;
    } else if (fm >= 3) {
      segment = "At Risk";
      rule = 4;
    }
    return { ...c, rankR: recency.get(c.name), rankF: frequency.get(c.name), rankM: monetary.get(c.name), r, f, m, fm, segment, rule };
  });
}

function rankTable(rows, rankKey, valueKey, scoreKey, formatValue, n) {
  return rows
    .slice()
    .sort((a, b) => a[rankKey] - b[rankKey])
    .map((c) => [c.name, formatValue(c[valueKey]), String(c[rankKey]), `${c[rankKey]} ÷ ${n} × 5 = ${((c[rankKey] * 5) / n).toFixed(1)}`, `**${c[scoreKey]}**`]);
}

function buildClvExample() {
  const rows = clvScores();
  const n = rows.length;
  const totalRevenue = rows.reduce((s, c) => s + c.spend, 0);
  const totalOrders = rows.reduce((s, c) => s + c.orders, 0);
  const groups = ["Champions", "Loyal Customers", "At Risk", "Hibernating", "Promising Customers"];
  const groupRows = groups.map((g) => {
    const members = rows.filter((c) => c.segment === g);
    const revenue = members.reduce((s, c) => s + c.spend, 0);
    return { g, members, revenue, share: (100 * revenue) / totalRevenue };
  });
  const champions = groupRows.find((x) => x.g === "Champions");
  const atRisk = groupRows.find((x) => x.g === "At Risk");
  const atRiskCustomer = atRisk.members[0];

  return {
    lead: `An online coffee bean shop has ${n} customers. The file has one row per purchase. Adding up each customer's rows gives this table. Days are counted from the customer's last purchase to the end of the file.`,
    leadTable: {
      head: ["Customer", "Days since last purchase", "Orders", "Total spend"],
      align: ["left", "right", "right", "right"],
      rows: CLV_CUSTOMERS.map((c) => [c.name, String(c.days), String(c.orders), money(c.spend)]),
    },
    steps: [
      {
        title: "Rank the customers on three measures",
        text: [
          "The three measures are Recency (R), the days since the last purchase, Frequency (F), the number of orders, and Monetary value (M), the total spend. Together they are known as RFM.",
          `For each measure, customers are ranked from weakest to strongest. Rank 1 is the weakest customer and rank ${n} is the strongest. The rank becomes a score from 1 to 5:`,
          `**Score = rank ÷ ${n} customers × 5, rounded up to a whole number**`,
        ],
      },
      {
        title: "Recency rank and score",
        text: ["A longer gap since the last purchase gives a lower rank."],
        table: {
          head: ["Customer", "Days since last purchase", "Rank", "Calculation", "R score"],
          align: ["left", "right", "right", "left", "right"],
          rows: rankTable(rows, "rankR", "days", "r", (v) => String(v), n),
        },
      },
      {
        title: "Frequency rank and score",
        text: ["Fewer orders give a lower rank."],
        table: {
          head: ["Customer", "Orders", "Rank", "Calculation", "F score"],
          align: ["left", "right", "right", "left", "right"],
          rows: rankTable(rows, "rankF", "orders", "f", (v) => String(v), n),
        },
      },
      {
        title: "Monetary value rank and score",
        text: ["Lower total spend gives a lower rank."],
        table: {
          head: ["Customer", "Total spend", "Rank", "Calculation", "M score"],
          align: ["left", "right", "right", "left", "right"],
          rows: rankTable(rows, "rankM", "spend", "m", (v) => money(v), n),
        },
      },
      {
        title: "Combine Frequency and Monetary value",
        text: ["The F score and the M score are averaged into one number, the F and M average."],
        table: {
          head: ["Customer", "R score", "F score", "M score", "F and M average"],
          align: ["left", "right", "right", "right", "left"],
          rows: rows.map((c) => [c.name, String(c.r), String(c.f), String(c.m), `(${c.f} + ${c.m}) ÷ 2 = **${c.fm.toFixed(1)}**`]),
        },
      },
      {
        title: "Place each customer in a group",
        text: ["Each combination of R score and F and M average belongs to one group. Find the customer's R score across the top and the F and M average down the side."],
        grid: true,
        table2: {
          head: ["Customer", "R score", "F and M average", "Group"],
          align: ["left", "right", "right", "left"],
          rows: rows.map((c) => [c.name, String(c.r), c.fm.toFixed(1), `**${c.segment}**`]),
        },
      },
      {
        title: "Headline numbers",
        table: {
          head: ["Measure", "Calculation", "Result"],
          align: ["left", "left", "right"],
          rows: [
            ["Total revenue", rows.map((c) => c.spend.toLocaleString("en-US")).join(" + "), `**${money(totalRevenue)}**`],
            ["Average lifetime value", `${money(totalRevenue)} ÷ ${n} customers`, `**${money(totalRevenue / n)}**`],
            ["Average order value", `${money(totalRevenue)} ÷ ${totalOrders} orders`, `**${money(Math.round(totalRevenue / totalOrders))}**`],
          ],
        },
        after: ["Average lifetime value is the average amount a customer has spent so far. Average order value is the average value of one order."],
      },
      {
        title: "Revenue by group",
        table: {
          head: ["Group", "Customers", "Revenue", "Calculation", "Share of revenue"],
          align: ["left", "right", "right", "left", "right"],
          rows: groupRows.map((x) => [x.g, String(x.members.length), money(x.revenue), `${x.revenue.toLocaleString("en-US")} ÷ ${totalRevenue.toLocaleString("en-US")}`, `**${x.share.toFixed(1)}%**`]),
        },
        after: [
          `${champions.members.length} of ${n} customers (${Math.round((100 * champions.members.length) / n)}%), the Champions, bring in ${champions.share.toFixed(1)}% of revenue. ${atRiskCustomer.name} is At Risk, accounts for ${atRisk.share.toFixed(1)}% of revenue and last bought ${atRiskCustomer.days} days ago, so ${atRiskCustomer.name} is the first customer to contact.`,
        ],
      },
      {
        title: "Use the groups",
        table: {
          head: ["Group", "Suggested action"],
          align: ["left", "left"],
          rows: [
            ["Champions", "Thank and reward them, for example with early access to new beans."],
            ["Loyal Customers", "Keep them buying with a loyalty offer."],
            ["Promising Customers", "Encourage a second and third order."],
            ["At Risk", "Contact them soon with a win-back offer."],
            ["Hibernating", "Send a low-cost reminder email."],
          ],
        },
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Product Recommendation
// ---------------------------------------------------------------------------
const recommendationExample = {
  lead: "A grocery shop has 7 customers and 5 products. A 1 means the customer bought the product.",
  leadTable: {
    head: ["Customer", "Bread", "Butter", "Jam", "Coffee", "Milk"],
    align: ["left", "right", "right", "right", "right", "right"],
    rows: [
      ["Emma", "1", "1", "1", "", ""],
      ["Noah", "1", "1", "1", "", ""],
      ["Olivia", "1", "1", "", "", "1"],
      ["Liam", "1", "", "", "1", "1"],
      ["Ava", "", "", "1", "1", "1"],
      ["Mason", "1", "1", "", "1", ""],
      ["Sophia", "1", "1", "1", "", ""],
    ],
  },
  steps: [
    {
      title: "Count the buyers of each product",
      table: {
        head: ["Product", "Buyers", "Number of buyers"],
        align: ["left", "left", "right"],
        rows: [
          ["Bread", "Emma, Noah, Olivia, Liam, Mason, Sophia", "**6**"],
          ["Butter", "Emma, Noah, Olivia, Mason, Sophia", "**5**"],
          ["Jam", "Emma, Noah, Ava, Sophia", "**4**"],
          ["Coffee", "Liam, Ava, Mason", "**3**"],
          ["Milk", "Olivia, Liam, Ava", "**3**"],
        ],
      },
    },
    {
      title: "Score how similar two products are",
      text: [
        "Two products are similar when the same customers buy both. The score is:",
        "**Similarity = customers who bought both ÷ √(buyers of the first product × buyers of the second product)**",
        "A new customer, Grace, has bought Bread and Jam. The table scores each product she has not bought against Bread and Jam.",
      ],
      table: {
        head: ["Pair", "Customers who bought both", "Calculation", "Similarity"],
        align: ["left", "left", "left", "right"],
        rows: [
          ["Butter and Bread", "Emma, Noah, Olivia, Mason, Sophia (5)", "5 ÷ √(5 × 6) = 5 ÷ 5.48", "**0.91**"],
          ["Butter and Jam", "Emma, Noah, Sophia (3)", "3 ÷ √(5 × 4) = 3 ÷ 4.47", "**0.67**"],
          ["Coffee and Bread", "Liam, Mason (2)", "2 ÷ √(3 × 6) = 2 ÷ 4.24", "**0.47**"],
          ["Coffee and Jam", "Ava (1)", "1 ÷ √(3 × 4) = 1 ÷ 3.46", "**0.29**"],
          ["Milk and Bread", "Olivia, Liam (2)", "2 ÷ √(3 × 6) = 2 ÷ 4.24", "**0.47**"],
          ["Milk and Jam", "Ava (1)", "1 ÷ √(3 × 4) = 1 ÷ 3.46", "**0.29**"],
        ],
      },
    },
    {
      title: "Score each product for the customer",
      text: ["A product's score is the average of its similarity to each product the customer bought. Match is the score multiplied by 100."],
      table: {
        head: ["Product", "Calculation", "Score", "Match"],
        align: ["left", "left", "right", "right"],
        rows: [
          ["Butter", "(0.91 + 0.67) ÷ 2", "0.79", "**79**"],
          ["Coffee", "(0.47 + 0.29) ÷ 2", "0.38", "**38**"],
          ["Milk", "(0.47 + 0.29) ÷ 2", "0.38", "**38**"],
        ],
      },
      after: ["Grace's top suggestion is Butter. Products a customer already bought are left out of the list."],
    },
    {
      title: "Check reliability: hide one purchase",
      text: [
        "The app checks its own suggestions. For each customer with at least 3 different products, it hides one purchase, makes suggestions from the rest and looks for the hidden product in the top 5 suggestions. To keep this example small, it looks at the top 1 suggestion.",
        "**Test 1: Emma, with Jam hidden.** The app knows Emma bought Bread and Butter. Jam now has 3 buyers (Noah, Ava, Sophia).",
      ],
      table: {
        head: ["Product", "Similarity to Bread", "Similarity to Butter", "Score"],
        align: ["left", "left", "left", "right"],
        rows: [
          ["Jam", "2 ÷ √(6 × 3) = 0.47", "2 ÷ √(5 × 3) = 0.52", "**0.49**"],
          ["Coffee", "2 ÷ √(6 × 3) = 0.47", "1 ÷ √(5 × 3) = 0.26", "0.36"],
          ["Milk", "2 ÷ √(6 × 3) = 0.47", "1 ÷ √(5 × 3) = 0.26", "0.36"],
        ],
      },
      after: ["Jam has the highest score. The hidden product was found, so this test is a **hit**."],
    },
    {
      title: "Check reliability: second test",
      text: ["**Test 2: Olivia, with Butter hidden.** The app knows Olivia bought Bread and Milk. Butter now has 4 buyers (Emma, Noah, Mason, Sophia), and none of them bought Milk."],
      table: {
        head: ["Product", "Similarity to Bread", "Similarity to Milk", "Score"],
        align: ["left", "left", "left", "right"],
        rows: [
          ["Coffee", "2 ÷ √(6 × 3) = 0.47", "2 ÷ √(3 × 3) = 0.67", "**0.57**"],
          ["Jam", "3 ÷ √(6 × 4) = 0.61", "1 ÷ √(4 × 3) = 0.29", "0.45"],
          ["Butter", "4 ÷ √(6 × 4) = 0.82", "0 ÷ √(4 × 3) = 0.00", "0.41"],
        ],
      },
      after: ["Coffee has the highest score and the hidden Butter ranks third, so this test is a **miss**."],
    },
    {
      title: "Hit rate",
      text: ["**Hit rate = tests that found the hidden product ÷ tests run**"],
      table: {
        head: ["Tests run", "Hits", "Calculation", "Hit rate"],
        align: ["right", "right", "left", "right"],
        rows: [["2", "1", "1 ÷ 2", "**50%**"]],
      },
      after: [
        "The app runs this test for every eligible customer in the file. It runs the same test for the most popular products, offered to every customer.",
        "For example, with 100 customers tested, if the suggestions find the hidden product for 30 customers (30%) and the most popular products find it for 18 customers (18%), the suggestions find more purchases than best sellers do, and the result reads better than most popular.",
      ],
    },
  ],
};

// ---------------------------------------------------------------------------
// Market Basket Analysis
// ---------------------------------------------------------------------------
const basketExample = {
  lead: "A coffee shop recorded 100 orders. Each order is one basket. The table shows how many baskets contain each product and each pair.",
  leadTable: {
    head: ["Item", "Orders containing it"],
    align: ["left", "right"],
    rows: [
      ["Coffee", "20"],
      ["Blueberry Muffin", "15"],
      ["Bottled Water", "40"],
      ["Coffee and Blueberry Muffin", "10"],
      ["Coffee and Bottled Water", "8"],
    ],
  },
  steps: [
    {
      title: "Support",
      text: ["**Support = orders containing both products ÷ all orders**"],
      table: {
        head: ["Pair", "Calculation", "Support"],
        align: ["left", "left", "right"],
        rows: [
          ["Coffee and Blueberry Muffin", "10 ÷ 100", "**10%**"],
          ["Coffee and Bottled Water", "8 ÷ 100", "**8%**"],
        ],
      },
    },
    {
      title: "Confidence",
      text: ["**Confidence (A then B) = orders containing both products ÷ orders containing A**"],
      table: {
        head: ["Direction", "Calculation", "Confidence"],
        align: ["left", "left", "right"],
        rows: [
          ["Coffee then Blueberry Muffin", "10 ÷ 20", "**50%**"],
          ["Blueberry Muffin then Coffee", "10 ÷ 15", "**66.7%**"],
          ["Coffee then Bottled Water", "8 ÷ 20", "**40%**"],
          ["Bottled Water then Coffee", "8 ÷ 40", "**20%**"],
        ],
      },
    },
    {
      title: "Lift",
      text: [
        "Chance alone would put two products in the same order at a rate equal to the share of orders with A multiplied by the share of orders with B. Lift compares what happens with that expected rate.",
        "**Lift = support ÷ (share of orders with A × share of orders with B)**",
      ],
      table: {
        head: ["Pair", "Expected by chance", "Support", "Lift"],
        align: ["left", "left", "right", "right"],
        rows: [
          ["Coffee and Blueberry Muffin", "20% × 15% = 3%", "10%", "10 ÷ 3 = **3.33**"],
          ["Coffee and Bottled Water", "20% × 40% = 8%", "8%", "8 ÷ 8 = **1.00**"],
        ],
      },
    },
    {
      title: "Read the result",
      table: {
        head: ["Pair", "Lift", "Meaning"],
        align: ["left", "right", "left"],
        rows: [
          ["Coffee and Blueberry Muffin", "3.33", "Bought together 3.3 times more often than chance. A bundle or a \"frequently bought together\" prompt suits this pair."],
          ["Coffee and Bottled Water", "1.00", "Bought together as often as chance gives. Both products are popular on their own."],
        ],
      },
      after: ["The results list pairs with a lift of at least 1.1, so Coffee and Blueberry Muffin appears and Coffee and Bottled Water does not."],
    },
  ],
};

// ---------------------------------------------------------------------------
// Forecasting
// ---------------------------------------------------------------------------
const forecastExample = {
  lead: "A store wants to forecast monthly sales. All sales figures are in $ thousands.",
  steps: [
    {
      title: "Total the sales by month",
      text: ["The rows of the file are added up by month. For example, three January rows of 50, 30 and 20 give January sales of **100**."],
    },
    {
      title: "Smooth the history (exponential smoothing)",
      text: [
        "Exponential smoothing keeps a running estimate of normal monthly sales, called the level. Each month, the level moves toward the latest actual sales:",
        "**New level = weight × actual sales + (1 - weight) × previous level**",
        "The weight is a number between 0 and 1. A higher weight makes recent months count more. The app chooses the weight that fits your history best. This example uses a weight of 0.5, and the first level is January's sales.",
      ],
      table: {
        head: ["Month", "Actual sales", "Calculation", "New level"],
        align: ["left", "right", "left", "right"],
        rows: [
          ["January", "100", "First month, so the level is the actual sales", "**100**"],
          ["February", "108", "0.5 × 108 + 0.5 × 100", "**104**"],
          ["March", "104", "0.5 × 104 + 0.5 × 104", "**104**"],
          ["April", "112", "0.5 × 112 + 0.5 × 104", "**108**"],
          ["May", "116", "0.5 × 116 + 0.5 × 108", "**112**"],
          ["June", "120", "0.5 × 120 + 0.5 × 112", "**116**"],
        ],
      },
      after: ["The latest level is the forecast. Every coming month is forecast at **116**."],
    },
    {
      title: "Add a trend when sales are rising or falling",
      text: [
        "The app also tries a version that tracks the trend, the average monthly change in sales. It keeps the trend up to date in the same way as the level, and fades it gradually so that it does not run on forever. The fade is a damping factor between 0 and 1.",
        "**Forecast for month h = level + trend × (damping + damping² + ... + damping^h)**",
        "For example, with a level of 116, a trend of 4 per month and a damping factor of 0.8:",
      ],
      table: {
        head: ["Month ahead", "Calculation", "Forecast"],
        align: ["right", "left", "right"],
        rows: [
          ["1", "116 + 4 × 0.8", "**119.2**"],
          ["2", "116 + 4 × (0.8 + 0.64)", "**121.8**"],
          ["3", "116 + 4 × (0.8 + 0.64 + 0.512)", "**123.8**"],
        ],
      },
      after: ["The app fits the version with a trend and the version without one, and keeps the one that fits your history better."],
    },
    {
      title: "Adjust for the yearly pattern",
      text: [
        "Many businesses have a yearly pattern, such as a busy December. The app separates this pattern from the underlying trend using STL (Seasonal and Trend decomposition using Loess). It then forecasts the underlying trend and applies the pattern back to each month.",
        "Each month gets a seasonal factor. A factor of 1.30 means that month is usually 30% above the underlying trend. For example, if the forecast before the yearly pattern is 120 for each month:",
      ],
      table: {
        head: ["Month", "Forecast before the yearly pattern", "Seasonal factor", "Forecast"],
        align: ["left", "right", "right", "right"],
        rows: [
          ["November", "120", "0.90", "120 × 0.90 = **108**"],
          ["December", "120", "1.30", "120 × 1.30 = **156**"],
          ["January", "120", "0.80", "120 × 0.80 = **96**"],
        ],
      },
      after: ["Learning a yearly pattern needs at least two years of history."],
    },
    {
      title: "Show a likely range",
      text: ["Each forecast month comes with a low and a high estimate that form a 95% likely range. For example, a forecast of 116 might come with a low estimate of 104 and a high estimate of 128."],
    },
    {
      title: "Test the forecast on past months",
      text: [
        "To measure accuracy, the app hides the latest months, forecasts them from the earlier history and compares each forecast with the actual sales. This example tests three months.",
      ],
      table: {
        head: ["Month", "Forecast", "Actual", "Error (forecast - actual)", "Absolute error", "Percentage error"],
        align: ["left", "right", "right", "right", "right", "left"],
        rows: [
          ["January", "110", "100", "+10", "10", "10 ÷ 100 = 10.0%"],
          ["February", "120", "130", "-10", "10", "10 ÷ 130 = 7.7%"],
          ["March", "130", "170", "-40", "40", "40 ÷ 170 = 23.5%"],
          ["**Total**", "", "**400**", "**-40**", "**60**", ""],
        ],
      },
    },
    {
      title: "Calculate the error measures",
      table: {
        head: ["Measure", "Calculation", "Result"],
        align: ["left", "left", "right"],
        rows: [
          ["Weighted absolute percentage error", "Total absolute error ÷ total actual sales = 60 ÷ 400", "**15.0%**"],
          ["Forecast accuracy", "100% - 15.0%", "**85.0%**"],
          ["Mean absolute percentage error", "(10.0% + 7.7% + 23.5%) ÷ 3", "**13.7%**"],
          ["Mean absolute error", "(10 + 10 + 40) ÷ 3", "**20**"],
          ["Root mean squared error", "Squared errors: 100, 100, 1,600. Average: 1,800 ÷ 3 = 600. Square root of 600", "**24.5**"],
          ["Bias", "Total error ÷ total actual sales = -40 ÷ 400", "**-10.0%**"],
        ],
      },
      after: ["Bias is negative, so the forecast ran low. A positive bias means the forecast ran high."],
    },
    {
      title: "Compare with the benchmark",
      text: ["The benchmark forecast repeats the sales of the same month last year."],
      table: {
        head: ["Month", "Same month last year", "Actual", "Absolute error"],
        align: ["left", "right", "right", "right"],
        rows: [
          ["January", "80", "100", "20"],
          ["February", "160", "130", "30"],
          ["March", "120", "170", "50"],
          ["**Total**", "", "**400**", "**100**"],
        ],
      },
      after: ["Benchmark error = 100 ÷ 400 = **25.0%**. The forecast error of 15.0% is lower, so the forecast beats repeating last year."],
    },
    {
      title: "Choose the method",
      text: [
        "The test is repeated from up to 12 starting points in the history, and the results are combined. It is run for exponential smoothing and for exponential smoothing with the yearly adjustment. The method with the lower error is used for your forecast.",
      ],
    },
  ],
};

export const EXAMPLES = {
  clv: buildClvExample(),
  recommendation: recommendationExample,
  basket: basketExample,
  forecast: forecastExample,
};
