import { describe, expect, it } from "vitest";
import {
  brlToCents,
  centsToBRL,
  centsToInputValue,
  formatCurrencyBRL,
} from "@/lib/currency";

// Intl.NumberFormat("pt-BR", { style: "currency" }) puts a NON-BREAKING space
// (U+00A0) between "R$" and the amount — a plain " " in these literals would
// silently never match.
const NBSP = " ";

describe("formatCurrencyBRL", () => {
  it("formats a positive value as BRL currency", () => {
    expect(formatCurrencyBRL(1234.5)).toBe(`R$${NBSP}1.234,50`);
  });

  it("formats zero", () => {
    expect(formatCurrencyBRL(0)).toBe(`R$${NBSP}0,00`);
  });
});

describe("centsToBRL", () => {
  it("formats cents as BRL currency", () => {
    expect(centsToBRL(123450n)).toBe(`R$${NBSP}1.234,50`);
  });

  it("formats zero cents", () => {
    expect(centsToBRL(0n)).toBe(`R$${NBSP}0,00`);
  });

  it("formats negative cents", () => {
    expect(centsToBRL(-1999n)).toBe(`-R$${NBSP}19,99`);
  });
});

describe("centsToInputValue", () => {
  it("formats cents as a plain decimal string", () => {
    expect(centsToInputValue(123450n)).toBe("1234.50");
  });

  it("formats negative cents", () => {
    expect(centsToInputValue(-1999n)).toBe("-19.99");
  });

  it("round-trips through brlToCents", () => {
    expect(brlToCents(centsToInputValue(105030n))).toBe(105030n);
  });
});

describe("brlToCents", () => {
  it("parses a whole number", () => {
    expect(brlToCents("1234")).toBe(1234_00n);
  });

  it("parses one decimal digit", () => {
    expect(brlToCents("1234.5")).toBe(1234_50n);
  });

  it("parses two decimal digits with a dot", () => {
    expect(brlToCents("1234.50")).toBe(1234_50n);
  });

  it("parses two decimal digits with a comma", () => {
    expect(brlToCents("1234,50")).toBe(1234_50n);
  });

  it("parses the classic float-rounding trap exactly", () => {
    expect(brlToCents("19.99")).toBe(1999n);
  });

  it("parses negative values", () => {
    expect(brlToCents("-19.99")).toBe(-1999n);
  });

  it("throws on malformed input", () => {
    expect(() => brlToCents("abc")).toThrow();
    expect(() => brlToCents("12.345")).toThrow();
    expect(() => brlToCents("")).toThrow();
  });

  it("round-trips through centsToBRL", () => {
    expect(centsToBRL(brlToCents("19.99"))).toBe(`R$${NBSP}19,99`);
  });
});
