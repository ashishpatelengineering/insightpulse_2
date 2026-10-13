/**
 * Every analysis mode is described here: its page, the information shown in the (i) popover,
 * and the inputs the user must fill in. The sidebar, popovers and Inputs form are built from this.
 */

export const ALL_VALUE = "__ALL__";
export const NONE_VALUE = "__NONE__";

const COMMON_STEPS_START = [
  "Upload a CSV file, or choose one of the sample datasets.",
  "Match each input below to the correct column in your data. We suggest matches for you, so please check them.",
];

export const MODES = [
  {
    id: "clv",
    api: "clv",
    path: "/clv",
    title: "Customer Lifetime Value",
    shortTitle: "CLV",
    icon: "clv",
    info: {
      bullets: [
        "Customer Lifetime Value mode shows which customers are worth the most to your business.",
        "Customers are placed into three groups (Low, Medium and High Value) based on their total purchase amount.",
        "Use the results to decide who to reward, who to win back and where to focus your marketing budget.",
      ],
      stepsTitle: "Follow these steps to segment your customers:",
      steps: [
        ...COMMON_STEPS_START,
        "All inputs are required.",
        "Your data must include these columns: Customer ID, Invoice ID, Invoice Date, Quantity and Unit Price.",
        "Click Analyze.",
      ],
    },
    fields: [
      { key: "customer_id", role: "customer", label: "Customer ID Column", hint: "Unique code or number for each customer", required: true },
      { key: "invoice_id", role: "invoice", label: "Invoice ID Column", hint: "Identifies each purchase or receipt", required: true },
      { key: "invoice_date", role: "date", label: "Invoice Date Column", hint: "The date of each purchase", required: true },
      { key: "quantity", role: "quantity", label: "Quantity Column", hint: "Number of units bought on each line", required: true },
      { key: "unit_price", role: "unitPrice", label: "Unit Price Column", hint: "Price of one unit", required: true },
    ],
  },
  {
    id: "recommendation",
    api: "recommendation",
    path: "/product-recommendation",
    title: "Product Recommendation",
    shortTitle: "Product Recommendation",
    icon: "recommendation",
    info: {
      bullets: [
        "Product Recommendation mode suggests which products to offer each customer next.",
        "Suggestions are based on what similar customers have bought, so they work well for cross selling, personalized offers and email campaigns.",
      ],
      stepsTitle: "Follow these steps to get recommendations:",
      steps: [
        ...COMMON_STEPS_START,
        "All inputs are required.",
        "Your data must include these columns: Customer ID, Product ID, Product Name, Category, Sub Category, Sales and Quantity.",
        "Click Analyze, then choose a customer to see their top 5 suggested products.",
      ],
    },
    fields: [
      { key: "product_id", role: "productId", label: "Product ID Column", hint: "Unique code for each product", required: true },
      { key: "product_name", role: "productName", label: "Product Name Column", hint: "The name customers see", required: true },
      { key: "sales", role: "sales", label: "Sales Column", hint: "Sales value of each line (amount paid)", required: true },
      { key: "category", role: "category", label: "Category Column", hint: "Main product group", required: true },
      { key: "sub_category", role: "subCategory", label: "Sub Category Column", hint: "More detailed product group", required: true },
      { key: "quantity", role: "quantity", label: "Quantity Column", hint: "Number of units bought", required: true },
      { key: "customer_id", role: "customer", label: "Customer ID Column", hint: "Unique code for each customer", required: true },
    ],
  },
  {
    id: "basket",
    api: "basket",
    path: "/market-basket-analysis",
    title: "Market Basket Analysis",
    shortTitle: "Market Basket Analysis",
    icon: "basket",
    info: {
      bullets: [
        "Market Basket Analysis mode shows which products customers tend to buy together.",
        "Use it to plan bundles, promotions, shelf or website layouts and \"frequently bought together\" suggestions.",
        "All products one member buys on the same date count as one basket.",
      ],
      stepsTitle: "Follow these steps to find product combinations:",
      steps: [
        ...COMMON_STEPS_START,
        "All inputs are required.",
        "Your data must include these columns: Member Number (customer), Date and Product Name.",
        "Click Analyze.",
      ],
      afterTitle: "How to read the results:",
      after: [
        "Together: the number of baskets that contain the products together.",
        "Confidence: how often the second product is bought when the first one is.",
        "Lift: how much more likely the products are bought together than by chance. Above 1 means a real link, and higher means a stronger link.",
      ],
    },
    fields: [
      { key: "member_number", role: "customer", label: "Member Number Column", hint: "Unique code for each member or customer", required: true },
      { key: "date", role: "date", label: "Date Column", hint: "The date of each purchase", required: true },
      { key: "product_name", role: "productName", label: "Product Name Column", hint: "The product that was bought", required: true },
    ],
  },
  {
    id: "forecast",
    api: "forecast",
    path: "/forecasting",
    title: "Forecasting",
    shortTitle: "Forecasting",
    icon: "forecast",
    info: {
      bullets: [
        "Forecasting mode predicts your future sales from your sales history.",
        "It learns your growth trend and, when you have 30 months or more of history, your yearly seasonal pattern such as holiday peaks.",
        "Forecasts are monthly and include a likely range, so you can plan for both stronger and weaker months.",
      ],
      stepsTitle: "Follow these steps to create a forecast:",
      steps: [
        ...COMMON_STEPS_START,
        "All inputs are required except the Additional Filter.",
        "Your data must include these columns: Sales (amount or value), Date and a Filter Column such as Product, Category or Region.",
        "Choose a value to forecast one product, category or region, or choose All to forecast total sales. Use the optional Additional Filter to narrow it further.",
        "Click Analyze.",
      ],
    },
    fields: [
      { key: "sales", role: "sales", label: "Sales Column", hint: "Sales amount or value of each line", required: true },
      { key: "date", role: "date", label: "Date Column", hint: "The date of each sale", required: true },
      { key: "filter_column", role: "category", label: "Filter Column", hint: "What to forecast, for example Category, Product or Region", required: true },
      { key: "filter_value", type: "value", column: "filter_column", label: "Filter Value", hint: "Choose one value, or All for total sales", required: true },
      { key: "periods", type: "number", label: "Forecasting Period (Months)", hint: "How many months ahead to forecast (1 to 36)", required: true, min: 1, max: 36, placeholder: "For example 6" },
      { key: "additional_column", role: "extraFilter", label: "Additional Filter Column (Optional)", hint: "Narrow the forecast further, for example by Region", required: false, allowNone: true },
      { key: "additional_value", type: "value", column: "additional_column", label: "Additional Filter Value", hint: "Choose one value, or All", required: false },
    ],
  },
];

export const MODE_BY_ID = Object.fromEntries(MODES.map((m) => [m.id, m]));

export function modeByPath(pathname) {
  return MODES.find((m) => m.path === pathname) || null;
}

/** Initial selections for a mode, using suggestions for the columns. */
export function initialSelections(mode, suggestions) {
  const values = {};
  mode.fields.forEach((field) => {
    if (field.type === "value") {
      values[field.key] = ALL_VALUE;
    } else if (field.type === "number") {
      values[field.key] = "6";
    } else if (field.allowNone) {
      values[field.key] = suggestions[field.role] || NONE_VALUE;
    } else {
      values[field.key] = suggestions[field.role] || "";
    }
  });
  return values;
}

/** Is every required input filled in correctly? Returns a list of problems (empty when ready). */
export function validateSelections(mode, selections, columns) {
  const problems = [];
  const names = new Set(columns.map((c) => c.name));
  mode.fields.forEach((field) => {
    const value = selections[field.key];
    if (field.type === "number") {
      const n = Number(value);
      if (value === "" || value === undefined || !Number.isInteger(n) || n < field.min || n > field.max) {
        problems.push(`${field.label}: enter a whole number between ${field.min} and ${field.max}.`);
      }
    } else if (field.type === "value") {
      const columnValue = selections[field.column];
      const columnChosen = columnValue && columnValue !== NONE_VALUE;
      if (columnChosen && (value === undefined || value === "")) problems.push(`${field.label}: please choose a value.`);
    } else if (field.required) {
      if (!value || value === NONE_VALUE) problems.push(`${field.label}: please select a column.`);
      else if (!names.has(value)) problems.push(`${field.label}: the selected column is not in this file.`);
    }
  });
  return problems;
}

/** Build the request body for the API. */
export function buildParams(mode, selections) {
  const params = {};
  mode.fields.forEach((field) => {
    const value = selections[field.key];
    if (field.type === "value") {
      const columnValue = selections[field.column];
      if (columnValue && columnValue !== NONE_VALUE) params[field.key] = value;
    } else if (field.allowNone) {
      if (value && value !== NONE_VALUE) params[field.key] = value;
    } else {
      params[field.key] = value;
    }
  });
  return params;
}
