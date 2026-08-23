import { describe, expect, it } from "vitest";
import { toDateInputValue } from "@/lib/renda-fixa/dates";

describe("toDateInputValue", () => {
  it("formats a date as YYYY-MM-DD", () => {
    expect(toDateInputValue(new Date("2026-01-15T00:00:00.000Z"))).toBe(
      "2026-01-15",
    );
  });

  it("returns an empty string for null", () => {
    expect(toDateInputValue(null)).toBe("");
  });

  it("returns an empty string for undefined", () => {
    expect(toDateInputValue(undefined)).toBe("");
  });
});
