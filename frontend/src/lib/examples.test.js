import test from "node:test";
import assert from "node:assert/strict";
import { clvScores, EXAMPLES } from "../content/examples.js";

// Expected values come from running the same ten customers through the backend analysis.
const EXPECTED = {
  Emily: ["5-5-5", "Champions"],
  James: ["5-4-5", "Champions"],
  Jessica: ["4-1-1", "Promising Customers"],
  Michael: ["4-3-4", "Loyal Customers"],
  Jennifer: ["3-4-3", "Loyal Customers"],
  Robert: ["3-3-3", "Loyal Customers"],
  Daniel: ["2-2-2", "Hibernating"],
  David: ["2-5-4", "At Risk"],
  Ashley: ["1-2-2", "Hibernating"],
  Brian: ["1-1-1", "Hibernating"],
};

test("customer lifetime value example matches the backend analysis", () => {
  for (const c of clvScores()) {
    assert.deepEqual([`${c.r}-${c.f}-${c.m}`, c.segment], EXPECTED[c.name], c.name);
  }
});

test("every example has steps and tables with matching column counts", () => {
  for (const [id, example] of Object.entries(EXAMPLES)) {
    assert.ok(example.steps.length > 0, id);
    const tables = [example.leadTable, ...example.steps.flatMap((s) => [s.table, s.table2])].filter(Boolean);
    for (const t of tables) for (const row of t.rows) assert.equal(row.length, t.head.length, `${id}: ${row[0]}`);
  }
});

test("examples contain no long dashes", () => {
  assert.ok(!/[\u2013\u2014]/.test(JSON.stringify(EXAMPLES)));
});
