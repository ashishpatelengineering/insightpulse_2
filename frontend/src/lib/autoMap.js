/**
 * Suggest which column in the user's file matches each input, based on common column names.
 * The user can always change the suggestion. Matching is forgiving about spaces, case and symbols.
 */

const norm = (text) => String(text).toLowerCase().replace(/[^a-z0-9]/g, "");

export const ROLES = {
  customer: {
    words: ["customerid", "customerno", "customernumber", "customer", "custid", "memberid", "membernumber", "membernum", "member", "clientid", "client", "userid", "buyerid"],
    exclude: /date|time|name$/,
  },
  invoice: {
    words: ["invoiceid", "invoiceno", "invoicenumber", "invoice", "billid", "billno", "billnumber", "bill", "orderid", "orderno", "ordernumber", "order", "transactionid", "transaction", "receiptno", "receipt"],
    exclude: /date|time|customer|member/,
  },
  date: {
    words: ["invoicedate", "orderdate", "purchasedate", "transactiondate", "saledate", "billdate", "date", "datetime", "timestamp"],
    exclude: /^$/,
    kind: "date",
  },
  productId: {
    words: ["productid", "productcode", "sku", "itemcode", "itemid", "stockcode", "partno", "partnumber"],
    exclude: /name|desc|category|cat$/,
  },
  productName: {
    words: ["productname", "itemname", "itemdescription", "productdescription", "description", "product", "item", "title"],
    exclude: /id$|code|category|sub/,
  },
  category: {
    words: ["category", "productcategory", "department", "segment", "dept", "productgroup", "group"],
    exclude: /sub/,
  },
  subCategory: {
    words: ["subcategory", "subsegment", "subdepartment", "aisle", "subgroup", "productclass", "class"],
    exclude: /^$/,
  },
  quantity: {
    words: ["quantity", "qty", "units", "unitssold", "pieces", "count"],
    exclude: /price|amount|revenue|sales/,
    kind: "number",
  },
  unitPrice: {
    words: ["unitprice", "priceperunit", "itemprice", "unitcost", "price", "rate"],
    exclude: /total/,
    kind: "number",
  },
  sales: {
    words: ["sales", "salesamount", "netsales", "revenue", "amount", "totalprice", "linetotal", "total", "value"],
    exclude: /unit|per|qty|quantity/,
    kind: "number",
  },
  extraFilter: {
    words: ["region", "store", "channel", "location", "branch", "city", "state", "country", "market"],
    exclude: /^$/,
  },
};

function scoreColumn(column, role) {
  const name = norm(column.name);
  if (!name || role.exclude.test(name)) return 0;
  let score = 0;
  role.words.forEach((word, index) => {
    const rank = role.words.length - index;
    if (name === word) score = Math.max(score, 1000 + rank);
    else if (name.startsWith(word) || name.endsWith(word)) score = Math.max(score, 500 + rank);
    else if (word.length >= 4 && name.includes(word)) score = Math.max(score, 200 + rank);
  });
  if (score === 0) return 0;
  if (role.kind && column.kind !== role.kind) {
    // A date or number role must not land on a column of another type.
    return role.kind === "date" ? 0 : Math.floor(score / 20);
  }
  return score;
}

/** Returns { roleName: columnName } with each column used at most once. */
export function suggestColumns(columns, roleNames) {
  const candidates = [];
  roleNames.forEach((roleName) => {
    columns.forEach((column) => {
      const score = scoreColumn(column, ROLES[roleName]);
      if (score > 0) candidates.push({ roleName, column: column.name, score });
    });
  });
  candidates.sort((a, b) => b.score - a.score);
  const result = {};
  const used = new Set();
  candidates.forEach((candidate) => {
    if (result[candidate.roleName] || used.has(candidate.column)) return;
    result[candidate.roleName] = candidate.column;
    used.add(candidate.column);
  });
  return result;
}
