import test from "node:test";
import assert from "node:assert/strict";
import { toCsv } from "./csv.js";

const columns = [{ label: "Value", value: (r) => r.v }];
const cell = (v) => toCsv([{ v }], columns).split("\r\n")[1];

test("text that a spreadsheet would run as a formula is neutralized", () => {
  assert.equal(cell("=SUM(A1)"), "'=SUM(A1)");
  assert.equal(cell("@cmd"), "'@cmd");
});

test("numbers, negative numbers and normal text are left alone", () => {
  assert.equal(cell(-12.5), "-12.5");
  assert.equal(cell("-3"), "-3");
  assert.equal(cell("Chair"), "Chair");
});

test("cells with commas are quoted", () => {
  assert.equal(cell("a,b"), '"a,b"');
});
