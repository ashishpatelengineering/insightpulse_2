import test from "node:test";
import assert from "node:assert/strict";
import { suggestColumns } from "./autoMap.js";

const ALL_ROLES = [
  "customer", "invoice", "date", "productId", "productName", "category", "subCategory",
  "quantity", "unitPrice", "sales", "extraFilter",
];

// Column names, kinds and the role each is expected to match. Mirrors the three sample files.
const FILES = {
  "office retail": [
    ["CustomerID", "text", "customer"], ["InvoiceNo", "text", "invoice"], ["InvoiceDate", "date", "date"],
    ["ProductID", "text", "productId"], ["ProductName", "text", "productName"], ["Category", "text", "category"],
    ["SubCategory", "text", "subCategory"], ["Quantity", "number", "quantity"], ["UnitPrice", "number", "unitPrice"],
    ["Sales", "number", "sales"], ["Region", "text", "extraFilter"],
  ],
  grocery: [
    ["member_number", "number", "customer"], ["bill_id", "number", "invoice"], ["purchase_date", "date", "date"],
    ["sku", "text", "productId"], ["item_name", "text", "productName"], ["department", "text", "category"],
    ["aisle", "text", "subCategory"], ["qty", "number", "quantity"], ["price", "number", "unitPrice"],
    ["amount", "number", "sales"], ["store", "text", "extraFilter"],
  ],
  electronics: [
    ["Customer Id", "text", "customer"], ["Order Number", "text", "invoice"], ["Order Date", "date", "date"],
    ["Item Code", "text", "productId"], ["Item Description", "text", "productName"], ["Segment", "text", "category"],
    ["Sub Segment", "text", "subCategory"], ["Units", "number", "quantity"], ["Price Per Unit", "number", "unitPrice"],
    ["Revenue", "number", "sales"], ["Channel", "text", "extraFilter"],
  ],
  fashion: [
    ["user_id", "text", "customer"], ["order_ref", "text", "invoice"], ["order_date", "date", "date"],
    ["style_code", "text", "productId"], ["product_title", "text", "productName"], ["product_type", "text", "category"],
    ["collection", "text", "subCategory"], ["units", "number", "quantity"], ["list_price", "number", "unitPrice"],
    ["line_total", "number", "sales"], ["country", "text", "extraFilter"],
  ],
  wholesale: [
    ["Account", "text", "customer"], ["Sales Order", "text", "invoice"], ["Ship Date", "date", "date"],
    ["Item No", "text", "productId"], ["Description", "text", "productName"], ["Product Group", "text", "category"],
    ["Product Line", "text", "subCategory"], ["Qty", "number", "quantity"], ["Net Price", "number", "unitPrice"],
    ["Net Amount", "number", "sales"], ["Region", "text", "extraFilter"],
  ],
};

for (const [label, spec] of Object.entries(FILES)) {
  test(`auto match: ${label}`, () => {
    const columns = spec.map(([name, kind]) => ({ name, kind }));
    const result = suggestColumns(columns, ALL_ROLES);
    for (const [name, , role] of spec) {
      assert.equal(result[role], name, `${role} should match ${name}, got ${result[role]}`);
    }
  });

  test(`auto match is stable when columns are shuffled: ${label}`, () => {
    const columns = spec.map(([name, kind]) => ({ name, kind })).reverse();
    const result = suggestColumns(columns, ALL_ROLES);
    for (const [name, , role] of spec) assert.equal(result[role], name);
  });
}

test("unknown names get no suggestion rather than a wrong one", () => {
  const columns = [{ name: "Foo", kind: "text" }, { name: "Bar", kind: "number" }];
  assert.deepEqual(suggestColumns(columns, ALL_ROLES), {});
});

// Other naming habits seen in real files.
const OTHER = {
  "buyer file": [
    ["Buyer", "text", "customer"], ["Txn Date", "date", "date"], ["Item", "text", "productName"], ["Amt", "number", "sales"],
  ],
  "till export": [
    ["Receipt", "text", "invoice"], ["Date", "date", "date"], ["SKU", "text", "productId"], ["Qty", "number", "quantity"], ["Price", "number", "unitPrice"],
  ],
  "web shop": [
    ["Shopper ID", "text", "customer"], ["Basket ID", "text", "invoice"], ["Barcode", "text", "productId"], ["Article Name", "text", "productName"],
    ["Net Amount", "number", "sales"], ["Product Type", "text", "category"],
  ],
};
for (const [label, spec] of Object.entries(OTHER)) {
  test(`auto match: ${label}`, () => {
    const result = suggestColumns(spec.map(([name, kind]) => ({ name, kind })), ALL_ROLES);
    for (const [name, , role] of spec) assert.equal(result[role], name, `${role} should match ${name}, got ${result[role]}`);
  });
}
