import { describe, expect, it } from "vitest";
import { FixedIncomeType } from "@prisma/client";
import {
  FIXED_INCOME_TYPE_LABELS,
  FIXED_INCOME_TYPE_OPTIONS,
} from "@/lib/renda-fixa/labels";

describe("FIXED_INCOME_TYPE_LABELS", () => {
  it("has a label for every FixedIncomeType", () => {
    for (const type of Object.values(FixedIncomeType)) {
      expect(FIXED_INCOME_TYPE_LABELS[type]).toBeTruthy();
    }
  });
});

describe("FIXED_INCOME_TYPE_OPTIONS", () => {
  it("has one option per FixedIncomeType, with matching labels", () => {
    const values = Object.values(FixedIncomeType);
    expect(FIXED_INCOME_TYPE_OPTIONS).toHaveLength(values.length);
    for (const option of FIXED_INCOME_TYPE_OPTIONS) {
      expect(option.label).toBe(FIXED_INCOME_TYPE_LABELS[option.value]);
    }
  });
});
