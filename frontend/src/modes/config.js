/**
 * Every analysis mode is described here: its page, the information shown in the (i) popover,
 * and the inputs the user must fill in. The sidebar, popovers and Inputs form are built from this.
 */

export const ALL_VALUE = "__ALL__";
export const NONE_VALUE = "__NONE__";

export const MODES = [
  {
    id: "clv",
    api: "clv",
    path: "/clv",
    title: "Customer Lifetime Value",
    shortTitle: "Customer Lifetime Value",
    icon: "clv",
    info: {
      bullets: [
        "Shows what each customer has spent and which customers matter most.",
        "Customers are placed in five groups, from Champions to Hibernating.",
      ],
    },
    fields: [
      { key: "customer_id", role: "customer", label: "Customer Column", hint: "Identifies each customer", required: true },
      { key: "invoice_date", role: "date", label: "Date Column", hint: "Date of each sale", required: true },
      { key: "sales", role: "sales", label: "Sales Column", hint: "Sales value of each row", required: true },
      { key: "invoice_id", role: "invoice", label: "Order Column (Optional)", hint: "Identifies each order", required: false, allowNone: true },
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
        "Suggests the products to offer each customer next.",
        "Suggestions come from what similar customers bought. A reliability check is shown with the results.",
      ],
    },
    fields: [
      { key: "customer_id", role: "customer", label: "Customer Column", hint: "Identifies each customer", required: true },
      { key: "product_name", role: "productName", fallbackRole: "productId", label: "Product Column", hint: "Identifies each product", required: true },
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
        "Shows which products appear in the same order.",
        "Use it for bundles, promotions and \"frequently bought together\" prompts.",
      ],
    },
    fields: [
      { key: "product_name", role: "productName", fallbackRole: "productId", label: "Product Column", hint: "Identifies each product", required: true },
      { key: "transaction_id", role: "invoice", label: "Order Column", hint: "Identifies each order", required: true },
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
        "Predicts sales for the coming months from your sales history.",
        "Forecast one group, such as a category or region, or all sales.",
      ],
    },
    fields: [
      { key: "sales", role: "sales", label: "Sales Column", hint: "Sales value of each row", required: true },
      { key: "date", role: "date", label: "Date Column", hint: "Date of each sale", required: true },
      { key: "filter_column", role: "category", label: "Group Column (Optional)", hint: "Forecast one group only", required: false, allowNone: true },
      { key: "filter_value", type: "value", column: "filter_column", label: "Group", hint: "One group, or All", required: false },
      { key: "periods", type: "number", label: "Months to Forecast", hint: "1 to 36", required: true, min: 1, max: 36, placeholder: "For example 6" },
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
      values[field.key] = suggestions[field.role] || suggestions[field.fallbackRole] || NONE_VALUE;
    } else {
      values[field.key] = suggestions[field.role] || suggestions[field.fallbackRole] || "";
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
